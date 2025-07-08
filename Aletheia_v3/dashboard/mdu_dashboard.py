import streamlit as st
import requests
import os # Añadido import os
from typing import List, Dict, Any, Optional

# Para visualización de grafos
try:
    from st_agraph import agraph, Node, Edge, Config
    AGRAPH_AVAILABLE = True
except ImportError:
    AGRAPH_AVAILABLE = False
    # Se mostrará advertencia en la app si no está disponible

# Configuración básica de la página
st.set_page_config(layout="wide", page_title="Aletheia Knowledge Dashboard")

# URL base de la API (debería ser configurable)
API_BASE_URL = os.getenv("ALETHEIA_API_URL", "http://localhost:8000/api/v1")

# --- Funciones de Helper para llamar a la API ---
def get_api_data(endpoint: str, params: Optional[Dict] = None) -> Optional[Any]:
    """Obtiene datos de un endpoint de la API."""
    try:
        full_url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(full_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al conectar con la API en {full_url}: {e}")
        return None
    except ValueError as e:
        st.error(f"Error al parsear JSON de {full_url}: {e}")
        return None

# --- Mapeo de Tipos de Concepto a Colores ---
CONCEPT_TYPE_COLORS = {
    "DOCUMENT_SOURCE": "#FFD700", # Gold
    "UCM": "#ADD8E6", # LightBlue
    "CLUSTER": "#90EE90", # LightGreen
    "PROPOSITION": "#FFA07A", # LightSalmon
    "MINI_THEORY": "#DA70D6", # Orchid
    "COMPREHENSIVE_THEORY": "#87CEFA", # LightSkyBlue
    "UNIFIED_MODEL": "#6A5ACD", # SlateBlue
    "GENERIC_CONCEPT": "#E0E0E0", # LightGray
    "DEFAULT": "#FFFFFF" # Blanco para tipos no mapeados
}

# --- Sección 1: Visualización del Grafo Completo (Implementación) ---
def display_full_knowledge_graph():
    st.subheader("Explorador del Grafo de Conocimiento Completo")

    if not AGRAPH_AVAILABLE:
        st.warning("streamlit-agraph no está instalado. La visualización de grafos no está disponible. Por favor, instálala: pip install streamlit-agraph")
        return

    # Carga de datos
    concepts_data = get_api_data("/eje-x/concepts/")
    relationships_data = get_api_data("/eje-x/relationships/")

    if concepts_data is None or relationships_data is None:
        # El error ya se muestra en get_api_data
        return

    if not concepts_data:
        st.info("No hay conceptos en la base de datos para mostrar.")
        return

    # --- Sidebar para filtros y detalles ---
    st.sidebar.title("Opciones del Grafo")

    unique_concept_types = sorted(list(set(c['concept_type'] for c in concepts_data if 'concept_type' in c)))
    if not unique_concept_types:
        unique_concept_types = ["N/A"]

    selected_types = st.sidebar.multiselect(
        "Filtrar por Tipo de Concepto:",
        options=unique_concept_types,
        default=unique_concept_types
    )

    # Preparar nodos y mapeo para detalles
    nodes = []
    node_ids_in_graph = set()
    concept_map = {c['id']: c for c in concepts_data}

    for concept in concepts_data:
        if concept['concept_type'] in selected_types:
            node_color = CONCEPT_TYPE_COLORS.get(concept['concept_type'], CONCEPT_TYPE_COLORS["DEFAULT"])
            node_label = concept['name'][:30] + "..." if len(concept['name']) > 30 else concept['name']

            nodes.append(Node(id=concept['id'],
                              label=node_label,
                              title=f"Nombre: {concept['name']}\nTipo: {concept['concept_type']}\nID: {concept['id']}",
                              shape="ellipse",
                              color=node_color,
                              font={"size": 12} # Tamaño de fuente reducido para mejor visualización
                              ))
            node_ids_in_graph.add(concept['id'])

    edges = []
    if relationships_data:
        for rel in relationships_data:
            if rel['source_concept_id'] in node_ids_in_graph and rel['target_concept_id'] in node_ids_in_graph:
                edge_label = rel['type'][:20] if rel.get('type') else "" # Asegurar que 'type' exista

                source_name = concept_map.get(rel['source_concept_id'],{}).get('name','ID: '+rel['source_concept_id'])
                target_name = concept_map.get(rel['target_concept_id'],{}).get('name','ID: '+rel['target_concept_id'])
                edge_title = f"De: {source_name}\nPara: {target_name}\nTipo: {rel.get('type', 'N/A')}"
                if rel.get('description'):
                    edge_title += f"\nDesc: {rel['description'][:50]}"
                    if len(rel['description']) > 50: edge_title += "..."

                edges.append(Edge(source=rel['source_concept_id'],
                                  target=rel['target_concept_id'],
                                  label=edge_label,
                                  title=edge_title,
                                  arrows="to" # Asegurar que las flechas se muestren
                                  ))

    agraph_height = 800 # Variable para la altura del grafo
    agraph_config = Config(
        width="100%",
        height=agraph_height,
        directed=True,
        physics={"enabled": True,
                   "barnesHut": {"gravitationalConstant": -15000, "centralGravity": 0.1, "springLength": 120, "springConstant": 0.05, "damping": 0.09},
                   "minVelocity": 0.75, # Detener la simulación cuando se estabilice
                   "solver": "barnesHut"},
        hierarchical=False,
        interaction={"navigationButtons": True, "tooltipDelay": 150, "hover": True, "zoomView": True, "dragNodes": True},
        nodes={"font": {"size": 10}}, # Tamaño de fuente para etiquetas de nodo
        edges={"font": {"size": 8, "align": "middle"}, "smooth": {"type": "cubicBezier", "roundness": 0.7}, "arrows": "to"}
    )

    if not nodes:
        st.info("No hay conceptos para mostrar con los filtros seleccionados.")
    else:
        num_nodes_display = len(nodes)
        num_edges_display = len(edges)
        st.info(f"Mostrando {num_nodes_display} conceptos y {num_edges_display} relaciones. Haz clic en un nodo para ver detalles en la barra lateral.")

        # Solo renderizar el grafo si hay nodos, para evitar errores con agraph
        if num_nodes_display > 0:
            selected_node_id = agraph(nodes=nodes, edges=edges, config=agraph_config)

            if selected_node_id and selected_node_id in concept_map:
                selected_concept_details = concept_map[selected_node_id]
                st.sidebar.subheader(f"Detalles del Concepto:")
                st.sidebar.markdown(f"**Nombre:** {selected_concept_details['name']}")
                st.sidebar.markdown(f"**ID:** `{selected_concept_details['id']}`")
                st.sidebar.markdown(f"**Tipo:** {selected_concept_details['concept_type']}")
                st.sidebar.markdown(f"**Descripción:** {selected_concept_details.get('description', 'N/A')}")
                st.sidebar.markdown("**Propiedades:**")
                st.sidebar.json(selected_concept_details.get('properties', {}), expanded=False)
                st.sidebar.markdown(f"**Creado:** {selected_concept_details.get('created_at', 'N/A')}")
                st.sidebar.markdown(f"**Actualizado:** {selected_concept_details.get('updated_at', 'N/A')}")
            elif selected_node_id:
                st.sidebar.warning(f"No se encontraron detalles completos para el nodo: {selected_node_id}")
        else:
            st.info("No hay nodos para mostrar después de aplicar los filtros.")

# --- Sección 2: Visualización de Jerarquía de Síntesis ---
def display_synthesis_hierarchy(all_concepts: Optional[List[Dict[str, Any]]]):
    st.markdown("Selecciona un concepto de alto nivel (Modelo Unificado, Teoría Comprehensiva, Mini-Teoría) para ver su jerarquía de componentes.")

    if not AGRAPH_AVAILABLE:
        st.warning("streamlit-agraph no está instalado. La visualización de grafos jerárquicos no está disponible.")
        return

    if not all_concepts:
        st.warning("No hay conceptos cargados para seleccionar.")
        return

    hierarchical_concept_types = [
        "UNIFIED_MODEL",
        "COMPREHENSIVE_THEORY",
        "MINI_THEORY",
        "PROPOSITION", # También podría ser interesante ver de qué clúster viene una proposición
        "CLUSTER"      # O qué UCMs componen un clúster
    ]

    selectable_concepts = [c for c in all_concepts if c.get('concept_type') in hierarchical_concept_types]

    if not selectable_concepts:
        st.info("No hay conceptos de tipo Modelo, Teoría, Proposición o Clúster para mostrar su jerarquía.")
        return

    concept_options = {f"{c['name']} ({c['concept_type']}, ID: ...{c['id'][-6:]})": c['id'] for c in selectable_concepts}

    selected_option = st.selectbox(
        "Selecciona un Concepto para ver su Jerarquía:",
        options=[""] + list(concept_options.keys()), # Añadir opción vacía para no seleccionar nada
        key="hierarchy_concept_select"
    )

    if selected_option and concept_options[selected_option]:
        selected_concept_id = concept_options[selected_option]
        st.write(f"Cargando jerarquía para el concepto ID: `{selected_concept_id}`")

        hierarchy_data = get_api_data(f"/eje-y/visualization/hierarchy_graph/{selected_concept_id}")

        if hierarchy_data and hierarchy_data.get('nodes'):
            nodes = [
                Node(
                    id=n['id'],
                    label=n['label'][:30] + "..." if len(n['label']) > 30 else n['label'],
                    title=f"Nombre: {n['label']}\nTipo: {n['type']}\nID: {n['id']}",
                    color=CONCEPT_TYPE_COLORS.get(n['type'], CONCEPT_TYPE_COLORS["DEFAULT"]),
                    shape="box", # Usar 'box' o 'database' para jerarquía
                    level=n.get('level') # Usar el nivel si la API lo proporciona
                ) for n in hierarchy_data['nodes']
            ]
            edges = [
                Edge(
                    source=e['from'], # El schema usa 'from' como alias de from_node
                    target=e['to'],  # El schema usa 'to' como alias de to_node
                    label=e.get('label', ''),
                    arrows="to"
                ) for e in hierarchy_data['edges']
            ]

            # Configuración para layout jerárquico
            hierarchical_config = Config(
                width="100%",
                height=600,
                directed=True,
                physics=False, # A menudo se desactiva para layouts jerárquicos puros
                hierarchical={
                    "enabled": True,
                    "direction": "DU",  # De abajo hacia arriba (UCMs en la base)
                    "sortMethod": "directed", # Trata de minimizar cruces de aristas
                    "levelSeparation": 150,
                    "nodeSpacing": 100,
                    "treeSpacing": 200
                },
                interaction={"navigationButtons": True, "tooltipDelay": 150, "hover": True, "zoomView": True},
                nodes={"font": {"size": 10}},
                edges={"font": {"size": 8}, "smooth": False} # Aristas rectas para jerarquía
            )

            agraph(nodes=nodes, edges=edges, config=hierarchical_config)
        elif hierarchy_data: # Nodos vacíos pero respuesta OK
            st.info(f"No se encontró una jerarquía o componentes para el concepto seleccionado (ID: {selected_concept_id}).")
        else:
            # get_api_data ya muestra un error si la llamada falla.
            st.warning(f"No se pudieron obtener datos de jerarquía para el concepto ID: {selected_concept_id}.")
    else:
        st.info("Selecciona un concepto de la lista para visualizar su jerarquía.")


# --- Main App ---
def main():
    st.title("🔬 Aletheia - Dashboard del Grafo de Conocimiento")
    st.markdown("Explora los conceptos y relaciones generados y sintetizados por el sistema Aletheia.")

    # Check for token before attempting to load any data dependent tabs
    if not st.session_state.jwt_token:
        st.info("Introduce un token JWT en la barra lateral para continuar.")
        return # Stop further execution if no token

    # Attempt to load concepts once for reuse if needed, e.g., for hierarchy selector
    # This is a basic approach; more sophisticated state management might be needed for large apps
    # For now, let's assume display_synthesis_hierarchy will fetch its own list or be adapted.
    # The current display_full_knowledge_graph fetches its own concepts.

    tab_explorador, tab_jerarquia, tab_estadisticas = st.tabs([
        "Explorador del Grafo",
        "Visor de Jerarquía",
        "Estadísticas"
    ])

    with tab_explorador:
        st.header("Explorador del Grafo Completo")
        display_full_knowledge_graph() # This function fetches its own concepts and relationships

    with tab_jerarquia:
        st.header("Visor de Jerarquía de Conceptos")
        # display_synthesis_hierarchy needs a list of all concepts for its dropdown.
        # For simplicity, let's fetch concepts again here or adapt the function.
        # A more optimized way would be to fetch concepts once and pass them around.
        # For now, let's assume it's okay to fetch within the function or it gets adapted.
        # The original code passed 'concepts_data' which was defined in another tab's scope.
        # We need to ensure 'all_concepts' is available.
        # A quick fix for now: fetch concepts if needed by the hierarchy tab
        # This might be redundant if the full graph already loaded them.
        # Consider passing data or having a shared cache if performance becomes an issue.

        # For now, let's modify display_synthesis_hierarchy to fetch its own list of concepts
        # if not provided, or we ensure it's called with the data.
        # The original display_synthesis_hierarchy took `all_concepts` as an argument.
        # Let's make it self-sufficient for now by fetching concepts for the selector.
        all_concepts_for_hierarchy = get_api_data("/eje-x/concepts/") # Fetch concepts for the dropdown
        if all_concepts_for_hierarchy:
            display_synthesis_hierarchy(all_concepts_for_hierarchy)
        else:
            st.warning("No se pudieron cargar los conceptos para el selector de jerarquía.")


    with tab_estadisticas:
        st.header("Estadísticas de Síntesis del Grafo")
        display_synthesis_statistics()

# --- Sección 3: Estadísticas de Síntesis ---
def display_synthesis_statistics():
    st.markdown("Métricas clave y distribución de tipos de conceptos en el grafo de conocimiento.")

    stats_data = get_api_data("/eje-y/visualization/synthesis_statistics")

    if stats_data:
        # Mostrar Overall Stats
        st.subheader("Estadísticas Generales")
        overall_stats = stats_data.get("overall_stats", [])
        if overall_stats:
            # Dividir en columnas para mejor presentación de st.metric
            # Determinar el número de columnas basado en la cantidad de métricas, ej. 3 por fila
            num_metrics = len(overall_stats)
            cols_per_row = 3

            for i in range(0, num_metrics, cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < num_metrics:
                        stat_item = overall_stats[i+j]
                        display_label = stat_item["name"]
                        cols[j].metric(label=display_label, value=stat_item["value"])
                        # Display unit below the metric if it exists and is not None
                        if stat_item.get("unit") is not None: # Check explicitly for None
                            cols[j].markdown(f"<small><i>({stat_item['unit']})</i></small>", unsafe_allow_html=True)

            # Consider pandas table as an alternative if overall_stats structure is complex
            # Example:
            # try:
            #     import pandas as pd
            #     df_overall_stats = pd.DataFrame(overall_stats)
            #     st.table(df_overall_stats.set_index('name')) # Assuming 'name' can be an index
            # except ImportError:
            #     st.json([{"name": s["name"], "value": s["value"], "unit": s.get("unit")} for s in overall_stats])

        else:
            st.info("No hay estadísticas generales disponibles.")

        st.markdown("---")

        # Mostrar Type Distribution
        st.subheader("Distribución de Conceptos por Tipo")
        type_distribution = stats_data.get("type_distribution", {})
        if type_distribution:
            # Convertir a DataFrame para st.bar_chart o st.table
            # import pandas as pd # Necesitaría importarlo al inicio del archivo
            try:
                import pandas as pd
                df_type_dist = pd.DataFrame(list(type_distribution.items()), columns=['Tipo de Concepto', 'Cantidad'])
                st.bar_chart(df_type_dist.set_index('Tipo de Concepto'))

                with st.expander("Ver datos de distribución en tabla"):
                    st.table(df_type_dist)
            except ImportError:
                st.warning("Pandas no está instalado. Mostrando datos de distribución como JSON. `pip install pandas` para gráficos.")
                st.json(type_distribution)
        else:
            st.info("No hay datos de distribución de tipos disponibles.")
    else:
        st.warning("No se pudieron cargar las estadísticas de síntesis desde la API.")


if __name__ == "__main__":
    main()
```

# aletheia_omega/domain/services.py

import gzip
import pickle
from typing import Any, List

from .entities import ModelRepresentation
# Importaciones adicionales para TrajectoryAnalysisService
from .entities import Trajectory, TrajectoryAnalysis, TrajectoryState


class KolmogorovComplexityProxyService:
    """
    Servicio de dominio para calcular un proxy de la Complejidad de Kolmogorov.
    La verdadera K(M) es incomputable. Usamos la longitud de la descripción
    comprimida como una aproximación práctica y efectiva.
    """

    def compute(self, model_content: bytes) -> float:
        """
        Calcula la complejidad de un modelo como la longitud de su representación
        serializada y comprimida con gzip.

        @equations:
            K_L(M) ≈ length(compress(describe(M, L)))
            Donde L es Python (via pickle) y compress es gzip.

        @param model_content: El contenido serializado del modelo.
        @return: Un valor de complejidad no negativo.
        """
        if not model_content:
            return 0.0
        compressed_content = gzip.compress(model_content)
        return float(len(compressed_content))


class LikelihoodService:
    """
    Servicio de dominio para calcular la log-verosimilitud de un modelo
    dado un conjunto de datos. La implementación específica depende del tipo de modelo.
    """

    def compute(self, model_content: bytes, data: Any) -> float:
        """
        Calcula la log-verosimilitud L(Data|Model).

        Esta implementación es un **ejemplo genérico** y debe ser extendida o
        reemplazada por una implementación específica para los modelos en uso.
        Aquí, asumimos que el modelo es un objeto scikit-learn con un método `score`.

        @param model_content: El contenido serializado del modelo.
        @param data: Tupla (X, y) con los datos de entrada y las etiquetas.
        @return: El valor de log-verosimilitud.
        """
        try:
            # Deserializa el modelo
            model_obj = pickle.loads(model_content)

            # Asume que data es una tupla (X, y)
            X, y = data

            if not hasattr(model_obj, "score"):
                raise NotImplementedError("El modelo no tiene un método 'score' para calcular la verosimilitud.")

            # El método 'score' en muchos modelos de scikit-learn devuelve una métrica
            # que puede ser proporcional a la log-verosimilitud.
            # Por ejemplo, en regresión lineal, es el coeficiente R^2.
            # Aquí lo usamos como un proxy directo.
            return float(model_obj.score(X, y))
        except (pickle.UnpicklingError, AttributeError, TypeError, NotImplementedError, ValueError) as e:
            # Si el modelo no se puede cargar o no es compatible, su verosimilitude es mínima.
            # Devolvemos un valor muy negativo para penalizarlo fuertemente.
            # Añadido TypeError y ValueError para capturar problemas si 'data' no es desempaquetable como (X,y)
            return -1e9


class OmegaCostService:
    """
    Implementa el núcleo del Axioma 1 del modelo Ω: el Principio de Mínima Descripción.
    """

    def calculate_mdl_cost(
        self, complexity: float, log_likelihood: float, lambda_param: float
    ) -> float:
        """
        Calcula el coste total de un modelo. El objetivo es minimizar este coste.

        @equations:
            Cost(M) = λ * K(M) - L(D|M)

        @param complexity: La complejidad calculada del modelo, K(M).
        @param log_likelihood: La log-verosimilitud del modelo, L(D|M).
        @param lambda_param: El parámetro de regularización λ, que balancea
                             simplicidad vs. precisión.
        @return: El coste MDL del modelo.
        """
        if lambda_param < 0:
            raise ValueError("El parámetro de regularización λ no puede ser negativo.")

        return (lambda_param * complexity) - log_likelihood


# --- Servicios para la Fase 2: Trayectorias ---

class TrajectoryAnalysisService:
    """
    Implementa la lógica del Axioma 3 para clasificar la dinámica de una trayectoria.
    """
    MIN_STEPS_FOR_ANALYSIS = 5 # Mínimo de modelos en la secuencia para un análisis con sentido
    MIN_STEPS_FOR_STATIONARY_CHECK = 3 # Mínimo de modelos idénticos consecutivos para considerar estacionaria la cola

    def analyze(self, trajectory: Trajectory) -> TrajectoryAnalysis:
        """
        Analiza una trayectoria y la clasifica.

        @param trajectory: La trayectoria de modelos a analizar.
        @return: Un objeto TrajectoryAnalysis con la clasificación.
        """
        if not trajectory or not trajectory.steps:
            # Manejo de caso de trayectoria vacía o sin pasos.
            # trajectory.id podría no existir si trajectory es None.
            # Si trajectory es un objeto pero trajectory.steps está vacío, trajectory.id sí existe.
            traj_id = trajectory.id if trajectory else None # Necesitamos un UUID o None
            # Si traj_id es None, TrajectoryAnalysis podría fallar si espera un UUID.
            # Por ahora, asumimos que una trayectoria siempre tiene un ID si el objeto existe.
            # Si trajectory es None, deberíamos lanzar un error o tener un manejo diferente.
            # Para este caso, si no hay pasos, es indefinida.
            if traj_id is None and trajectory is None: # Si la trayectoria en sí es None
                 # No podemos crear TrajectoryAnalysis sin un trajectory_id.
                 # Esto indica un problema de llamada, el servicio espera una Trajectory.
                 raise ValueError("Se intentó analizar una trayectoria nula.")


            return TrajectoryAnalysis(
                trajectory_id=trajectory.id, # Asumimos que trajectory.id existe
                state=TrajectoryState.UNDEFINED,
                comment="La trayectoria está vacía o no tiene pasos.",
                step_count=0
            )

        steps = trajectory.steps
        step_count = len(steps)

        if step_count < self.MIN_STEPS_FOR_ANALYSIS:
            return TrajectoryAnalysis(
                trajectory_id=trajectory.id,
                state=TrajectoryState.UNDEFINED,
                comment=f"Se requieren al menos {self.MIN_STEPS_FOR_ANALYSIS} pasos para el análisis (actuales: {step_count}).",
                step_count=step_count
            )

        # Simplificación para el MVP: La lógica real podría ser mucho más compleja,
        # involucrando métricas de distancia de Kolmogorov, análisis espectral, etc.
        # Aquí usamos una heurística basada en la identidad de los modelos.

        # Lógica para ESTACIONARIA (Refinada)
        # La cola debe tener al menos MIN_STEPS_FOR_STATIONARY_CHECK y ser al menos un tercio de la longitud.
        # Y la trayectoria total debe tener al menos MIN_STEPS_FOR_ANALYSIS.
        # El chequeo de MIN_STEPS_FOR_ANALYSIS ya se hizo arriba.

        # Determinar el tamaño de la cola a revisar para estacionariedad.
        # Debe ser como mínimo MIN_STEPS_FOR_STATIONARY_CHECK.
        # Y también consideramos una fracción de la longitud total (ej. 1/3).
        # La cantidad de pasos en la cola que deben ser idénticos.
        # Usamos max para asegurar que tail_size sea al menos MIN_STEPS_FOR_STATIONARY_CHECK,
        # pero solo si step_count es suficientemente grande para soportar esto.
        # Si step_count es 5 y MIN_STEPS_FOR_STATIONARY_CHECK es 3, tail_size es 3.
        # Si step_count es 9 y MIN_STEPS_FOR_STATIONARY_CHECK es 3, step_count // 3 es 3, tail_size es 3.
        # Si step_count es 6 y MIN_STEPS_FOR_STATIONARY_CHECK es 3, step_count // 3 es 2, tail_size es 3.
        tail_size_candidate_one_third = step_count // 3
        tail_size = max(self.MIN_STEPS_FOR_STATIONARY_CHECK, tail_size_candidate_one_third)

        # Asegurarse de que la trayectoria sea lo suficientemente larga para una cola de este tamaño.
        # Esto ya está cubierto por MIN_STEPS_FOR_ANALYSIS si MIN_STEPS_FOR_STATIONARY_CHECK <= MIN_STEPS_FOR_ANALYSIS / 3 (aprox)
        # o si MIN_STEPS_FOR_STATIONARY_CHECK es el factor dominante y es <= MIN_STEPS_FOR_ANALYSIS.
        # El chequeo principal es que la longitud de la cola que se toma no exceda la longitud de los pasos disponibles.
        # Lo cual no sucederá con steps[-tail_size:].

        last_n_model_identifiers = [s.model.identifier for s in steps[-tail_size:]]

        # Verificar que la cola no esté vacía (ya cubierto por tail_size >= MIN_STEPS_FOR_STATIONARY_CHECK y MIN_STEPS_FOR_ANALYSIS)
        # y que todos los modelos en la cola sean idénticos.
        if len(last_n_model_identifiers) >= self.MIN_STEPS_FOR_STATIONARY_CHECK and \
           len(set(last_n_model_identifiers)) == 1:
            return TrajectoryAnalysis(
                trajectory_id=trajectory.id,
                state=TrajectoryState.STATIONARY,
                comment=f"La trayectoria parece haber convergido al modelo '{last_n_model_identifiers[0]}'.",
                step_count=step_count
            )

        # Lógica para OSCILATORIA: Los modelos recientes (últimos MIN_STEPS_FOR_ANALYSIS) se repiten en un ciclo pequeño.
        # Usamos todos los pasos si son menos que MIN_STEPS_FOR_ANALYSIS * 2 para tener una ventana razonable
        # o una ventana de MIN_STEPS_FOR_ANALYSIS como mínimo.
        # La propuesta original usa MIN_STEPS_FOR_ANALYSIS, lo cual es razonable.
        recent_model_identifiers = [s.model.identifier for s in steps[-self.MIN_STEPS_FOR_ANALYSIS:]]
        unique_recent_models = set(recent_model_identifiers)

        # Si hay entre 2 y un número pequeño de modelos únicos (ej. 2 o 3) en la ventana reciente,
        # y estos se repiten, podría ser oscilatoria. La propuesta es len <= 2 (excluyendo 1, que sería estacionaria).
        if 1 < len(unique_recent_models) <= 2: # Oscila entre 2 modelos
             return TrajectoryAnalysis(
                trajectory_id=trajectory.id,
                state=TrajectoryState.OSCILLATORY,
                comment=f"La trayectoria parece oscilar entre los modelos: {unique_recent_models}.",
                step_count=step_count
            )

        # Por defecto, asumimos PROGRESIVA si no es estacionaria ni oscilatoria (con estas simples heurísticas)
        return TrajectoryAnalysis(
            trajectory_id=trajectory.id,
            state=TrajectoryState.PROGRESSIVE,
            comment="La trayectoria parece estar explorando nuevos modelos o no muestra un patrón claro de convergencia/oscilación con las heurísticas actuales.",
            step_count=step_count
        )

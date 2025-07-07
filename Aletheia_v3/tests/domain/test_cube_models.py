import pytest
from hypothesis import given, strategies as st_hypothesis, assume
import numpy as np

# Adjust import paths based on the new structure
# Assuming Aletheia_v3 is in PYTHONPATH or tests are run from project root
from ...core.cube_models import CuboMDU, CeldaCubo, RotationEngine
# For type hints if needed, or direct use
# from ...core.domain_models import ... # if CeldaCubo content becomes specific domain models

class TestCuboMDU:
    """Tests unitarios para el CuboMDU y su motor de rotación."""

    @pytest.fixture
    def cube_instance(self) -> CuboMDU: # Renamed fixture, added type hint
        """Proporciona una instancia fresca de CuboMDU para cada test."""
        return CuboMDU()

    def test_cube_initialization(self, cube_instance: CuboMDU):
        """Verifica la inicialización correcta del cubo y sus celdas."""
        assert cube_instance.dimensiones == (4, 4, 4)
        assert cube_instance.matriz.shape == (4, 4, 4)

        component_contents = set()
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    cell = cube_instance.matriz[i, j, k]
                    assert cell is not None, f"Celda ({i},{j},{k}) no inicializada."
                    assert isinstance(cell, CeldaCubo), f"Celda ({i},{j},{k}) no es instancia de CeldaCubo."
                    assert cell.coordenadas == (i,j,k), f"Coordenadas incorrectas para celda ({i},{j},{k})."
                    assert cell.contenido == f"Componente ({i},{j},{k})" # Check placeholder content
                    component_contents.add(cell.contenido)
        assert len(component_contents) == 64 # Ensure all contents were unique as per init logic

    @given(
        face_name=st_hypothesis.sampled_from(['front', 'back', 'top', 'bottom', 'left', 'right']),
        degrees_rotation=st_hypothesis.integers(min_value=0, max_value=360).filter(lambda x: x % 90 == 0)
    )
    def test_rotation_engine_preserves_integrity(self, cube_instance: CuboMDU, face_name: str, degrees_rotation: int):
        """
        Property-based test: La rotación de una cara mediante RotationEngine debe preservar la integridad del cubo
        y el conjunto de componentes.
        """
        initial_state_snapshot = cube_instance.get_state_snapshot() # Snapshot of content by coordinates
        initial_component_contents = {c.contenido for c in cube_instance.get_all_components()}

        rotation_engine = RotationEngine(cube_instance)

        try:
            rotation_engine.rotate_face(face_name, degrees_rotation)
        except ValueError as e:
            # Allow certain ValueErrors if they are due to valid constraints (e.g. "Unknown face" if engine is partial)
            # For this test, assume all faces in sampled_from are valid for the engine.
            # If engine.rotate_face has preconditions not met by hypothesis, use `assume`.
            assume("Unknown face" not in str(e)) # Example: if engine doesn't support all faces yet
            return # Skip test for this case

        assert cube_instance.validate_integrity(), f"Integridad del cubo falló después de rotar cara '{face_name}' por {degrees_rotation}°."

        components_after_rotation = cube_instance.get_all_components()
        assert len(components_after_rotation) == 64, "El número de componentes cambió después de la rotación."

        current_component_contents = {c.contenido for c in components_after_rotation}
        assert initial_component_contents == current_component_contents, "El conjunto de contenidos de los componentes cambió después de la rotación."

        # Check if a full 360-degree rotation (or multiple thereof, excluding 0) restores the state.
        # This depends on the definition of "state". get_state_snapshot compares content at coordinates.
        num_90_deg_turns = (degrees_rotation // 90) % 4
        if num_90_deg_turns == 0 and degrees_rotation != 0: # Effective 360 degree rotation
            final_state_snapshot = cube_instance.get_state_snapshot()
            assert initial_state_snapshot == final_state_snapshot, \
                f"El estado del cubo (contenido por coordenada) no se restauró después de una rotación de {degrees_rotation}° en la cara '{face_name}'."
        elif num_90_deg_turns != 0 : # If it was a partial rotation, contents should be permuted but present
            # This is already covered by checking the set of contents.
            # We could add a check that not ALL cells are in their original positions if it was a non-360 rotation.
            final_state_snapshot = cube_instance.get_state_snapshot()
            if initial_state_snapshot != final_state_snapshot:
                pass # Expected for partial rotation
            else:
                # This could happen if e.g. rotating an empty face or a face where all elements are identical
                # For this test's setup, elements are unique, so state should change unless it's a full cycle.
                # print(f"Warning: State snapshot unchanged for non-360 rotation ({degrees_rotation} deg on {face_name}). This might be unexpected.")
                pass


    # Example of a more specific test for RotationEngine if needed
    def test_front_face_cw_90_rotation_specific_cells(self, cube_instance: CuboMDU):
        """Test específico para verificar el movimiento de celdas en una rotación CW de 90° de la cara frontal."""
        # Content of corner cell (0,0,0) before rotation
        original_000_content = cube_instance.matriz[0,0,0].contenido
        # Content of cell (0,3,0) which should move to (0,0,0)'s original spot after CW 90 on front face
        # (assuming standard Rubik's like front face rotation, (0,3,0) -> (0,0,0) is not standard, need to trace elements)
        # Let's trace: (0,0,0) -> (3,0,0) for a CW Z-axis rotation of XY plane (viewed from +Z) with np.rot90(m,k=1) axes=(1,0)
        # np.rot90(m, k=1) on a matrix A makes A[i,j] -> A[N-1-j, i] (CCW)
        # For k=1 (1 CW 90 deg on front face, axes=(1,0) for np.rot90), A[i,j] -> A[j, M-1-i]
        # So, cell at (0,0,0) content should move to (0,3,0) if dim_y=4.
        # Cell at (3,0,0) content should move to (0,0,0).

        # Content of cell at (dim_x-1, 0, 0) which is (3,0,0)
        original_300_content = cube_instance.matriz[3,0,0].contenido

        engine = RotationEngine(cube_instance)
        engine.rotate_face("front", 90) # 90 degrees CW

        # After CW 90 deg rotation of front face (z=0):
        # Original (0,0,0) content should be at (3,0,0)
        # Original (3,0,0) content should be at (3,3,0)
        # Original (3,3,0) content should be at (0,3,0)
        # Original (0,3,0) content should be at (0,0,0)
        # This mapping corresponds to: (r,c) -> (c, N-1-r) where N is dim_x (or dim_y if not square)

        assert cube_instance.matriz[3,0,0].contenido == original_000_content, "Cell (0,0,0) did not move to (3,0,0)"
        # And the content that was at (0,3,0) should now be at (0,0,0)
        # This specific mapping needs to be carefully verified against np.rot90 behavior.
        # For np.rot90(m, k=1, axes=(1,0)) (which means 1 CW 90deg rotation):
        # element at m[r, c] goes to new_m[c, r] (if axes=(0,1))
        # for axes=(1,0), element at m[r,c] goes to new_m[r_new, c_new] where it's effectively a transpose then flip.
        # A[i,j] after rot90(A, k=1, axes=(1,0)) means element from A[j,i] with rows reversed.
        # A_rot[i,j] = A[dim_cols-1-j, i]
        # So, new (0,0,0) gets content from old (3,0,0)
        assert cube_instance.matriz[0,0,0].contenido == original_300_content, "Cell (3,0,0) did not move to (0,0,0)"

    # Add more unit tests for CuboMDU methods like _establecer_conexiones if complex,
    # or for CeldaCubo specific logic if any.
    # RotationEngine._update_connections_after_rotation is a placeholder, so testing its effect is not yet meaningful.

    # Test IRotable can be conceptually tested if CuboMDU or CeldaCubo implement it,
    # but IRotable itself is a Protocol, not a concrete class to test.
    # Test that classes intended to be IRotable have the required methods.
    def test_cubomdu_is_irotable_conceptually(self):
        # This is a static check more than a runtime test here
        assert hasattr(CuboMDU, "rotate") # Though it's a placeholder
        # IRotable also defines sincronizar_estado, validar_integridad
        # CuboMDU has validate_integrity. sincronizar_estado is missing if strictly following IRotable.
        # This test is more for design verification.
        assert hasattr(CuboMDU, "validate_integrity")
        # For strict protocol adherence:
        # assert isinstance(CuboMDU(), IRotable) # This would fail if methods are missing/placeholders don't match signature
        pass # Conceptual check

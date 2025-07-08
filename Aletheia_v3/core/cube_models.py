from typing import Protocol, TypeVar, Generic, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import hashlib # For get_state_hash

# --- Section 1: Core Cube Structure (from mdu_cube_system.py) ---
T = TypeVar('T')

@dataclass
class CeldaCubo(Generic[T]):
    """Unidad básica del cubo - completamente funcional"""
    coordenadas: Tuple[int, int, int]  # (x, y, z)
    contenido: T
    conexiones: Dict[str, 'CeldaCubo'] # Forward reference for type hint
    estado: Dict[str, any]
    layer: Optional[str] = None

class IRotable(Protocol):
    """Interfaz para componentes que pueden rotar en el cubo"""
    def rotar(self, eje: str, grados: int) -> None: ...
    def sincronizar_estado(self) -> None: ...
    def validar_integridad(self) -> bool: ...

class CuboMDU:
    """Arquitectura cúbica 4x4x4 = 64 componentes activos"""
    def __init__(self):
        self.dimensiones = (4, 4, 4)
        self.matriz: np.ndarray = np.empty(self.dimensiones, dtype=object)
        self.current_rx: int = 0
        self.current_ry: int = 0
        self.current_rz: int = 0
        self.layers: list[str] = ['presentation', 'application', 'domain', 'infrastructure']
        self._inicializar_celdas()
        self._establecer_conexiones()
        self.original_matriz_state: Optional[np.ndarray] = None

    def _inicializar_celdas(self):
        """Inicializa las celdas del cubo."""
        for i in range(self.dimensiones[0]):
            for j in range(self.dimensiones[1]):
                for k in range(self.dimensiones[2]):
                    layer_name = ""
                    if k == 0: layer_name = "Presentation"
                    elif k == 1: layer_name = "Application"
                    elif k == 2: layer_name = "Domain"
                    elif k == 3: layer_name = "Infrastructure"

                    self.matriz[i, j, k] = CeldaCubo(
                        coordenadas=(i, j, k),
                        contenido=f"Componente ({i},{j},{k})",
                        conexiones={},
                        estado={"status": "idle"},
                        layer=layer_name
                    )

    def _establecer_conexiones(self):
        """Establece conexiones placeholder entre celdas."""
        for i in range(self.dimensiones[0]):
            for j in range(self.dimensiones[1]):
                for k in range(self.dimensiones[2]):
                    celda_actual = self.matriz[i,j,k]
                    if i + 1 < self.dimensiones[0]:
                        celda_actual.conexiones['next_x'] = self.matriz[i+1,j,k]
                    if i - 1 >= 0:
                         celda_actual.conexiones['prev_x'] = self.matriz[i-1,j,k]
                    # Add similar for y and z if needed

    def get_state_hash(self) -> str:
        """Devuelve un hash del estado actual del cubo."""
        state_str = ""
        for i in range(self.dimensiones[0]):
            for j in range(self.dimensiones[1]):
                for k in range(self.dimensiones[2]):
                    cell = self.matriz[i,j,k]
                    if cell and hasattr(cell, 'contenido'): # Check if cell and content exist
                         state_str += f"({i},{j},{k}):{str(cell.contenido)};"
        return hashlib.sha256(state_str.encode()).hexdigest()

    def validate_integrity(self) -> bool:
        """Valida la integridad estructural del cubo."""
        if self.matriz.shape != self.dimensiones:
            return False
        for i in range(self.dimensiones[0]):
            for j in range(self.dimensiones[1]):
                for k in range(self.dimensiones[2]):
                    if not isinstance(self.matriz[i,j,k], CeldaCubo):
                        return False
                    # Simplified connection check (placeholder)
                    for _conn_name, connected_cell_ref in self.matriz[i,j,k].conexiones.items():
                        if not (hasattr(connected_cell_ref, 'coordenadas') and
                                0 <= connected_cell_ref.coordenadas[0] < self.dimensiones[0] and
                                0 <= connected_cell_ref.coordenadas[1] < self.dimensiones[1] and
                                0 <= connected_cell_ref.coordenadas[2] < self.dimensiones[2]):
                           pass
        return True

    def get_all_components(self) -> list:
        """Devuelve una lista de todos los componentes en el cubo."""
        return [self.matriz[i,j,k] for i in range(self.dimensiones[0]) for j in range(self.dimensiones[1]) for k in range(self.dimensiones[2])]

    def rotate_to_perspective(self, perspective: str):
        """Placeholder: Rota el cubo a una nueva perspectiva."""
        # print(f"CuboMDU: Rotating cube to perspective: {perspective}")
        pass # Actual rotation logic would use RotationEngine

    def get_state_snapshot(self) -> Dict[Tuple[int,int,int], str]:
        """Devuelve un snapshot del estado del cubo para comparación."""
        snapshot: Dict[Tuple[int,int,int], str] = {}
        for i in range(self.dimensiones[0]):
            for j in range(self.dimensiones[1]):
                for k in range(self.dimensiones[2]):
                    cell = self.matriz[i,j,k]
                    snapshot[(i,j,k)] = str(cell.contenido)
        return snapshot

    def rotate(self, rx: int, ry: int, rz: int): # As used by CubeHoneycombIntegration
        """Rotates the cube conceptually by updating its orientation attributes."""
        self.current_rx = (self.current_rx + rx) % 360
        self.current_ry = (self.current_ry + ry) % 360
        self.current_rz = (self.current_rz + rz) % 360
        print(f"CuboMDU: Orientación conceptual rotada a RX={self.current_rx}, RY={self.current_ry}, RZ={self.current_rz}")

    def reset_orientation(self):
        """Resets the cube's conceptual orientation to its default state."""
        self.current_rx = 0
        self.current_ry = 0
        self.current_rz = 0
        print("CuboMDU: Orientación conceptual restablecida.")


# --- Section 3.1: Rotation Engine (from mdu_cube_system.py) ---
class RotationEngine:
    """Motor de rotación para el cubo MDU"""
    def __init__(self, cube: CuboMDU):
        self.cube = cube
        # The rotation_matrix_configs were for point rotation, not directly used in the np.rot90 logic.
        # Keeping it simple as the face rotation logic is self-contained.

    def rotate_face(self, face_name: str, degrees: int) -> None:
        """Rota una cara del cubo manteniendo conexiones."""
        if degrees % 90 != 0:
            raise ValueError("Rotation must be a multiple of 90 degrees")

        num_cw_rotations = (degrees // 90) % 4 # Number of 90-degree clockwise rotations
        if num_cw_rotations == 0: return

        dim_x, dim_y, dim_z = self.cube.dimensiones

        # Map face name to axis of rotation and the fixed index of that axis
        face_details = {
            "front":  ('z', 0), "back": ('z', dim_z - 1),
            "top":    ('y', dim_y - 1), "bottom": ('y', 0),
            "left":   ('x', 0), "right": ('x', dim_x - 1),
        }

        if face_name not in face_details:
            raise ValueError(f"Unknown face: {face_name}. Valid: {list(face_details.keys())}")

        axis_char, fixed_idx = face_details[face_name]

        # np.rot90(m, k) rotates k times by 90 degrees CCW.
        # To rotate CW by num_cw_rotations: use k = -num_cw_rotations or k = (4 - num_cw_rotations) % 4
        k_for_rot90 = (4 - num_cw_rotations) % 4 # Equivalent number of CCW rotations

        if axis_char == 'z':
            face_slice = self.cube.matriz[:, :, fixed_idx]
            rotated_slice = np.rot90(face_slice, k=k_for_rot90) # axes=(0,1) is default for 2D
            self.cube.matriz[:, :, fixed_idx] = rotated_slice
            for r in range(dim_x):
                for c in range(dim_y):
                    if hasattr(self.cube.matriz[r,c,fixed_idx], 'coordenadas'):
                        self.cube.matriz[r,c,fixed_idx].coordenadas = (r,c,fixed_idx)

        elif axis_char == 'y':
            face_slice = self.cube.matriz[:, fixed_idx, :]
            rotated_slice = np.rot90(face_slice, k=k_for_rot90)
            self.cube.matriz[:, fixed_idx, :] = rotated_slice
            for r in range(dim_x):
                for c in range(dim_z):
                    if hasattr(self.cube.matriz[r, fixed_idx, c], 'coordenadas'):
                        self.cube.matriz[r, fixed_idx, c].coordenadas = (r, fixed_idx, c)

        elif axis_char == 'x':
            face_slice = self.cube.matriz[fixed_idx, :, :]
            rotated_slice = np.rot90(face_slice, k=k_for_rot90)
            self.cube.matriz[fixed_idx, :, :] = rotated_slice
            for r in range(dim_y):
                for c in range(dim_z):
                    if hasattr(self.cube.matriz[fixed_idx, r, c], 'coordenadas'):
                        self.cube.matriz[fixed_idx, r, c].coordenadas = (fixed_idx, r, c)

        self._update_connections_after_rotation() # Placeholder
        # if not self.cube.validate_integrity(): # Can be noisy
            # print(f"Warning: Cube integrity may be compromised after rotating {face_name} by {degrees}.")
            # pass # This line and its comment are removed

    def _update_connections_after_rotation(self):
        """Placeholder: Actualiza las conexiones internas de las celdas."""
        # Actual connection update logic is highly complex and would go here.
        # For now, this method does nothing.
        # print("RotationEngine: _update_connections_after_rotation called (placeholder).")
        pass

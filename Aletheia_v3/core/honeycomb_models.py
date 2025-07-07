from typing import Set, Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field # Added import for dataclass and field
import asyncio
from enum import Enum
import hashlib
import heapq # For PathOptimizer

# Assuming domain_models and cube_models might be needed for type hints or specific interactions
# For now, keeping imports minimal until cross-dependencies are fully mapped.
# from .cube_models import CuboMDU # Example, if Honeycomb interacts with CuboMDU directly

class CellState(Enum):
    """Estados posibles de una celda en la colmena"""
    IDLE = "idle"
    PROCESSING = "processing"
    SYNCING = "syncing"
    COMPLETE = "complete"
    ERROR = "error"

class HexagonalCell:
    """Celda hexagonal en la colmena de procesamiento"""
    def __init__(self, position: Tuple[int, int, int], layer: str): # q, r, layer_idx
        self.position = position
        self.layer = layer
        self.state = CellState.IDLE
        self.neighbors: Set['HexagonalCell'] = set()
        self.data_buffer: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.processing_history: List[Dict[str, Any]] = []
        self.cell_id = self._generate_id()

        # Placeholder for layer-specific processing logic, assigned during HoneycombGrid init or dynamically
        self._process_presentation = self._default_process
        self._process_application = self._default_process
        self._process_domain = self._default_process
        self._process_infrastructure = self._default_process

    def _generate_id(self) -> str:
        """Genera ID único basado en posición y capa"""
        content = f"{self.layer}:{self.position[0]},{self.position[1]},{self.position[2]}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def _default_process(self, data: dict) -> dict:
        # print(f"Cell {self.cell_id} ({self.layer}): Default processing data.") # Can be noisy
        await asyncio.sleep(0.01) # Simulate work
        return {"processed_by": self.cell_id, "original_data_snippet": str(data)[:50]}

    async def process_data(self, data: dict) -> dict:
        """Procesa datos según la lógica de la capa"""
        self.state = CellState.PROCESSING
        try:
            if self.layer == "presentation": result = await self._process_presentation(data)
            elif self.layer == "application": result = await self._process_application(data)
            elif self.layer == "domain": result = await self._process_domain(data)
            elif self.layer == "infrastructure": result = await self._process_infrastructure(data)
            else: raise ValueError(f"Unknown layer in HexagonalCell: {self.layer}")

            self.processing_history.append({
                'timestamp': asyncio.get_event_loop().time(),
                'input_hash': hashlib.sha256(str(data).encode()).hexdigest()[:8],
                'output_hash': hashlib.sha256(str(result).encode()).hexdigest()[:8]
            })
            self.state = CellState.COMPLETE
            return result
        except Exception as e:
            self.state = CellState.ERROR
            # print(f"Error in cell {self.cell_id} processing: {e}") # For debugging
            raise e

    async def sync_with_neighbors(self) -> None:
        """Sincroniza estado con celdas vecinas"""
        self.state = CellState.SYNCING
        sync_tasks = [self._sync_with_cell(neighbor) for neighbor in self.neighbors]
        await asyncio.gather(*sync_tasks)
        self.state = CellState.IDLE

    async def _sync_with_cell(self, neighbor: 'HexagonalCell'):
        if not self.data_buffer.empty():
            data_to_send = await self.data_buffer.get()
            # print(f"Cell {self.cell_id} syncing with {neighbor.cell_id}, sending {str(data_to_send)[:30]}")
            await neighbor.data_buffer.put(data_to_send)

class HoneycombGrid:
    """Grid de colmena para procesamiento distribuido"""
    def __init__(self, radius: int = 3):
        self.radius = radius
        self.cells: Dict[Tuple[int, int, int], HexagonalCell] = {}
        self.layers = ['presentation', 'application', 'domain', 'infrastructure']
        self._initialize_grid()

    def _initialize_grid(self):
        for layer_idx, layer_name in enumerate(self.layers):
            for q_coord in range(-self.radius, self.radius + 1):
                for r_coord in range(max(-self.radius, -q_coord - self.radius),
                               min(self.radius, -q_coord + self.radius) + 1):
                    pos_axial_layer = (q_coord, r_coord, layer_idx)
                    cell = HexagonalCell(pos_axial_layer, layer_name)
                    self.cells[pos_axial_layer] = cell
        self._connect_neighbors()

    def _connect_neighbors(self):
        axial_directions = [(1,0), (0,1), (-1,1), (-1,0), (0,-1), (1,-1)]
        for pos, cell in self.cells.items():
            q, r, layer_idx = pos
            for dq, dr in axial_directions:
                neighbor_q, neighbor_r = q + dq, r + dr
                if (neighbor_q, neighbor_r, layer_idx) in self.cells:
                    cell.neighbors.add(self.cells[(neighbor_q, neighbor_r, layer_idx)])
            for layer_offset in [-1, 1]:
                adjacent_layer_idx = layer_idx + layer_offset
                if 0 <= adjacent_layer_idx < len(self.layers):
                    if (q, r, adjacent_layer_idx) in self.cells:
                        cell.neighbors.add(self.cells[(q, r, adjacent_layer_idx)])

class WavePropagation:
    """Propagación de análisis en ondas a través de la colmena"""
    def __init__(self, honeycomb: HoneycombGrid):
        self.honeycomb = honeycomb
        self.wave_front: Set[HexagonalCell] = set()
        self.processed_cells: Set[str] = set()

    async def propagate_analysis(
        self, start_cell: HexagonalCell, initial_data: dict
    ) -> Dict[str, Any]:
        self.wave_front.clear()
        self.processed_cells.clear()

        self.wave_front.add(start_cell)
        wave_results: Dict[str, Any] = {}
        processing_path_map: Dict[str, List[str]] = {start_cell.cell_id: [start_cell.cell_id]}

        wave_number = 0
        while self.wave_front:
            wave_number += 1
            current_wave_cells = list(self.wave_front)
            self.wave_front.clear()

            tasks_with_cells: List[Tuple[HexagonalCell, asyncio.Future]] = []
            for cell_in_wave in current_wave_cells:
                if cell_in_wave.cell_id not in self.processed_cells:
                    path_to_current = processing_path_map.get(cell_in_wave.cell_id, [cell_in_wave.cell_id])
                    coro = self._process_cell(cell_in_wave, initial_data, wave_number, path_to_current)
                    tasks_with_cells.append((cell_in_wave, coro)) # Store cell with coroutine

            gathered_results = await asyncio.gather(*(coro for _, coro in tasks_with_cells), return_exceptions=True)

            for i, (cell, _) in enumerate(tasks_with_cells):
                if cell.cell_id in self.processed_cells: continue

                result_or_exc = gathered_results[i]

                if not isinstance(result_or_exc, Exception):
                    wave_results[cell.cell_id] = result_or_exc
                    self.processed_cells.add(cell.cell_id)

                    current_path = processing_path_map.get(cell.cell_id, [cell.cell_id])
                    for neighbor in cell.neighbors:
                        if neighbor.cell_id not in self.processed_cells:
                            self.wave_front.add(neighbor)
                            if neighbor.cell_id not in processing_path_map or \
                               len(processing_path_map[neighbor.cell_id]) > len(current_path) + 1:
                                 processing_path_map[neighbor.cell_id] = current_path + [neighbor.cell_id]
                else:
                    print(f"WaveProp: Error processing cell {cell.cell_id}: {result_or_exc}")

            if current_wave_cells:
                await self._sync_wave_boundary(current_wave_cells)

        return self._aggregate_results(wave_results)

    async def _process_cell(
        self, cell: HexagonalCell, data: dict, wave_num: int, path: List[str]
    ) -> dict:
        enriched_data = {
            **data, 'wave_number': wave_num, 'cell_position': cell.position,
            'processing_path_ids': path
        }
        return await cell.process_data(enriched_data)

    async def _sync_wave_boundary(self, wave_cells: List[HexagonalCell]):
        # print(f"WaveProp: Syncing boundary of {len(wave_cells)} cells (placeholder).")
        pass

    def _aggregate_results(self, wave_results: Dict[str, Any]) -> Dict[str, Any]:
        # print(f"WaveProp: Aggregating results from {len(wave_results)} cells.")
        summary = {
            "num_cells_processed_in_wave": len(wave_results),
            "sample_result_keys": list(list(wave_results.values())[0].keys()) if wave_results else []
        }
        return {"all_wave_results_map": wave_results, "aggregation_summary": summary}

import json # For ConsensusEngine comparable value string
from collections import defaultdict # For ConsensusEngine value_counts

class ConsensusEngine:
    """Motor de consenso para resultados distribuidos"""
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.voting_history: List[Dict[str, Any]] = []

    async def achieve_consensus(self, cell_results_map: Dict[str, dict]) -> dict:
        if not cell_results_map: return {"consensus_achieved": False, "reason": "No results provided"}

        value_counts: Dict[str, List[str]] = defaultdict(list)
        for key, result_payload in cell_results_map.items():
            try:
                comparable_value_str = json.dumps(result_payload, sort_keys=True)
            except TypeError:
                comparable_value_str = str(result_payload)
            value_counts[comparable_value_str].append(key)

        if not value_counts:
             return {"consensus_achieved": False, "reason": "Could not process results for consensus"}

        most_common_value_str, supporting_keys = max(value_counts.items(), key=lambda item: len(item[1]), default=("",[]))

        num_participants = len(cell_results_map)
        confidence = len(supporting_keys) / num_participants if num_participants > 0 else 0

        consensus_data: Dict[str, Any]
        if confidence >= self.threshold and most_common_value_str:
            consensus_payload = cell_results_map[supporting_keys[0]] if supporting_keys else {}
            consensus_data = {
                'consensus_achieved': True, 'result_payload': consensus_payload,
                'confidence': confidence,
                'supporting_result_keys': supporting_keys,
                'num_participants': num_participants
            }
        else:
            consensus_data = await self._byzantine_consensus(cell_results_map)

        self.voting_history.append({**consensus_data, 'timestamp': asyncio.get_event_loop().time()})
        if len(self.voting_history) > 100: self.voting_history.pop(0)
        return consensus_data

    async def _byzantine_consensus(self, cell_results_map: Dict[str, dict]) -> dict:
        # print("ConsensusEngine: Byzantine consensus fallback (placeholder).")
        return {
            "consensus_achieved": False,
            "reason": "Threshold not met and Byzantine consensus not fully implemented",
            "details": "Majority vote failed. Defaulting to no consensus.",
            "num_participants": len(cell_results_map),
            "result_payload": None
        }

from dataclasses import field # Already imported at top, but good for context here

@dataclass
class PathNode:
    cell: HexagonalCell
    cost: float
    f_score: float
    path: List[HexagonalCell] = field(default_factory=list)
    def __lt__(self, other: 'PathNode') -> bool: # Added type hint for other
        return self.f_score < other.f_score

class PathOptimizer: # CuboMDU is not used here, only HoneycombGrid
    def __init__(self, honeycomb: HoneycombGrid): # Removed cube: CuboMDU
        self.honeycomb = honeycomb
        self.path_cache: Dict[Tuple[str, str, str], Optional[List[HexagonalCell]]] = {}


    def find_optimal_path(
        self, start_cell: HexagonalCell, goal_cell: HexagonalCell, constraints: dict
    ) -> Optional[List[HexagonalCell]]:
        cache_key = (start_cell.cell_id, goal_cell.cell_id, str(constraints))
        if cache_key in self.path_cache: return self.path_cache[cache_key]

        open_set_pq: List[PathNode] = []
        start_f_score = self._heuristic(start_cell, goal_cell)
        heapq.heappush(open_set_pq, PathNode(start_cell, 0, start_f_score, [start_cell]))

        g_scores: Dict[str, float] = {start_cell.cell_id: 0}

        while open_set_pq:
            current_node = heapq.heappop(open_set_pq)
            current_cell = current_node.cell

            if current_cell.cell_id == goal_cell.cell_id:
                self.path_cache[cache_key] = current_node.path
                return current_node.path

            for neighbor_cell in current_cell.neighbors:
                move_cost = self._calculate_move_cost(current_cell, neighbor_cell, constraints)
                if move_cost == float('inf'): continue

                tentative_g_score = g_scores.get(current_cell.cell_id, float('inf')) + move_cost

                if tentative_g_score < g_scores.get(neighbor_cell.cell_id, float('inf')):
                    g_scores[neighbor_cell.cell_id] = tentative_g_score
                    heuristic_cost = self._heuristic(neighbor_cell, goal_cell)
                    f_score = tentative_g_score + heuristic_cost
                    new_path = current_node.path + [neighbor_cell]
                    heapq.heappush(open_set_pq, PathNode(neighbor_cell, tentative_g_score, f_score, new_path))
        self.path_cache[cache_key] = None # Cache miss if no path found
        return None

    def _heuristic(self, cell1: HexagonalCell, cell2: HexagonalCell) -> float:
        (q1,r1,l1) = cell1.position; (q2,r2,l2) = cell2.position
        s1 = -q1-r1; s2 = -q2-r2
        hex_dist = (abs(q1-q2) + abs(r1-r2) + abs(s1-s2)) / 2.0
        layer_dist = abs(l1-l2)
        return hex_dist + layer_dist * 5.0

    def _calculate_move_cost(self, from_c: HexagonalCell, to_c: HexagonalCell, constr: dict) -> float:
        cost = 1.0
        if from_c.layer != to_c.layer: cost *= constr.get('layer_change_penalty', 2.0)
        if to_c.state == CellState.PROCESSING: cost *= constr.get('busy_penalty', 3.0)
        # if self._has_affinity(from_c, to_c): cost *= constr.get('affinity_bonus', 0.8) # Placeholder
        return cost

    # def _has_affinity(self, c1: HexagonalCell, c2: HexagonalCell) -> bool: return False # Placeholder, removed as not used

import random # For ReplicationManager
from datetime import datetime # For ReplicationManager checkpoint timestamp

class ReplicationManager:
    def __init__(self, honeycomb_grid: HoneycombGrid, replication_factor: int = 3):
        self.replication_factor = max(1, replication_factor)
        self.replica_map: Dict[str, List[HexagonalCell]] = {}
        self.checkpoints: List[Dict[str, Any]] = []
        self.honeycomb = honeycomb_grid

    async def replicate_analysis(self, primary_cell: HexagonalCell, data: dict, analysis_id: str) -> List[Tuple[HexagonalCell, dict]]:
        all_cells_list = list(self.honeycomb.cells.values())
        potential_replicas = [c for c in all_cells_list if c.cell_id != primary_cell.cell_id]

        num_additional_replicas_needed = self.replication_factor - 1

        replica_cells: List[HexagonalCell] = []
        if num_additional_replicas_needed > 0:
            if len(potential_replicas) < num_additional_replicas_needed:
                # print(f"Warning: Not enough distinct cells for {num_additional_replicas_needed} additional replicas. Using {len(potential_replicas)}.")
                replica_cells = potential_replicas
            else:
                replica_cells = random.sample(potential_replicas, num_additional_replicas_needed)

        tasks_with_cells_info: List[Tuple[HexagonalCell, Dict[Any, Any]]] = [(primary_cell, data.copy())]
        for rep_cell in replica_cells:
            tasks_with_cells_info.append((rep_cell, data.copy()))

        coroutines = [cell.process_data(d.copy()) for cell, d in tasks_with_cells_info] # Ensure data is copied for each task
        results_or_exceptions = await asyncio.gather(*coroutines, return_exceptions=True)

        valid_results_tuples: List[Tuple[HexagonalCell, dict]] = []
        failed_tasks_for_handler: List[Tuple[HexagonalCell, dict]] = []

        for i, (cell, original_data_for_task) in enumerate(tasks_with_cells_info):
            outcome = results_or_exceptions[i]
            if not isinstance(outcome, Exception):
                valid_results_tuples.append((cell, outcome))
            else:
                # print(f"ReplicationManager: Cell {cell.cell_id} failed initial processing: {outcome}")
                failed_tasks_for_handler.append((cell, original_data_for_task))

        if failed_tasks_for_handler:
            await self._handle_failures(failed_tasks_for_handler)

        successful_cells_after_initial_try = [cell for cell, _ in valid_results_tuples]
        if successful_cells_after_initial_try:
             self.replica_map[analysis_id] = successful_cells_after_initial_try

        return valid_results_tuples

    async def _handle_failures(self, failed_tasks_with_data: List[Tuple[HexagonalCell, dict]]):
        for cell, original_data in failed_tasks_with_data:
            # print(f"ReplicationManager: Attempting recovery for cell {cell.cell_id}.")
            try:
                cell.state = CellState.IDLE
                await cell.process_data(original_data.copy()) # Copy data for retry
                # print(f"Cell {cell.cell_id} recovered after retry.")
            except Exception as e_retry:
                cell.state = CellState.ERROR
                # print(f"Cell {cell.cell_id} failed recovery: {e_retry}")
                await self._notify_cell_failure(cell, e_retry)

    async def _notify_cell_failure(self, cell: HexagonalCell, error: Exception):
        # print(f"MONITORING_ALERT: Cell {cell.cell_id} permanently failed: {error}")
        pass # Placeholder for actual notification

    def create_checkpoint(self, analysis_id: str, current_state_data: dict) -> str:
        checkpoint_id = hashlib.sha256(f"{analysis_id}{str(current_state_data)}{datetime.now()}".encode()).hexdigest()[:16]
        self.checkpoints.append({
            'id': checkpoint_id, 'analysis_id': analysis_id,
            'timestamp': asyncio.get_event_loop().time(), # Consider time.time() for non-async context if needed
            'state_data_snippet': str(current_state_data)[:100]
        })
        if len(self.checkpoints) > 10: self.checkpoints.pop(0)
        return checkpoint_id

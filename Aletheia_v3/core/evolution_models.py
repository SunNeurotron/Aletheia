from typing import List, Tuple, Dict, Optional, Any
import random
import numpy as np
from collections import defaultdict
from dataclasses import dataclass # Added import

@dataclass # Added dataclass decorator
class StrategyGenome:
    """Genoma que codifica una estrategia de análisis"""
    genes: Dict[str, Any] = None # type: ignore # Allow None and initialize in post_init or method
    fitness: float = 0.0
    generation: int = 0

    def __post_init__(self): # Use post_init for default gene generation
        if self.genes is None:
            self.genes = self._random_genome()

    def _random_genome(self) -> Dict[str, Any]:
        """Genera genoma aleatorio"""
        return {
            'depth_weight': random.random(),
            'breadth_weight': random.random(),
            'temporal_weight': random.random(),
            'causal_weight': random.random(),
            'replication_factor': random.randint(1, 3),
            'consensus_threshold': random.uniform(0.5, 0.9),
            'wave_delay': random.uniform(0.0, 0.1),
            'parallelism_degree': random.randint(2, 8)
        }

    def crossover(self, other: 'StrategyGenome') -> 'StrategyGenome':
        """Cruza dos genomas"""
        child_genes: Dict[str, Any] = {} # Ensure type
        parent1_genes = list(self.genes.keys())
        parent2_genes = list(other.genes.keys())
        all_gene_names = list(set(parent1_genes + parent2_genes))

        for gene_name in all_gene_names:
            # Ensure gene exists in at least one parent
            val_self = self.genes.get(gene_name)
            val_other = other.genes.get(gene_name)

            if random.random() < 0.5:
                child_genes[gene_name] = val_self if val_self is not None else val_other
            else:
                child_genes[gene_name] = val_other if val_other is not None else val_self

        child = StrategyGenome(genes=child_genes) # Pass genes directly
        child.generation = max(self.generation, other.generation) + 1
        return child

    def mutate(self, mutation_rate: float = 0.1):
        """Muta el genoma"""
        if self.genes is None: # Should not happen if __post_init__ runs
            self.genes = self._random_genome()

        for gene in list(self.genes.keys()): # Iterate over a copy of keys if modifying dict
            if random.random() < mutation_rate:
                current_value = self.genes[gene]
                if isinstance(current_value, float):
                    new_val = current_value + random.gauss(0, 0.1)
                    # Clamp based on typical ranges
                    if 'weight' in gene or 'threshold' in gene: self.genes[gene] = max(0.0, min(1.0, new_val))
                    elif 'delay' in gene: self.genes[gene] = max(0.0, min(0.5, new_val))
                    else: self.genes[gene] = new_val
                elif isinstance(current_value, int):
                    new_val = current_value + random.randint(-1, 1)
                    if 'factor' in gene or 'degree' in gene: self.genes[gene] = max(1, new_val)
                    # Ensure other integer genes also have valid ranges if applicable
                    else: self.genes[gene] = new_val


# Placeholder for FitnessEvaluator - used by EvolutionaryOptimizer
class FitnessEvaluator:
    async def evaluate(self, genome: StrategyGenome) -> float:
        # print(f"FitnessEvaluator: Evaluating genome (genes: {genome.genes})") # Debug
        if genome.genes is None: return 0.0 # Should not happen
        fitness = 0.0
        fitness += genome.genes.get('replication_factor', 1) * 0.1
        fitness += genome.genes.get('parallelism_degree', 1) * 0.05
        fitness -= genome.genes.get('wave_delay', 0) * 0.2
        return max(0.0, fitness)

import asyncio # For EvolutionaryOptimizer

class EvolutionaryOptimizer:
    """Optimizador evolutivo para estrategias de análisis"""
    def __init__(self, population_size: int = 10): # Smaller for tests
        self.population_size = population_size
        self.population: List[StrategyGenome] = [StrategyGenome(generation=0) for _ in range(population_size)]
        self.generation = 0
        self.best_genome: Optional[StrategyGenome] = None
        self.evolution_history: List[Dict[str, Any]] = []

    async def evolve_generation(
        self,
        fitness_evaluator: FitnessEvaluator # Use the placeholder
    ) -> StrategyGenome:
        """Evoluciona una generación completa"""
        self.generation += 1

        # Evaluar fitness de toda la población
        fitness_evaluation_tasks = [fitness_evaluator.evaluate(genome) for genome in self.population]
        fitness_scores = await asyncio.gather(*fitness_evaluation_tasks)

        for i, genome in enumerate(self.population):
            genome.fitness = fitness_scores[i]

        # Ordenar por fitness
        self.population.sort(key=lambda g: g.fitness, reverse=True)

        # Actualizar mejor genoma
        current_best_in_pop = self.population[0] if self.population else None
        if current_best_in_pop and (not self.best_genome or current_best_in_pop.fitness > self.best_genome.fitness):
            # Create a new StrategyGenome instance for best_genome to avoid modifying it if it's part of population
            self.best_genome = StrategyGenome(genes=current_best_in_pop.genes.copy(),
                                              fitness=current_best_in_pop.fitness,
                                              generation=current_best_in_pop.generation)

        # Registrar historia
        avg_fitness = sum(g.fitness for g in self.population) / len(self.population) if self.population else 0
        self.evolution_history.append({
            'generation': self.generation,
            'best_fitness': self.best_genome.fitness if self.best_genome else (current_best_in_pop.fitness if current_best_in_pop else 0),
            'avg_fitness': avg_fitness,
            'diversity': self._calculate_diversity() # Placeholder
        })

        # Selección y reproducción
        new_population: List[StrategyGenome] = []

        # Elitismo: mantener los mejores
        if self.population:
            elite_size = max(1, self.population_size // 10)
            # Ensure elite individuals are new instances if they might be mutated later
            new_population.extend([StrategyGenome(genes=g.genes.copy(), fitness=g.fitness, generation=g.generation) for g in self.population[:elite_size]])

        # Reproducción
        while len(new_population) < self.population_size:
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()

            if parent1 and parent2: # Ensure parents were selected
                child = parent1.crossover(parent2)
                child.mutate()
                child.generation = self.generation # Set current generation for child
                new_population.append(child)
            elif parent1: # Fallback if only one parent selected
                 mutated_parent1 = StrategyGenome(genes=parent1.genes.copy(), generation=self.generation)
                 mutated_parent1.mutate()
                 new_population.append(mutated_parent1)
            else: # Fallback if no parents selected (should not happen with non-empty pop)
                 new_population.append(StrategyGenome(generation=self.generation))

        self.population = new_population

        return self.best_genome if self.best_genome else StrategyGenome() # Fallback if best_genome is still None

    def _tournament_selection(self, tournament_size: int = 3) -> Optional[StrategyGenome]:
        if not self.population: return None
        actual_tournament_size = min(tournament_size, len(self.population))
        if actual_tournament_size == 0: return None # Should not happen if population checked

        tournament = random.sample(self.population, actual_tournament_size)
        selected = max(tournament, key=lambda g: g.fitness)
        # Return a copy to prevent modification of the selected genome in population
        return StrategyGenome(genes=selected.genes.copy(), fitness=selected.fitness, generation=selected.generation)

    def _calculate_diversity(self) -> float: # Placeholder
        # A simple diversity metric: e.g., number of unique genomes (based on string representation of genes)
        if not self.population: return 0.0
        unique_genomes = set()
        for genome in self.population:
            if genome.genes: # Ensure genes exist
                 # Convert dict to a frozenset of items for hashability
                 frozen_genes = frozenset(genome.genes.items())
                 unique_genomes.add(frozen_genes)
        return len(unique_genomes) / len(self.population) if self.population else 0.0


# Placeholder for AnalysisEnvironment - used by QLearningAnalyzer
class AnalysisEnvironment:
    def __init__(self, max_steps: int = 10):
        self.current_state_idx = 0
        self.max_steps = max_steps # Max steps per episode

    def reset(self) -> str:
        self.current_state_idx = 0
        return f"s_{self.current_state_idx}" # Simpler state representation

    async def step(self, action_idx: int) -> Tuple[str, float, bool]: # Renamed action to action_idx
        # Simulate effect of action
        self.current_state_idx += 1 # Move to next state

        # Reward can depend on action and state transition
        reward = random.uniform(-1.0, 1.0) # Example random reward
        if action_idx == 0: reward += 0.2 # Bonus for a specific action (example)

        done = self.current_state_idx >= self.max_steps
        next_state_repr = f"s_{self.current_state_idx}"

        return next_state_repr, reward, done


class QLearningAnalyzer:
    """Analizador que aprende estrategias óptimas con Q-Learning"""
    def __init__(
        self,
        state_space_size: int = 20, # Conceptual size, actual states are strings
        action_space_size: int = 5,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.2 # Initial epsilon for exploration
    ):
        self.q_table: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(action_space_size))
        self.alpha = learning_rate # Renamed learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.training_episodes_count = 0 # Renamed training_episodes
        self.num_actions = action_space_size # Renamed action_space_size

    def choose_action(self, state_key: str) -> int:
        """Elige acción usando política epsilon-greedy"""
        if random.random() < self.epsilon:
            # Exploración
            return random.randint(0, self.num_actions - 1)
        else:
            # Explotación: Choose best action from Q-table for current state
            # If state not in Q-table yet or all Q-values are zero, pick randomly to encourage exploration
            if state_key not in self.q_table or not np.any(self.q_table[state_key]):
                return random.randint(0, self.num_actions - 1)
            return np.argmax(self.q_table[state_key]) # type: ignore # Numpy argmax is fine

    def update_q_value(
        self,
        state_key: str, # Renamed state to state_key
        action_idx: int, # Renamed action to action_idx
        reward_val: float, # Renamed reward to reward_val
        next_state_key: str # Renamed next_state to next_state_key
    ):
        """Actualiza valor Q usando la ecuación de Bellman"""
        current_q_value = self.q_table[state_key][action_idx] # Renamed current_q

        # If next_state_key is new, its Q-values are all zeros. Max will be 0.
        max_future_q = np.max(self.q_table[next_state_key]) if next_state_key in self.q_table else 0.0

        # Q-learning formula
        new_q_value = current_q_value + self.alpha * (reward_val + self.gamma * max_future_q - current_q_value)

        self.q_table[state_key][action_idx] = new_q_value

    async def train_episode(
        self,
        env: AnalysisEnvironment # Renamed environment to env
    ) -> float:
        """Entrena un episodio completo"""
        current_state = env.reset() # Renamed state to current_state
        episode_total_reward = 0.0 # Renamed total_reward
        is_done = False # Renamed done

        while not is_done:
            chosen_action = self.choose_action(current_state) # Renamed action to chosen_action
            next_observed_state, reward_received, is_done = await env.step(chosen_action) # Renamed vars

            self.update_q_value(current_state, chosen_action, reward_received, next_observed_state)

            current_state = next_observed_state
            episode_total_reward += reward_received

        self.training_episodes_count += 1

        # Decay epsilon to reduce exploration over time
        self.epsilon = max(0.01, self.epsilon * 0.99) # Ensure epsilon doesn't go below a minimum

        return episode_total_reward

"""Small, dependency-free real-valued genetic algorithm."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from random import Random
from typing import Callable, Mapping


@dataclass(frozen=True)
class GeneticAlgorithmResult:
    values: dict[str, float]
    fitness: float
    generations: int
    evaluations: int
    history: tuple[float, ...]


class GeneticAlgorithm:
    """Minimize a numeric fitness function within inclusive real-valued bounds."""

    def __init__(
        self,
        *,
        population_size: int = 60,
        generations: int = 80,
        mutation_rate: float = 0.18,
        crossover_rate: float = 0.85,
        elite_count: int = 4,
        tournament_size: int = 3,
        seed: int = 42,
    ) -> None:
        if population_size < 4:
            raise ValueError("population_size must be at least 4")
        if generations < 1:
            raise ValueError("generations must be positive")
        if not 0 <= mutation_rate <= 1 or not 0 <= crossover_rate <= 1:
            raise ValueError("mutation and crossover rates must be between 0 and 1")
        if not 1 <= elite_count < population_size:
            raise ValueError("elite_count must be between 1 and population_size - 1")
        if not 2 <= tournament_size <= population_size:
            raise ValueError("invalid tournament_size")
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_count = elite_count
        self.tournament_size = tournament_size
        self.seed = seed

    def minimize(
        self,
        fitness_function: Callable[[Mapping[str, float]], float],
        bounds: Mapping[str, tuple[float, float]],
        *,
        initial_values: Mapping[str, float] | None = None,
    ) -> GeneticAlgorithmResult:
        if not bounds:
            raise ValueError("at least one variable bound is required")
        names = tuple(bounds)
        normalized: dict[str, tuple[float, float]] = {}
        for name, pair in bounds.items():
            lower, upper = map(float, pair)
            if not isfinite(lower) or not isfinite(upper) or lower > upper:
                raise ValueError(f"invalid bounds for {name}")
            normalized[name] = (lower, upper)

        rng = Random(self.seed)
        population = [self._random_candidate(rng, normalized) for _ in range(self.population_size)]
        if initial_values is not None:
            population[0] = {
                name: max(normalized[name][0], min(normalized[name][1], float(initial_values[name])))
                for name in names
            }

        evaluations = 0
        history: list[float] = []
        best_values: dict[str, float] | None = None
        best_fitness = float("inf")

        for _ in range(self.generations):
            scored = []
            for candidate in population:
                score = float(fitness_function(candidate))
                evaluations += 1
                if not isfinite(score):
                    score = float("inf")
                scored.append((score, candidate))
            scored.sort(key=lambda item: item[0])
            if scored[0][0] < best_fitness:
                best_fitness = scored[0][0]
                best_values = dict(scored[0][1])
            history.append(best_fitness)

            next_population = [dict(item[1]) for item in scored[: self.elite_count]]
            while len(next_population) < self.population_size:
                parent_a = self._tournament(rng, scored)
                parent_b = self._tournament(rng, scored)
                child = self._crossover(rng, parent_a, parent_b, normalized)
                self._mutate(rng, child, normalized)
                next_population.append(child)
            population = next_population

        if best_values is None:
            raise RuntimeError("genetic algorithm failed to evaluate a candidate")
        return GeneticAlgorithmResult(
            values=best_values,
            fitness=best_fitness,
            generations=self.generations,
            evaluations=evaluations,
            history=tuple(history),
        )

    @staticmethod
    def _random_candidate(rng: Random, bounds: Mapping[str, tuple[float, float]]) -> dict[str, float]:
        return {name: rng.uniform(lower, upper) for name, (lower, upper) in bounds.items()}

    def _tournament(self, rng: Random, scored: list[tuple[float, dict[str, float]]]) -> dict[str, float]:
        contenders = rng.sample(scored, self.tournament_size)
        return dict(min(contenders, key=lambda item: item[0])[1])

    def _crossover(
        self,
        rng: Random,
        parent_a: Mapping[str, float],
        parent_b: Mapping[str, float],
        bounds: Mapping[str, tuple[float, float]],
    ) -> dict[str, float]:
        if rng.random() > self.crossover_rate:
            return dict(parent_a)
        child = {}
        for name, (lower, upper) in bounds.items():
            alpha = rng.random()
            value = alpha * parent_a[name] + (1 - alpha) * parent_b[name]
            child[name] = max(lower, min(upper, value))
        return child

    def _mutate(
        self,
        rng: Random,
        candidate: dict[str, float],
        bounds: Mapping[str, tuple[float, float]],
    ) -> None:
        for name, (lower, upper) in bounds.items():
            if lower == upper:
                candidate[name] = lower
            elif rng.random() < self.mutation_rate:
                span = upper - lower
                candidate[name] = max(lower, min(upper, candidate[name] + rng.gauss(0, span * 0.10)))


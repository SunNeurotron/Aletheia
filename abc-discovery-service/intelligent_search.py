import math
from skopt import gp_minimize
from skopt.space import Real
from skopt.utils import use_named_args
from typing import List
from dataclasses import dataclass

# Lógica de dominio simplificada para ser autocontenida
def gcd(a, b):
    while b: a, b = b, a % b
    return a

@dataclass(frozen=True)
class ABCTriple: a: int; b: int; c: int
@dataclass(frozen=True)
class ABCQuality: triple: ABCTriple; quality: float

def get_quality(a, b, c):
    if a <= 0 or b <= 0: return 0.0
    if gcd(a,b) != 1 or a + b != c: return 0.0
    def _radical(n):
        r, t, i = 1, n, 3
        if t % 2 == 0: r *= 2
        while t % 2 == 0: t //= 2
        while i * i <= t:
            if t % i == 0: r *= i
            while t % i == 0: t //= i
            i += 2
        if t > 1: r *= t
        return r
    rad = _radical(a*b*c)
    return math.log(c) / math.log(rad) if rad < c else 0.0

search_space = [
    Real(1, 15, name='log_a', prior='log-uniform'),
    Real(1, 15, name='log_b', prior='log-uniform')
]

# Variable global para almacenar los mejores hits encontrados
# (En una app real, esto se manejaría de forma más robusta)
found_hits_during_search = []

@use_named_args(search_space)
def objective_function(log_a, log_b) -> float:
    a = int(math.exp(log_a))
    b = int(math.exp(log_b))
    if a >= b: return 0.0
    c = a + b
    quality = get_quality(a, b, c)
    if quality > 1.4:
        found_hits_during_search.append(ABCQuality(triple=ABCTriple(a=a,b=b,c=c), quality=quality))
    return -quality

class IntelligentSearchUseCase:
    def search(self, n_calls: int) -> List[ABCQuality]:
        global found_hits_during_search
        found_hits_during_search = [] # Reset for each run

        gp_minimize(
            func=objective_function,
            dimensions=search_space,
            n_calls=n_calls,
            n_random_starts=10,
            random_state=42
        )
        unique_hits = list({hit.triple: hit for hit in found_hits_during_search}.values())
        unique_hits.sort(key=lambda x: x.quality, reverse=True)
        return unique_hits

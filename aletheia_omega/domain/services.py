# aletheia_omega/domain/services.py

import gzip
import pickle
from typing import Any, List

from .entities import ModelRepresentation


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

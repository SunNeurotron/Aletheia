# Ecuaciones y Referencias Científicas del Módulo Aletheia-Stats

Este documento detalla las formulaciones matemáticas y las referencias clave utilizadas en los análisis estadísticos dentro del módulo Aletheia-Stats.

## 1. Prueba de Normalidad de Shapiro-Wilk

Antes de realizar una prueba t, es común verificar si los datos de las muestras siguen una distribución normal. El módulo Aletheia-Stats utiliza la prueba de Shapiro-Wilk para este propósito.

-   **Hipótesis**:
    -   \(H_0\): Los datos provienen de una población normalmente distribuida.
    -   \(H_1\): Los datos no provienen de una población normally distribuida.
-   **Estadístico de Prueba (W)**:
    El estadístico W se calcula como:
    \[ W = \frac{(\sum_{i=1}^{n} a_i x_{(i)})^2}{\sum_{i=1}^{n} (x_i - \bar{x})^2} \]
    Donde:
    -   \(x_{(i)}\) son las estadísticas de orden de la muestra (datos ordenados).
    -   \(x_i\) son los valores de la muestra.
    -   \(\bar{x}\) es la media de la muestra.
    -   \(a_i\) son coeficientes constantes generados a partir de las medias, varianzas y covarianzas de las estadísticas de orden de una muestra de tamaño \(n\) de una distribución normal estándar. Estos coeficientes son tabulados o calculados.
-   **Interpretación**:
    Un valor pequeño de W (y, correspondientemente, un p-valor pequeño) lleva al rechazo de la hipótesis nula, sugiriendo que los datos no son normales. En `StatsService`, si el p-valor de la prueba de Shapiro-Wilk es menor que un nivel alfa predefinido (ej. 0.05), se emite una advertencia en el comentario del resultado.
-   **Implementación**: Se utiliza `scipy.stats.shapiro`.
-   **Referencia Principal**:
    -   Shapiro, S. S., & Wilk, M. B. (1965). An analysis of variance test for normality (complete samples). *Biometrika*, 52(3/4), 591–611. [JSTOR](https://www.jstor.org/stable/2333709)

## 2. Prueba t de Welch para Dos Muestras Independientes

Para comparar las medias de dos grupos independientes cuando no se puede asumir que las varianzas de las poblaciones son iguales, se utiliza la prueba t de Welch.

-   **Hipótesis (bilateral)**:
    -   \(H_0: \mu_1 = \mu_2\) (Las medias de las dos poblaciones son iguales).
    -   \(H_1: \mu_1 \neq \mu_2\) (Las medias de las dos poblaciones son diferentes).
-   **Estadístico de Prueba (t)**:
    \[ t = \frac{\bar{x}_1 - \bar{x}_2}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}} \]
    Donde:
    -   \(\bar{x}_1, \bar{x}_2\) son las medias muestrales de los grupos 1 y 2, respectivamente.
    -   \(s_1^2, s_2^2\) son las varianzas muestrales (usando \(n-1\) en el denominador) de los grupos 1 y 2.
    -   \(n_1, n_2\) son los tamaños de las muestras de los grupos 1 y 2.
-   **Grados de Libertad (df)**:
    Los grados de libertad se calculan utilizando la ecuación de Welch-Satterthwaite:
    \[ \text{df} \approx \frac{\left(\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}\right)^2}{\frac{\left(\frac{s_1^2}{n_1}\right)^2}{n_1-1} + \frac{\left(\frac{s_2^2}{n_2}\right)^2}{n_2-1}} \]
    El resultado generalmente no es un entero.
-   **Intervalo de Confianza para la Diferencia de Medias (\(\mu_1 - \mu_2\))**:
    Un intervalo de confianza del \((1-\alpha) \times 100\%\) para la diferencia de medias es:
    \[ (\bar{x}_1 - \bar{x}_2) \pm t_{\alpha/2, \text{df}} \times \sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}} \]
    Donde \(t_{\alpha/2, \text{df}}\) es el valor crítico de la distribución t con los grados de libertad calculados y un nivel de significancia \(\alpha/2\) en cada cola.
-   **Implementación**: Se utiliza `scipy.stats.ttest_ind(equal_var=False)`. El cálculo del intervalo de confianza y los grados de libertad se realiza explícitamente en `StatsService` para asegurar la alineación con la teoría y proporcionar estos valores en los resultados.
-   **Referencias Principales**:
    -   Welch, B. L. (1947). The generalization of "Student's" problem when several different population variances are involved. *Biometrika*, 34(1/2), 28–35. [JSTOR](https://www.jstor.org/stable/2332510)
    -   SciPy Documentation: `scipy.stats.ttest_ind`.

## Consideraciones Adicionales

-   **Tamaño Mínimo de Muestra**:
    -   La prueba de Shapiro-Wilk implementada en `scipy.stats.shapiro` requiere al menos 3 muestras.
    -   La prueba t requiere al menos 2 muestras por grupo para calcular la varianza.
    -   El `StatsService` del módulo impone un mínimo de 3 muestras por grupo para poder realizar la prueba de normalidad como paso previo.
-   **Supuestos de la Prueba t de Welch**:
    1.  Las dos muestras son independientes.
    2.  Los datos en cada muestra siguen aproximadamente una distribución normal. (La prueba t es robusta a desviaciones moderadas de la normalidad, especialmente con tamaños de muestra más grandes. La prueba de Shapiro-Wilk ayuda a evaluar esto).
    -   No se asume igualdad de varianzas entre las poblaciones (a diferencia de la prueba t de Student estándar).

Este documento sirve como referencia para la base teórica de los análisis implementados. Para detalles específicos de la implementación, consultar los docstrings y el código fuente dentro del módulo.

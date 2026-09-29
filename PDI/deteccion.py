"""
Detección de manos.

Cada cuadro de la cámara pasa por esta cadena (pipeline):

    cuadro BGR ──> 1. filtrar ──> 2. umbral_amarillo ──> 3. limpiar ──> 4. region_mas_grande ──> 5. Y
                  (desenfoque)    (máscara binaria)      (morfología)   (segmentación)            (centroide)

    1. Filtro:        desenfoque gaussiano. La cámara tiene ruido (píxeles que cambian de color al
                      azar); promediar cada píxel con sus vecinos lo reduce y hace el umbral más estable.
    2. Umbralización: se decide píxel por píxel si es amarillo mirando sus canales R, G y B.
                      El resultado es una máscara binaria: 255 (blanco) = amarillo, 0 (negro) = no.
    3. Morfología:    la máscara tiene puntos sueltos (falsos positivos) y huecos dentro del guante
                      (sombras, arrugas). La apertura borra los puntos y el cierre rellena los huecos.
    4. Segmentación:  se agrupan los píxeles blancos que se tocan en regiones (componentes conectados)
                      y se elige la más grande, que debería ser el guante.
    5. Posición:      el centroide (centro de masa) de la región; para el hockey solo se usa su Y.

La imagen se divide en dos mitades y la cadena se aplica a cada una: izquierda = jugador 1,
derecha = jugador 2. Los umbrales vienen de config.py (y de calibracion.json si se guardó).
"""
import cv2
import numpy as np

from . import config


# ------------------------------------------------------------------ 1. filtro

def filtrar(imagen, kernel=config.KERNEL_DESENFOQUE):
    """
    Desenfoque gaussiano: cada píxel pasa a ser un promedio ponderado de sus vecinos
    (los más cercanos pesan más). `kernel` es el tamaño de la vecindad y debe ser impar.
    Más grande = menos ruido pero bordes más borrosos.
    """
    return cv2.GaussianBlur(imagen, (kernel, kernel), 0)


# ------------------------------------------------------------------ 2. umbralización

def umbral_amarillo(imagen_bgr, r_min=config.R_MIN, g_min=config.G_MIN, b_max=config.B_MAX,
                    dif_rg_max=config.DIF_RG_MAX):
    """
    Máscara binaria (0 o 255) de los píxeles amarillos, usando reglas sobre los canales RGB.

    En RGB el amarillo es rojo + verde sin azul (amarillo puro = R 255, G 255, B 0), así que un
    píxel se considera amarillo si cumple las cuatro condiciones a la vez:
        R >= r_min           tiene bastante rojo
        G >= g_min           tiene bastante verde
        B <= b_max           tiene poco azul (esto descarta el blanco, que tiene R, G y B altos)
        |R - G| <= dif_rg_max el rojo y el verde están equilibrados (esto descarta el naranja,
                              que tiene mucho más rojo que verde, y los verdes)
    """
    # OpenCV guarda los canales en orden B, G, R. Se convierten a int16 porque en uint8 (0 a 255)
    # la resta R - G daría la vuelta: 10 - 20 serían 246 en lugar de -10.
    b = imagen_bgr[:, :, 0].astype(np.int16)
    g = imagen_bgr[:, :, 1].astype(np.int16)
    r = imagen_bgr[:, :, 2].astype(np.int16)

    # cada comparación da una matriz de True/False del tamaño de la imagen; & exige todas a la vez
    amarillo = (r >= r_min) & (g >= g_min) & (b <= b_max) & (np.abs(r - g) <= dif_rg_max)
    return amarillo.astype(np.uint8) * 255


# ------------------------------------------------------------------ 3. morfología

def limpiar(mascara, kernel=config.KERNEL_MORFOLOGIA):
    """
    Limpia la máscara con dos operaciones morfológicas usando un elemento estructurante elíptico:
        apertura = erosión + dilatación: borra manchas más pequeñas que el elemento (ruido)
                   y devuelve al resto su tamaño original.
        cierre   = dilatación + erosión: rellena huecos y grietas pequeñas dentro del guante.
    `kernel` es el tamaño del elemento: más grande = limpia más, pero pierde detalles.
    """
    elemento = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel, kernel))
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, elemento)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, elemento)
    return mascara


# ------------------------------------------------------------------ 4 y 5. segmentación y posición

def region_mas_grande(mascara, area_minima=config.AREA_MINIMA):
    """
    Segmenta la máscara en componentes conectados (grupos de píxeles blancos que se tocan, contando
    también las diagonales: conectividad 8) y devuelve la región más grande como
        (cx, cy, area, (x, y, ancho, alto))
    donde (cx, cy) es el centroide y (x, y, ancho, alto) el rectángulo que la encierra.
    Devuelve None si ninguna región llega a `area_minima` píxeles (así un objeto amarillo pequeño
    del fondo no se confunde con el guante).
    """
    # n: número de regiones (incluido el fondo), stats: x, y, ancho, alto y área de cada región,
    # centroides: (cx, cy) de cada región
    n, _, stats, centroides = cv2.connectedComponentsWithStats(mascara, connectivity=8)
    if n <= 1:  # solo está el fondo
        return None

    # la etiqueta 0 siempre es el fondo, se busca la región más grande entre las demás
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    area = int(stats[i, cv2.CC_STAT_AREA])
    if area < area_minima:
        return None

    x, y, ancho, alto = (int(v) for v in stats[i, :4])
    cx, cy = centroides[i]
    return float(cx), float(cy), area, (x, y, ancho, alto)


# ------------------------------------------------------------------ suavizado temporal

class Suavizado:
    """
    Filtro exponencial (media móvil exponencial) entre cuadros:
        valor = alfa * nuevo + (1 - alfa) * valor_anterior
    El centroide salta unos píxeles de un cuadro a otro aunque la mano esté quieta; este filtro
    lo estabiliza. alfa cerca de 1 = responde rápido pero tiembla; cerca de 0 = suave pero con retraso.
    """

    def __init__(self, alfa=config.SUAVIZADO):
        self.alfa = alfa
        self.valor = None

    def actualizar(self, nuevo):
        if nuevo is None:
            return self.valor  # si se pierde el guante se mantiene la última posición
        if self.valor is None:
            self.valor = nuevo  # primera detección: no hay valor anterior con el que promediar
        else:
            self.valor = self.alfa * nuevo + (1 - self.alfa) * self.valor
        return self.valor


# ------------------------------------------------------------------ detector completo

class DetectorGuantes:
    """
    Aplica toda la cadena a un cuadro y detecta un guante en cada mitad de la imagen:
        mitad izquierda -> jugador 1, mitad derecha -> jugador 2.
    Los umbrales son atributos para poder cambiarlos en vivo (prueba_camara.py los mueve con barras).
    """

    def __init__(self):
        self.suavizado = [Suavizado(), Suavizado()]  # uno por jugador
        self.r_min, self.g_min, self.b_max = config.R_MIN, config.G_MIN, config.B_MAX
        self.dif_rg_max = config.DIF_RG_MAX
        self.area_minima = config.AREA_MINIMA

    def procesar(self, imagen_bgr):
        """
        Procesa un cuadro BGR de la cámara y devuelve (posiciones_y, regiones, mascara):
            posiciones_y: [y_jugador1, y_jugador2], Y del centroide dividida por el alto de la imagen
                          (0.0 arriba, 1.0 abajo) y suavizada. Si un guante se pierde se mantiene
                          su última Y; es None solo si nunca se ha visto.
            regiones:     [region_jugador1, region_jugador2] como las da region_mas_grande(), en
                          coordenadas de la imagen completa; None si no se vio en ESTE cuadro.
            mascara:      máscara binaria limpia de toda la imagen (para mostrarla o depurar).
        """
        alto, ancho = imagen_bgr.shape[:2]
        mitad = ancho // 2

        # pasos 1 a 3 sobre la imagen completa
        suave = filtrar(imagen_bgr)
        mascara = umbral_amarillo(suave, self.r_min, self.g_min, self.b_max, self.dif_rg_max)
        mascara = limpiar(mascara)

        # pasos 4 y 5 en cada mitad, así cada jugador tiene su propio guante
        posiciones, regiones = [], []
        for jugador, (x0, x1) in enumerate(((0, mitad), (mitad, ancho))):
            region = region_mas_grande(mascara[:, x0:x1], self.area_minima)
            if region is not None:
                cx, cy, area, (x, y, w, h) = region
                # la región se buscó dentro de la mitad; se suma x0 para pasarla a la imagen completa
                region = (cx + x0, cy, area, (x + x0, y, w, h))
                y_norm = cy / alto
            else:
                y_norm = None
            posiciones.append(self.suavizado[jugador].actualizar(y_norm))
            regiones.append(region)

        return posiciones, regiones, mascara

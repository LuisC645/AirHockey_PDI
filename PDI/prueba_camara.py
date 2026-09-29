"""
Herramienta de calibración del detector de guantes amarillos (se usa antes de jugar).

Muestra la cámara con la detección de cada jugador y la máscara binaria, y permite ajustar los
umbrales RGB en vivo hasta que solo el guante aparezca en blanco en la máscara. Los valores
guardados con G quedan en calibracion.json y los usa el juego (a través de bridge.py).

Uso (desde la carpeta AirHockey):
    python PDI/prueba_camara.py          -> usa la cámara de config.CAMARA
    python PDI/prueba_camara.py 1        -> usa la cámara 1

Ventanas:
    PDI - Camara    imagen con la posición detectada de cada jugador
    PDI - Mascara   resultado de la umbralización + morfología (blanco = amarillo)
    PDI - Umbrales  barras para ajustar los umbrales en vivo

Teclas:
    clic izquierdo  muestra el color R, G, B del píxel (útil para calibrar con el guante)
    g               guarda los umbrales actuales en calibracion.json (se usan en las próximas ejecuciones)
    q o Esc         salir (sin guardar)
"""
import os
import sys
import time

import cv2

if __package__ in (None, ""):  # permite ejecutarlo como script: python PDI/prueba_camara.py
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PDI import config
from PDI.deteccion import DetectorGuantes

VENTANA_CAMARA = "PDI - Camara"
VENTANA_MASCARA = "PDI - Mascara"
VENTANA_UMBRALES = "PDI - Umbrales"

COLOR_J1 = (92, 92, 255)    # rojo (BGR), igual que la paleta del jugador 1
COLOR_J2 = (219, 189, 100)  # azul (BGR), igual que la paleta del jugador 2

ultimo_clic = None  # (x, y, (r, g, b)) del último píxel pulsado
aviso = ("", 0.0)   # (texto, hora hasta la que se muestra)


def al_hacer_clic(evento, x, y, _flags, imagen):
    """Al hacer clic en la ventana de la cámara, guarda y muestra el color R, G, B de ese píxel."""
    global ultimo_clic
    if evento == cv2.EVENT_LBUTTONDOWN and imagen["actual"] is not None:
        b, g, r = (int(v) for v in imagen["actual"][y, x])
        ultimo_clic = (x, y, (r, g, b))
        print(f"pixel ({x}, {y}) -> R={r} G={g} B={b}")


def crear_barras():
    """Crea la ventana de barras, empezando con los valores actuales de config (o de la calibración)."""
    cv2.namedWindow(VENTANA_UMBRALES)
    cv2.resizeWindow(VENTANA_UMBRALES, 420, 260)
    nada = lambda _v: None
    cv2.createTrackbar("R min", VENTANA_UMBRALES, config.R_MIN, 255, nada)
    cv2.createTrackbar("G min", VENTANA_UMBRALES, config.G_MIN, 255, nada)
    cv2.createTrackbar("B max", VENTANA_UMBRALES, config.B_MAX, 255, nada)
    cv2.createTrackbar("|R-G| max", VENTANA_UMBRALES, config.DIF_RG_MAX, 255, nada)
    cv2.createTrackbar("Area min x100", VENTANA_UMBRALES, config.AREA_MINIMA // 100, 200, nada)


def leer_barras(detector):
    """Copia la posición de las barras en el detector, así los cambios se ven en el siguiente cuadro."""
    detector.r_min = cv2.getTrackbarPos("R min", VENTANA_UMBRALES)
    detector.g_min = cv2.getTrackbarPos("G min", VENTANA_UMBRALES)
    detector.b_max = cv2.getTrackbarPos("B max", VENTANA_UMBRALES)
    detector.dif_rg_max = cv2.getTrackbarPos("|R-G| max", VENTANA_UMBRALES)
    detector.area_minima = cv2.getTrackbarPos("Area min x100", VENTANA_UMBRALES) * 100


def dibujar(imagen, posiciones, regiones):
    """
    Dibuja sobre la imagen la línea que separa a los jugadores y, para cada uno, el rectángulo y el
    centroide del guante, una línea en su Y suavizada y el valor de Y (0 arriba, 1 abajo).
    """
    alto, ancho = imagen.shape[:2]
    mitad = ancho // 2
    cv2.line(imagen, (mitad, 0), (mitad, alto), (255, 255, 255), 1)

    for jugador, (y_norm, region, color) in enumerate(zip(posiciones, regiones, (COLOR_J1, COLOR_J2))):
        x0 = 0 if jugador == 0 else mitad
        x1 = mitad if jugador == 0 else ancho

        if region is not None:
            cx, cy, area, (x, y, w, h) = region
            cv2.rectangle(imagen, (x, y), (x + w, y + h), color, 2)
            cv2.circle(imagen, (int(cx), int(cy)), 6, color, -1)

        if y_norm is not None:
            y_px = int(y_norm * alto)
            cv2.line(imagen, (x0, y_px), (x1, y_px), color, 2)  # posición Y suavizada
            texto = f"J{jugador + 1}  Y = {y_norm:.2f}"
        else:
            texto = f"J{jugador + 1}  sin guante"
        if region is None and y_norm is not None:
            texto += " (perdido)"
        cv2.putText(imagen, texto, (x0 + 10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    if ultimo_clic is not None:
        x, y, (r, g, b) = ultimo_clic
        cv2.drawMarker(imagen, (x, y), (255, 255, 255), cv2.MARKER_CROSS, 14, 2)
        cv2.putText(imagen, f"R={r} G={g} B={b}", (10, alto - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 2)

    texto, hasta = aviso
    if time.time() < hasta:
        cv2.putText(imagen, texto, (mitad + 10, alto - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


def guardar(detector):
    """Guarda los umbrales actuales del detector en calibracion.json (tecla G)."""
    global aviso
    valores = {"R_MIN": detector.r_min, "G_MIN": detector.g_min, "B_MAX": detector.b_max,
               "DIF_RG_MAX": detector.dif_rg_max, "AREA_MINIMA": detector.area_minima}
    config.guardar_calibracion(valores)
    print(f"Calibracion guardada en {config.ARCHIVO_CALIBRACION}: {valores}")
    aviso = ("Calibracion guardada", time.time() + 2)


def main():
    """Abre la cámara y repite: leer cuadro, detectar, dibujar y mostrar, hasta pulsar Q o Esc."""
    indice = int(sys.argv[1]) if len(sys.argv) > 1 else config.CAMARA
    camara = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
    camara.set(cv2.CAP_PROP_FRAME_WIDTH, config.ANCHO)
    camara.set(cv2.CAP_PROP_FRAME_HEIGHT, config.ALTO)
    if not camara.isOpened():
        print(f"No se pudo abrir la cámara {indice}")
        return

    if config.CALIBRACION_CARGADA:
        print(f"Usando la calibracion guardada en {config.ARCHIVO_CALIBRACION}")
    else:
        print("Sin calibracion guardada, usando los valores por defecto de config.py (pulsa G para guardar)")

    detector = DetectorGuantes()
    imagen = {"actual": None}
    cv2.namedWindow(VENTANA_CAMARA)
    cv2.setMouseCallback(VENTANA_CAMARA, al_hacer_clic, imagen)
    crear_barras()

    while True:
        ok, cuadro = camara.read()
        if not ok:
            print("No se pudo leer la cámara")
            break
        if config.ESPEJO:
            cuadro = cv2.flip(cuadro, 1)
        imagen["actual"] = cuadro.copy()

        leer_barras(detector)
        posiciones, regiones, mascara = detector.procesar(cuadro)

        dibujar(cuadro, posiciones, regiones)
        cv2.imshow(VENTANA_CAMARA, cuadro)
        cv2.imshow(VENTANA_MASCARA, mascara)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla in (ord("q"), 27):
            break
        if tecla == ord("g"):
            guardar(detector)

    camara.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

"""
Parámetros del detector de guantes amarillos (los usan deteccion.py, prueba_camara.py y bridge.py).

Los valores de abajo son los de por defecto. Los umbrales se ajustan en vivo con prueba_camara.py
y al pulsar G se guardan en calibracion.json; ese archivo se carga al final de este módulo y
reemplaza los valores por defecto, así cada escena (luz, fondo) puede tener su propia calibración.
Para volver a los valores por defecto basta con borrar calibracion.json.
"""
import json
import os

# ---------------- cámara ----------------

CAMARA = 0          # índice de la cámara: 0 es la primera; prueba 1, 2... si hay varias
ANCHO = 640         # resolución pedida a la cámara (la cámara puede entregar otra)
ALTO = 480
ESPEJO = True       # voltear la imagen horizontalmente: al mover la mano a la derecha, en la
                    # imagen también se mueve a la derecha (como un espejo)

# ---------------- 1. filtro ----------------

# Tamaño (impar) del desenfoque gaussiano que reduce el ruido de la cámara.
# Más grande = menos ruido, pero bordes más borrosos.
KERNEL_DESENFOQUE = 5

# ---------------- 2. umbralización RGB ----------------
# Un píxel es amarillo si cumple las cuatro reglas: R alto, G alto, B bajo y R parecido a G.
# Con valores 0 o 255 una regla queda desactivada (por ejemplo R_MIN = 0 acepta cualquier rojo).

R_MIN = 150         # rojo mínimo
G_MIN = 150         # verde mínimo
B_MAX = 110         # azul máximo (descarta blancos y grises claros)
DIF_RG_MAX = 70     # diferencia máxima entre R y G (descarta naranjas y verdes)

# ---------------- 3. morfología ----------------

# Tamaño del elemento estructurante de la apertura (quita puntos sueltos) y el cierre (rellena
# huecos del guante). Más grande = máscara más limpia, pero se pierden detalles pequeños.
KERNEL_MORFOLOGIA = 7

# ---------------- 4. segmentación ----------------

# Área mínima (en píxeles) para aceptar una región como guante. Evita que objetos amarillos
# pequeños del fondo se tomen como un guante. Depende de la distancia a la cámara.
AREA_MINIMA = 1500

# ---------------- 5. posición ----------------

# Suavizado exponencial de la Y entre cuadros, de 0 a 1:
# cerca de 1 = responde rápido pero tiembla; cerca de 0 = muy suave pero con retraso.
SUAVIZADO = 0.5


# ---------------- calibración guardada ----------------

ARCHIVO_CALIBRACION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibracion.json")

# parámetros que se guardan en el archivo de calibración
CALIBRABLES = ("R_MIN", "G_MIN", "B_MAX", "DIF_RG_MAX", "AREA_MINIMA")


def guardar_calibracion(valores):
    """Guarda los valores en calibracion.json y los aplica como nuevos globales de este módulo."""
    valores = {k: int(valores[k]) for k in CALIBRABLES}
    with open(ARCHIVO_CALIBRACION, "w", encoding="utf-8") as archivo:
        json.dump(valores, archivo, indent=4)
    globals().update(valores)


def cargar_calibracion():
    """Reemplaza los valores por defecto con los de calibracion.json, si existe."""
    try:
        with open(ARCHIVO_CALIBRACION, encoding="utf-8") as archivo:
            valores = json.load(archivo)
    except FileNotFoundError:
        return False
    globals().update({k: int(v) for k, v in valores.items() if k in CALIBRABLES})
    return True


CALIBRACION_CARGADA = cargar_calibracion()

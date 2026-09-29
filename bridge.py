"""
Bridge entre la visión por computador (carpeta PDI) y el juego (carpeta game).

Es el único archivo que conoce las dos partes: el juego no importa nada de PDI y PDI no sabe
nada del juego. El bridge:

    1. Abre la cámara y la lee en un hilo aparte. La cámara entrega ~15-30 cuadros por segundo y
       cada lectura bloquea hasta que llega un cuadro; si se leyera dentro del juego (60 fps) el
       juego se trabaría. Con el hilo, el juego solo consulta el último resultado disponible.
    2. Pasa cada cuadro por el detector de guantes amarillos (PDI/deteccion.py).
    3. Convierte la Y del guante en la cámara a la Y de la paleta en el campo.
    4. Prepara una vista previa pequeña de la cámara, dividida en jugador 1 y jugador 2,
       para que el juego la dibuje.

Lo que usa el juego (ver game/air_hockey.py):
    posiciones()   -> [y_jugador1, y_jugador2], de 0.0 (arriba) a 1.0 (abajo) o None si no se ve
    vista_previa() -> [imagen_jugador1, imagen_jugador2] en RGB, o None si aún no hay imagen

Reparto de la cámara (la imagen se voltea como un espejo, ver PDI/config.py ESPEJO):
    mitad izquierda -> jugador 1 (paleta roja, portería izquierda)
    mitad derecha   -> jugador 2 (paleta azul, portería derecha)
"""
import threading

import cv2

from PDI import config
from PDI.deteccion import DetectorGuantes

# Franja vertical de la cámara (de 0 a 1) que corresponde a todo el alto del campo.
# Con (0.15, 0.85) basta mover la mano entre el 15 % y el 85 % de la altura de la imagen para
# recorrer el campo completo, sin tener que llegar a los bordes de la cámara.
RANGO_Y = (0.15, 0.85)

# Tamaño de la vista previa respecto a la imagen de la cámara (0.25 = una cuarta parte).
ESCALA_VISTA = 0.25

# Colores de cada jugador en la vista previa (OpenCV usa el orden B, G, R).
COLOR_J1 = (92, 92, 255)     # rojo, como la paleta del jugador 1
COLOR_J2 = (219, 189, 100)   # azul, como la paleta del jugador 2
COLOR_RANGO = (200, 200, 200)


class PuenteCamara:
    """Conecta la cámara y el detector de guantes con el juego."""

    def __init__(self, camara=config.CAMARA, rango_y=RANGO_Y):
        self.camara = camara
        self.rango_y = rango_y
        self.detector = DetectorGuantes()

        # resultados compartidos entre el hilo de la cámara y el juego,
        # protegidos con un candado para que no se lean a medio escribir
        self._posiciones = [None, None]
        self._vistas = None
        self._candado = threading.Lock()

        self._activo = False
        self._hilo = None
        self._captura = None

    # ---------------------------------------------------------------- ciclo de vida

    def iniciar(self):
        """Abre la cámara y empieza a detectar en segundo plano. Devuelve False si no hay cámara."""
        # CAP_DSHOW (DirectShow) abre la cámara mucho más rápido en Windows
        self._captura = cv2.VideoCapture(self.camara, cv2.CAP_DSHOW)
        self._captura.set(cv2.CAP_PROP_FRAME_WIDTH, config.ANCHO)
        self._captura.set(cv2.CAP_PROP_FRAME_HEIGHT, config.ALTO)
        if not self._captura.isOpened():
            print(f"[bridge] No se pudo abrir la camara {self.camara}, se juega solo con teclado")
            return False

        estado = "guardada" if config.CALIBRACION_CARGADA else "por defecto"
        print(f"[bridge] Camara {self.camara} abierta, calibracion {estado}")
        self._activo = True
        # daemon=True: si el juego termina, el hilo no impide que el programa se cierre
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()
        return True

    def detener(self):
        """Detiene el hilo y libera la cámara para que otros programas puedan usarla."""
        self._activo = False
        if self._hilo is not None:
            self._hilo.join(timeout=1)
        if self._captura is not None:
            self._captura.release()

    # ---------------------------------------------------------------- hilo de la cámara

    def _bucle(self):
        """Se ejecuta en el hilo: lee la cámara, detecta los guantes y guarda el resultado."""
        while self._activo:
            ok, cuadro = self._captura.read()
            if not ok:
                continue
            if config.ESPEJO:
                cuadro = cv2.flip(cuadro, 1)

            # posiciones: Y suavizada de cada jugador (0 a 1 en la cámara)
            # regiones:   guante encontrado en ESTE cuadro, o None si no se vio
            posiciones, regiones, _ = self.detector.procesar(cuadro)

            # solo se entrega la posición si el guante se ve en este cuadro; si no, se entrega None
            # y el juego deja a ese jugador con el teclado
            actuales = [self._a_campo(y) if region is not None else None
                        for y, region in zip(posiciones, regiones)]
            vistas = self._crear_vistas(cuadro, posiciones, regiones)

            with self._candado:
                self._posiciones = actuales
                self._vistas = vistas

    def _a_campo(self, y):
        """
        Convierte la Y de la cámara a la Y del campo (ambas de 0 a 1).
        La franja RANGO_Y se estira a todo el campo; lo que queda fuera se recorta a 0 o 1.
        Ejemplo con RANGO_Y = (0.15, 0.85): cámara 0.15 -> campo 0.0, 0.50 -> 0.5, 0.85 -> 1.0
        """
        y_min, y_max = self.rango_y
        return min(max((y - y_min) / (y_max - y_min), 0.0), 1.0)

    def _crear_vistas(self, cuadro, posiciones, regiones):
        """
        Dibuja la detección sobre el cuadro, lo divide en dos mitades (jugador 1 y jugador 2)
        y las reduce a ESCALA_VISTA. Devuelve las dos mitades en RGB, que es lo que usa pygame.
        """
        imagen = cuadro.copy()
        alto, ancho = imagen.shape[:2]
        mitad = ancho // 2

        # franja útil de la cámara (RANGO_Y): por fuera de estas líneas la paleta ya está en el borde
        for y in self.rango_y:
            cv2.line(imagen, (0, int(y * alto)), (ancho, int(y * alto)), COLOR_RANGO, 2)

        for y_norm, region, color, (x0, x1) in zip(posiciones, regiones, (COLOR_J1, COLOR_J2),
                                                    ((0, mitad), (mitad, ancho))):
            if region is not None:
                _, _, _, (x, y, w, h) = region
                cv2.rectangle(imagen, (x, y), (x + w, y + h), color, 4)
            if y_norm is not None:
                cv2.line(imagen, (x0, int(y_norm * alto)), (x1, int(y_norm * alto)), color, 4)

        vistas = []
        for x0, x1 in ((0, mitad), (mitad, ancho)):
            mitad_img = cv2.resize(imagen[:, x0:x1], None, fx=ESCALA_VISTA, fy=ESCALA_VISTA,
                                   interpolation=cv2.INTER_AREA)
            vistas.append(cv2.cvtColor(mitad_img, cv2.COLOR_BGR2RGB))
        return vistas

    # ---------------------------------------------------------------- lo que consulta el juego

    def posiciones(self):
        """[y_jugador1, y_jugador2] de 0.0 (arriba) a 1.0 (abajo), None si no se ve ese guante."""
        with self._candado:
            return list(self._posiciones)

    def vista_previa(self):
        """[imagen_jugador1, imagen_jugador2] en RGB (arreglos de numpy), o None si aún no hay."""
        with self._candado:
            return None if self._vistas is None else list(self._vistas)

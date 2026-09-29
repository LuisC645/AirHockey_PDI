# Air Hockey con guantes amarillos

Juego de Air Hockey para dos jugadores que se controla moviendo la mano frente a la cámara con un
**guante amarillo**. La detección se hace solo con **procesamiento digital de imágenes clásico**
(filtros, umbralización RGB, morfología y segmentación), sin inteligencia artificial.

## Juego base

El juego está basado en **[mkfeuhrer/Air-hockey](https://github.com/mkfeuhrer/Air-hockey)**.

Cambios respecto al original:

- Portado de Python 2 a Python 3 y organizado como paquete (`game/`).
- Sin menú de inicio: el partido empieza directamente con una cuenta regresiva de 3 segundos y el
  disco sale desde el centro en línea recta hacia un lado al azar.
- Siempre dos jugadores, con colores fijos (rojo y azul) y una sola velocidad.
- Las paletas están fijas en X, cerca de su portería, y solo se mueven en Y.
- Fuente JetBrains Mono, márgenes uniformes y paneles legibles en la pausa y entre rondas.
- Se quitaron el menú, la selección de colores y de tema, los nombres editables, la ayuda y el
  botón de silencio.
- Control por cámara con guantes amarillos (`PDI/` + `bridge.py`) y una vista previa pequeña de la
  cámara, dividida por jugador, dentro del juego.

## Requisitos

- Python 3
- Una cámara web
- Librerías:

```
pip install pygame-ce opencv-python numpy
```

OpenCV solo se usa para leer la cámara y para operaciones clásicas de imagen (desenfoque,
morfología y componentes conectados).

## Uso

Todos los comandos se ejecutan desde esta carpeta.

### 1. Calibrar los guantes

```
python PDI/prueba_camara.py
```

Ajusta las barras de la ventana **PDI - Umbrales** hasta que en **PDI - Mascara** solo se vea el
guante en blanco. Al hacer clic sobre el guante en la ventana de la cámara se muestran sus valores
R, G, B. Pulsa **G** para guardar la calibración en `PDI/calibracion.json` y **Q** o **Esc** para
salir. Si cambian la luz o el lugar, basta con volver a calibrar.

Si hay varias cámaras se puede elegir una: `python PDI/prueba_camara.py 1`.

### 2. Jugar

```
python main.py
```

| Jugador | Paleta | Guante | Teclado (si no se ve el guante) |
|---|---|---|---|
| 1 | Roja, portería izquierda | Mitad izquierda de la cámara | W / S |
| 2 | Azul, portería derecha | Mitad derecha de la cámara | ↑ / ↓ |

- **Espacio** o el botón de pausa: pausar, continuar o reiniciar.
- En las esquinas inferiores se ve la cámara de cada jugador, con su guante marcado y la franja
  útil de movimiento (líneas grises).
- Si no hay cámara, el juego funciona solo con teclado.

## Cómo funciona la detección

Cada cuadro de la cámara pasa por esta cadena (`PDI/deteccion.py`), por separado en la mitad
izquierda (jugador 1) y la derecha (jugador 2):

1. **Filtro**: desenfoque gaussiano para reducir el ruido de la cámara.
2. **Umbralización RGB**: un píxel es amarillo si `R ≥ R_MIN`, `G ≥ G_MIN`, `B ≤ B_MAX` y
   `|R − G| ≤ DIF_RG_MAX`. El resultado es una máscara binaria.
3. **Morfología**: una apertura quita los puntos sueltos y un cierre rellena los huecos del guante.
4. **Segmentación**: componentes conectados; se toma la región más grande que supere un área mínima.
5. **Posición**: la Y del centroide, suavizada entre cuadros con un filtro exponencial.

`bridge.py` lee la cámara en un hilo aparte, pasa cada cuadro por el detector y convierte la Y del
guante en la Y de la paleta.

## Estructura

```
AirHockey/
├── main.py            Punto de entrada: crea el bridge y arranca el juego
├── bridge.py          Une la cámara y la detección con el juego
├── PDI/               Visión por computador
│   ├── config.py          Parámetros (cámara, umbrales, filtros) y carga de la calibración
│   ├── deteccion.py       Cadena de procesamiento de imágenes
│   ├── prueba_camara.py   Herramienta de calibración
│   └── calibracion.json   Calibración guardada (se crea al pulsar G)
└── game/              Juego (pygame)
    ├── air_hockey.py      Bucle del juego, cuenta regresiva, pausa y rondas
    ├── paddle.py, puck.py Paletas y disco
    ├── endScreen.py, ui.py Pantalla del ganador y elementos de interfaz
    ├── constants.py       Tamaños, colores, velocidades y reglas
    ├── globals.py         Recursos compartidos (imágenes, fuentes)
    └── assets/            Imágenes, sonidos y fuentes
```

## Ajustes útiles

| Qué | Dónde |
|---|---|
| Umbrales del color amarillo | `PDI/prueba_camara.py` (se guardan en `PDI/calibracion.json`) |
| Cámara a usar, suavizado, tamaños de filtro | `PDI/config.py` |
| Franja de la cámara que recorre todo el campo | `RANGO_Y` en `bridge.py` |
| Tamaño de la vista previa de la cámara | `ESCALA_VISTA` en `bridge.py` |
| Velocidad máxima de la paleta al seguir el guante | `CAMERA_PADDLE_SPEED` en `game/constants.py` |
| Distancia de las paletas a su portería | `PADDLE_GOAL_DISTANCE` en `game/constants.py` |
| Fondo del campo | Guardar una imagen como `game/assets/field.png` (1200 × 600) |

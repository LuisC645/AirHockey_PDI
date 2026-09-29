# PDI + Bridge: guía completa para la sustentación

Este documento explica **solo la parte de Procesamiento Digital de Imágenes (carpeta `PDI/`) y el
puente con el juego (`bridge.py`)**. El código del juego (pygame, física del disco, marcador) se
omite: para esta parte el juego es una "caja negra" que recibe dos números entre 0 y 1.

---

## Índice

1. [Qué problema resolvemos](#1-qué-problema-resolvemos)
2. [Visión general del sistema](#2-visión-general-del-sistema)
3. [Archivos y responsabilidades](#3-archivos-y-responsabilidades)
4. [Conceptos base: imagen digital, canales, BGR](#4-conceptos-base-imagen-digital-canales-bgr)
5. [Adquisición: cámara y efecto espejo](#5-adquisición-cámara-y-efecto-espejo)
6. [Paso 1 — Filtro: desenfoque gaussiano](#6-paso-1--filtro-desenfoque-gaussiano)
7. [Paso 2 — Umbralización RGB (segmentación por color)](#7-paso-2--umbralización-rgb-segmentación-por-color)
8. [Paso 3 — Morfología: apertura y cierre](#8-paso-3--morfología-apertura-y-cierre)
9. [Paso 4 — Segmentación: componentes conectados](#9-paso-4--segmentación-componentes-conectados)
10. [Paso 5 — Posición: centroide y normalización](#10-paso-5--posición-centroide-y-normalización)
11. [Suavizado temporal: filtro exponencial](#11-suavizado-temporal-filtro-exponencial)
12. [División en dos jugadores](#12-división-en-dos-jugadores)
13. [Calibración: prueba_camara.py y calibracion.json](#13-calibración-prueba_camarapy-y-calibracionjson)
14. [El bridge (bridge.py)](#14-el-bridge-bridgepy)
15. [Tabla resumen de parámetros y por qué esos valores](#15-tabla-resumen-de-parámetros-y-por-qué-esos-valores)
16. [Rendimiento](#16-rendimiento)
17. [Limitaciones y mejoras posibles](#17-limitaciones-y-mejoras-posibles)
18. [Guion sugerido para la sustentación](#18-guion-sugerido-para-la-sustentación)
19. [Preguntas probables del jurado (con respuesta)](#19-preguntas-probables-del-jurado-con-respuesta)
20. [Glosario rápido](#20-glosario-rápido)

---

## 1. Qué problema resolvemos

Queremos controlar las paletas de un Air Hockey **moviendo la mano frente a una cámara web**, con un
**guante amarillo**. Dos jugadores comparten la misma cámara: uno en la mitad izquierda de la imagen
y otro en la derecha. De cada guante solo necesitamos **su altura (Y)**, porque las paletas solo se
mueven verticalmente.

Restricción clave del proyecto: **nada de inteligencia artificial** (ni redes neuronales, ni
MediaPipe, ni modelos entrenados). Todo se hace con **técnicas clásicas de PDI**:

| Técnica | Para qué sirve aquí |
|---|---|
| Filtro gaussiano | Quitar el ruido de la cámara |
| Umbralización por color (RGB) | Decidir qué píxeles son "amarillo guante" |
| Morfología (apertura + cierre) | Limpiar la máscara binaria |
| Componentes conectados | Separar la máscara en objetos y elegir el guante |
| Centroide (momentos) | Obtener la posición del guante |
| Filtro exponencial temporal | Evitar que la paleta tiemble |

**¿Por qué un guante amarillo?** El amarillo saturado es un color **poco frecuente** en un salón
(paredes, piel, ropa, muebles), y en RGB tiene una firma muy clara: **R alto, G alto, B bajo**. Eso
permite segmentarlo con reglas simples, sin aprendizaje.

---

## 2. Visión general del sistema

```
 ┌─────────┐   cuadro BGR    ┌──────────────────── PDI/deteccion.py ─────────────────────┐
 │ Cámara  │ ─────────────▶ │ 1. Filtro      2. Umbral RGB   3. Morfología               │
 │ 640x480 │  (hilo aparte)  │ GaussianBlur ─▶ máscara 0/255 ─▶ apertura + cierre         │
 └─────────┘                 │                                        │                   │
                             │              ┌─────────────────────────┴──────────┐        │
                             │              ▼ mitad izquierda                    ▼ derecha│
                             │ 4. Componentes conectados → región más grande (≥ área mín.)│
                             │ 5. Centroide → Y / alto → suavizado exponencial            │
                             └──────────────────────────────┬─────────────────────────────┘
                                                            │ [y_j1, y_j2] en 0..1 (cámara)
                                                  ┌─────────▼──────────┐
                                                  │     bridge.py      │
                                                  │ RANGO_Y → 0..1     │
                                                  │ (campo) + vista    │
                                                  │ previa + candado   │
                                                  └─────────┬──────────┘
                                                            │ posiciones(), vista_previa()
                                                  ┌─────────▼──────────┐
                                                  │   Juego (pygame)   │
                                                  └────────────────────┘
```

Idea de diseño importante: **separación de responsabilidades**.

- `PDI/` no sabe nada del juego: recibe una imagen y devuelve posiciones. Se puede probar sola
  (`prueba_camara.py`).
- El juego no sabe nada de visión: solo pide `posiciones()` y `vista_previa()`.
- `bridge.py` es el **único** archivo que conoce ambas partes.

---

## 3. Archivos y responsabilidades

| Archivo | Qué hace |
|---|---|
| `PDI/config.py` | Todos los parámetros (cámara, tamaños de kernel, umbrales, área, suavizado) y la carga/guardado de `calibracion.json`. |
| `PDI/deteccion.py` | La cadena de PDI: `filtrar`, `umbral_amarillo`, `limpiar`, `region_mas_grande`, la clase `Suavizado` y la clase `DetectorGuantes` que lo une todo. |
| `PDI/prueba_camara.py` | Herramienta de calibración con barras deslizantes, máscara en vivo y lectura del color de un píxel con clic. |
| `PDI/calibracion.json` | Umbrales guardados para la escena actual (luz, fondo). Se crea al pulsar **G**. |
| `bridge.py` | Abre la cámara en un hilo, llama al detector, convierte la Y de cámara a Y de campo, arma la vista previa y la entrega al juego de forma segura (candado). |
| `main.py` | Crea el bridge, lo inicia, corre el juego y al final libera la cámara. |

---

## 4. Conceptos base: imagen digital, canales, BGR

- Una **imagen digital en color** es una matriz de `alto × ancho × 3`. Cada píxel tiene tres
  valores enteros de **0 a 255** (tipo `uint8`), uno por canal.
- Con 640 × 480 hay **307 200 píxeles** y **921 600 valores** por cuadro.
- **OpenCV guarda los canales en orden B, G, R** (no R, G, B). Por eso en `umbral_amarillo`:

  ```python
  b = imagen_bgr[:, :, 0]   # canal 0 = azul
  g = imagen_bgr[:, :, 1]   # canal 1 = verde
  r = imagen_bgr[:, :, 2]   # canal 2 = rojo
  ```

  y por eso el bridge convierte a RGB (`cv2.COLOR_BGR2RGB`) antes de pasarle la vista previa a
  pygame, que sí usa RGB.

- **Modelo RGB aditivo**: el amarillo es la suma de rojo y verde. Amarillo puro = `(R=255, G=255, B=0)`.
  El blanco es `(255, 255, 255)`: también tiene R y G altos, **la diferencia con el amarillo está en el azul**.
- **Máscara binaria**: imagen de un solo canal donde cada píxel vale 0 (negro, "no es") o 255
  (blanco, "sí es"). Es el resultado de la umbralización y la entrada de la morfología y la segmentación.

---

## 5. Adquisición: cámara y efecto espejo

Código: `bridge.py` (`iniciar`, `_bucle`) y `prueba_camara.py` (`main`).

```python
captura = cv2.VideoCapture(camara, cv2.CAP_DSHOW)
captura.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
captura.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
...
cuadro = cv2.flip(cuadro, 1)   # si ESPEJO = True
```

| Decisión | Por qué |
|---|---|
| `CAP_DSHOW` (DirectShow) | En Windows abre la cámara mucho más rápido que el backend por defecto (MSMF). |
| 640 × 480 | Resolución estándar soportada por casi todas las webcams. Suficiente para ver un guante; más resolución solo haría el procesamiento más lento sin ganar precisión útil (la paleta no necesita precisión de 1 píxel). La cámara puede entregar otra resolución: el código siempre lee `shape` y no asume el tamaño. |
| `flip(cuadro, 1)` — espejo horizontal | La cámara ve al jugador "de frente": sin voltear, si el jugador mueve la mano a su derecha, en la imagen se mueve a la izquierda. Con el espejo la imagen se comporta como un espejo de baño, que es lo intuitivo. Además garantiza que **el jugador que está a la izquierda quede en la mitad izquierda** de la imagen (jugador 1). El `1` significa "voltear respecto al eje vertical". |

---

## 6. Paso 1 — Filtro: desenfoque gaussiano

Código: `deteccion.py → filtrar()`; parámetro `KERNEL_DESENFOQUE = 5`.

```python
cv2.GaussianBlur(imagen, (5, 5), 0)
```

### Qué problema resuelve

El sensor de una webcam tiene **ruido**: aunque la escena esté quieta, cada píxel cambia unos
cuantos niveles de color de un cuadro a otro (ruido térmico, compresión, poca luz). Si umbralizamos
directamente, los píxeles del borde del guante "parpadean" entre amarillo y no amarillo, y aparecen
puntos sueltos en el fondo.

### Cómo funciona (convolución)

Es un **filtro pasa-bajos lineal**: cada píxel se reemplaza por un **promedio ponderado** de su
vecindad de 5 × 5, donde los vecinos más cercanos pesan más (pesos de una campana de Gauss). Se
aplica a cada canal (B, G, R) por separado.

Con `sigma = 0`, OpenCV calcula sigma a partir del tamaño:
`σ = 0.3·((k − 1)·0.5 − 1) + 0.8 = 0.3·(2 − 1) + 0.8 = 1.1 px`.
Para kernels pequeños (≤ 7) y sigma automático, OpenCV usa el kernel binomial exacto
**[1 4 6 4 1] / 16**, que es la aproximación discreta de una gaussiana.

**Kernel 1D real (calculado con `cv2.getGaussianKernel(5, 0)`):**

```
[0.0625  0.25  0.375  0.25  0.0625]   =   [1  4  6  4  1] / 16
```

**Kernel 2D = producto exterior del 1D consigo mismo (÷ 256):**

```
 1   4   6   4   1                 0.0039 0.0156 0.0234 0.0156 0.0039
 4  16  24  16   4                 0.0156 0.0625 0.0938 0.0625 0.0156
 6  24  36  24   6   ×  1/256  =   0.0234 0.0938 0.1406 0.0938 0.0234
 4  16  24  16   4                 0.0156 0.0625 0.0938 0.0625 0.0156
 1   4   6   4   1                 0.0039 0.0156 0.0234 0.0156 0.0039
```

Propiedades para mencionar:

- **Los pesos suman 1** → la imagen no se aclara ni se oscurece, solo se suaviza.
- **Es separable** → en lugar de 25 multiplicaciones por píxel se hacen 5 horizontales + 5
  verticales = 10. Por eso es muy rápido.
- **Es isotrópico** (igual en todas las direcciones) y no introduce artefactos como el filtro de
  caja (promedio simple), cuyos bordes abruptos generan "anillos" en frecuencia.

### Ejemplo numérico

Un píxel de ruido aislado con valor 255 rodeado de ceros: tras el filtro, el centro queda en
`255 × 0.1406 ≈ 36`. Ya no supera ningún umbral → **el ruido desaparece antes de umbralizar**.
En cambio, dentro del guante todos los vecinos son amarillos, así que el promedio sigue siendo
amarillo: el guante no se pierde.

### ¿Por qué 5 y no otro valor?

| Kernel | Efecto |
|---|---|
| 1 | Sin filtro: la máscara parpadea y tiene mucho ruido de sal. |
| 3 | Quita algo de ruido, pero en poca luz sigue habiendo parpadeo. |
| **5** | **Buen equilibrio**: elimina el ruido de píxel individual y conserva la forma del guante (que mide decenas o cientos de píxeles). |
| 9, 15… | Más suave, pero el borde del guante se mezcla con el fondo: los colores del borde se "lavan" y el guante parece más pequeño; además es más lento. |

- **Debe ser impar** para que exista un píxel central (el kernel queda simétrico alrededor del
  píxel que se está calculando).
- El guante es un objeto **grande** frente a la escala del ruido (1-2 px), así que un kernel de
  5 px no afecta su detección.

---

## 7. Paso 2 — Umbralización RGB (segmentación por color)

Código: `deteccion.py → umbral_amarillo()`.

```python
amarillo = (r >= r_min) & (g >= g_min) & (b <= b_max) & (np.abs(r - g) <= dif_rg_max)
mascara  = amarillo.astype(np.uint8) * 255
```

### Idea

Se decide **píxel por píxel** si es amarillo con **cuatro reglas** que se deben cumplir **a la vez**
(operador `&`, un Y lógico):

| Regla | Valor por defecto | Qué significa | Qué descarta |
|---|---|---|---|
| `R ≥ R_MIN` | 150 | Tiene bastante rojo | Verdes, azules, oscuros |
| `G ≥ G_MIN` | 150 | Tiene bastante verde | Rojos, naranjas, oscuros, piel en sombra |
| `B ≤ B_MAX` | 110 | Tiene **poco azul** | **Blanco y grises claros** (tienen R, G y B altos), azules |
| `|R − G| ≤ DIF_RG_MAX` | 70 | Rojo y verde **equilibrados** | **Naranja** (R ≫ G) y **verde lima** (G ≫ R) |

Interpretación geométrica: cada regla es un **semiespacio** en el cubo RGB (0-255 en cada eje). La
región aceptada es la **intersección** de los cuatro semiespacios: un poliedro alrededor de la
esquina amarilla del cubo `(255, 255, 0)`.

Relación con HSV (útil si el jurado pregunta):

- `|R − G| ≤ …` controla el **tono** (hue): si R y G son parecidos y B es bajo, el tono está cerca
  de 60° (amarillo).
- `B ≤ …` junto con `R, G ≥ …` controla la **saturación**: mucho R y G pero poco B = color intenso,
  no blanquecino.
- `R, G ≥ …` controla el **brillo** (value): descarta amarillos muy oscuros / sombras.

Es decir, las reglas RGB imitan una umbralización HSV, pero se leen directamente con los valores
que la herramienta de calibración muestra al hacer clic (R, G, B), lo que hace la calibración muy
intuitiva.

### Ejemplos (con los valores por defecto 150 / 150 / 110 / 70)

| Píxel | R | G | B | \|R−G\| | ¿Amarillo? | Regla que falla |
|---|---|---|---|---|---|---|
| Guante iluminado | 220 | 205 | 60 | 15 | **Sí** | — |
| Guante en sombra suave | 170 | 160 | 50 | 10 | **Sí** | — |
| Pared blanca | 240 | 240 | 235 | 0 | No | B > 110 |
| Naranja | 240 | 140 | 30 | 100 | No | G < 150 y \|R−G\| > 70 |
| Verde lima | 150 | 230 | 40 | 80 | No | \|R−G\| > 70 |
| Piel | 200 | 150 | 120 | 50 | No | B > 110 |
| Camiseta roja | 200 | 40 | 40 | 160 | No | G < 150 y \|R−G\| |

### Detalle técnico importante: `int16`

```python
b = imagen_bgr[:, :, 0].astype(np.int16)
```

Las imágenes son `uint8` (0 a 255, sin signo). En `uint8`, `10 − 20` **no da −10, da 246**
(desbordamiento, aritmética módulo 256). Entonces `|R − G|` sería falso para muchos píxeles. Al
convertir a `int16` (−32 768 a 32 767) la resta es correcta.

### Detalle técnico: vectorización con NumPy

No hay ningún `for` sobre píxeles: cada comparación (`r >= r_min`) produce **de una vez** una matriz
booleana de 480 × 640, y `&` combina las matrices elemento a elemento. NumPy lo ejecuta en C, por eso
se procesan ~300 000 píxeles en milisegundos. Un doble `for` en Python tardaría segundos por cuadro.

### ¿Por qué "Y" (`&`) y no "O"?

Cada regla por sí sola deja pasar colores que no son amarillos (el blanco pasa `R ≥ 150` y `G ≥ 150`).
Solo la **combinación** define el amarillo. Con `0` o `255` una regla queda desactivada (p. ej.
`R_MIN = 0` acepta cualquier rojo).

### La calibración actual guardada

`PDI/calibracion.json` contiene hoy:

```json
{ "R_MIN": 0, "G_MIN": 173, "B_MAX": 167, "DIF_RG_MAX": 48, "AREA_MINIMA": 1000 }
```

Lectura para la sustentación:

- `R_MIN = 0` **parece** desactivar la regla del rojo, pero no la anula en la práctica: si
  `G ≥ 173` y `|R − G| ≤ 48`, entonces **R ≥ 125** automáticamente. Las reglas se refuerzan entre sí.
- `G_MIN = 173` es más exigente que el valor por defecto: pide un guante bien iluminado y descarta
  la piel (G de la piel suele estar por debajo).
- `B_MAX = 167` es más permisivo: con la luz de esa escena (probablemente luz blanca/fría) el guante
  tenía más azul del esperado. El blanco puro (B ≈ 240) sigue sin pasar, pero **cuidado**: un gris
  claro amarillento con B ≤ 167 sí podría pasar. Por eso también existen el filtro de **área mínima**
  y la elección de **la región más grande**.
- `DIF_RG_MAX = 48` es más estricto que 70: se ajustó para no aceptar naranjas / tonos piel.

Mensaje clave: **los umbrales dependen de la iluminación**, por eso existe la herramienta de
calibración y el archivo por escena.

---

## 8. Paso 3 — Morfología: apertura y cierre

Código: `deteccion.py → limpiar()`; parámetro `KERNEL_MORFOLOGIA = 7`.

```python
elemento = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
mascara  = cv2.morphologyEx(mascara, cv2.MORPH_OPEN,  elemento)   # apertura
mascara  = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, elemento)   # cierre
```

### Problema

Tras umbralizar, la máscara tiene dos defectos:

1. **Falsos positivos pequeños**: puntos y manchitas blancas en el fondo (reflejos, ruido que
   sobrevivió al filtro, objetos con algún píxel amarillento).
2. **Falsos negativos dentro del guante**: huecos negros por sombras, arrugas de la tela, brillos
   especulares (que se ven blancos, con B alto) o los espacios entre dedos.

### Operaciones básicas (sobre imágenes binarias)

El **elemento estructurante** (EE) es una pequeña forma que se "pasea" por la imagen.

- **Erosión**: un píxel queda blanco solo si **todo** el EE centrado en él cae sobre blanco. Efecto:
  los objetos **adelgazan**; los que son más pequeños que el EE **desaparecen**. (Es un filtro de mínimo.)
- **Dilatación**: un píxel queda blanco si **algún** píxel del EE cae sobre blanco. Efecto: los
  objetos **engordan**; los huecos más pequeños que el EE **se rellenan**. (Es un filtro de máximo.)

### Operaciones compuestas usadas

| Operación | Definición | Efecto | Qué arregla aquí |
|---|---|---|---|
| **Apertura** (`MORPH_OPEN`) | Erosión → Dilatación | Elimina objetos/salientes más pequeños que el EE; lo que sobrevive recupera (aprox.) su tamaño | Borra el **ruido de sal** del fondo |
| **Cierre** (`MORPH_CLOSE`) | Dilatación → Erosión | Rellena huecos/grietas más pequeños que el EE; el contorno exterior recupera (aprox.) su tamaño | Rellena los **huecos del guante** y une partes separadas |

A diferencia de hacer solo una erosión o solo una dilatación, apertura y cierre **no cambian
significativamente el tamaño del objeto grande**, así que el centroide no se desplaza.

### ¿Por qué primero apertura y luego cierre?

Si se cerrara primero, los puntos de ruido cercanos entre sí **se fusionarían** en manchas más
grandes que la apertura ya no podría borrar. Se limpia primero el fondo (apertura) y luego se
consolida el guante (cierre).

### ¿Por qué elíptico?

Elemento estructurante real (`getStructuringElement(MORPH_ELLIPSE, (7, 7))`):

```
0 0 0 1 0 0 0
0 1 1 1 1 1 0
1 1 1 1 1 1 1
1 1 1 1 1 1 1
1 1 1 1 1 1 1
0 1 1 1 1 1 0
0 0 0 1 0 0 0
```

Es aproximadamente un **disco**: actúa igual en todas las direcciones, y la mano/guante es una forma
redondeada. Un EE cuadrado tendería a dejar esquinas "cuadradas" y a tratar distinto las diagonales.

### ¿Por qué 7?

- El ruido tras el filtro gaussiano son manchas de **pocos píxeles** → un EE de 7 × 7 las borra.
- Los huecos por arrugas o sombras son **de unos pocos píxeles** de ancho → el cierre los rellena.
- El guante mide **decenas a cientos de píxeles** → sobrevive intacto a la apertura.
- Es **mayor que el kernel del filtro (5)** porque actúa sobre un problema de mayor escala (manchas y
  huecos, no ruido de un píxel).

| Tamaño | Efecto |
|---|---|
| 3 | Deja pasar manchas medianas del fondo y no rellena bien los huecos. |
| **7** | Limpia bien y conserva el guante a distancias normales de juego. |
| 15+ | Máscara muy limpia pero borra el guante si el jugador está lejos (guante pequeño) y deforma el contorno; más costoso. |

---

## 9. Paso 4 — Segmentación: componentes conectados

Código: `deteccion.py → region_mas_grande()`; parámetro `AREA_MINIMA`.

```python
n, etiquetas, stats, centroides = cv2.connectedComponentsWithStats(mascara, connectivity=8)
i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))    # la región más grande (sin el fondo)
if stats[i, cv2.CC_STAT_AREA] < area_minima: return None
```

### Qué hace

La máscara es solo "blanco/negro"; todavía no sabemos **cuántos objetos** hay ni cuál es el guante.
El **etiquetado de componentes conectados** agrupa los píxeles blancos que se tocan y le asigna a
cada grupo un número (etiqueta). Para cada región, OpenCV devuelve:

- `stats`: `x, y, ancho, alto` del **rectángulo envolvente** (bounding box) y el **área** (número de píxeles).
- `centroides`: el **centro de masa** `(cx, cy)` de la región.
- La **etiqueta 0 siempre es el fondo**; por eso se busca entre `stats[1:]` y se suma 1.

### Conectividad 8 vs 4

```
Conectividad 4:     Conectividad 8:
    · X ·               X X X
    X P X               X P X
    · X ·               X X X
```

Con **8** también cuentan los vecinos en diagonal. Se usa 8 porque los bordes diagonales del guante
(dedos inclinados) no deben partir el guante en varias regiones.

### Criterios de selección

1. **La región más grande**: en la mitad de cada jugador, el guante es el objeto amarillo dominante.
   Si hubiera otro objeto amarillo pequeño en el fondo, pierde frente al guante.
2. **Área mínima** (`AREA_MINIMA`, 1500 por defecto; 1000 en la calibración actual): si ni siquiera
   la región más grande la alcanza, se responde **"no hay guante"** (`None`). Esto evita que, cuando
   el jugador baja la mano, la paleta salte a perseguir un lápiz amarillo del fondo.

### ¿Por qué 1500 (o 1000) píxeles?

Cada mitad de la imagen es 320 × 480 = **153 600 px**. 1500 px ≈ **1 %** de la mitad, equivalente a
un cuadrado de ~39 × 39 px. Un guante a distancia de juego (≈ 0.5 - 1.5 m) ocupa bastante más; un
objeto amarillo pequeño o un reflejo, bastante menos. Depende de la distancia a la cámara, por eso es
**calibrable** (barra "Area min x100").

---

## 10. Paso 5 — Posición: centroide y normalización

El **centroide** es el promedio de las coordenadas de todos los píxeles de la región (momentos de
orden 0 y 1):

```
cx = (Σ x) / A      cy = (Σ y) / A        con A = área = número de píxeles (momento M00)
```

Por qué el centroide y no, por ejemplo, el punto más alto del guante:

- Usa **todos** los píxeles → es **robusto**: si unos pocos píxeles del borde aparecen o desaparecen,
  el promedio casi no se mueve.
- Corresponde intuitivamente al "centro de la mano".

**Normalización**: `y_norm = cy / alto` → de **0.0 (arriba) a 1.0 (abajo)**. Así el resultado no
depende de la resolución de la cámara ni del tamaño de la ventana del juego. Solo se usa la Y porque
las paletas solo se mueven en vertical.

---

## 11. Suavizado temporal: filtro exponencial

Código: `deteccion.py → class Suavizado`; parámetro `SUAVIZADO = 0.5`.

```python
valor = alfa * nuevo + (1 - alfa) * valor_anterior
```

### Problema

Aunque la mano esté quieta, el centroide "baila" unos píxeles de un cuadro a otro (ruido residual,
bordes que cambian). La paleta temblaría.

### Solución: media móvil exponencial (EMA, filtro IIR de primer orden)

Es un **filtro pasa-bajos en el tiempo** (no en el espacio, como el gaussiano). Cada valor nuevo se
mezcla con el anterior. Los cuadros viejos pesan cada vez menos: `α, α(1−α), α(1−α)², …`

### ¿Por qué α = 0.5?

- **Respuesta**: ante un salto de la mano, el error restante tras n cuadros es `(1 − α)^n = 0.5^n`:
  tras 1 cuadro 50 %, tras 3 cuadros 12.5 %, tras 5 cuadros ~3 %. A 30 fps, eso es **~100 ms para
  llegar al 87 %** del movimiento: se percibe como inmediato.
- **Reducción de ruido**: para ruido blanco, la varianza de salida es `α / (2 − α) = 1/3` de la de
  entrada → la desviación estándar del temblor baja a **~58 %**.
- α → 1: sin suavizado (rápido pero tiembla). α → 0: muy estable pero con retraso notable (se siente
  "pesado"). **0.5 es el punto medio** para un juego que requiere reacción rápida.

### Casos especiales

- **Primera detección**: no hay valor anterior → se toma el nuevo directamente (si no, se promediaría
  con nada o con 0 y la paleta arrancaría desde arriba).
- **Guante perdido** (`nuevo is None`): se **mantiene el último valor**. El detector recuerda dónde
  estaba el guante; el bridge decide qué hacer con eso (ver sección 14).
- Hay **un filtro por jugador** (`[Suavizado(), Suavizado()]`), para que no se mezclen sus posiciones.

### Dos filtros, dos dominios (buena frase para la sustentación)

> "Usamos un pasa-bajos **espacial** (gaussiano) para el ruido dentro de cada imagen, y un pasa-bajos
> **temporal** (exponencial) para el ruido entre imágenes."

---

## 12. División en dos jugadores

Código: `deteccion.py → DetectorGuantes.procesar()`.

```python
suave   = filtrar(imagen)                  # pasos 1-3 sobre la imagen completa (una sola vez)
mascara = limpiar(umbral_amarillo(suave))
for jugador, (x0, x1) in enumerate(((0, mitad), (mitad, ancho))):
    region = region_mas_grande(mascara[:, x0:x1], area_minima)   # pasos 4-5 por mitad
    ...
    region = (cx + x0, cy, area, (x + x0, y, w, h))              # volver a coords. de la imagen completa
```

- Los pasos 1 a 3 (filtro, umbral, morfología) son **iguales para ambos jugadores**, así que se
  hacen **una sola vez** sobre toda la imagen (más eficiente).
- La segmentación (paso 4) se hace **en cada mitad por separado**: así cada jugador tiene su propio
  "guante más grande". Si se segmentara la imagen completa, solo se encontraría un guante.
- `mascara[:, x0:x1]` es un **recorte (slice) de NumPy**: no copia memoria, es una vista.
- Como la región de la mitad derecha se buscó en coordenadas locales (empezando en 0), se le **suma
  `x0`** para dibujarla en el lugar correcto de la imagen completa. La Y no cambia.

`procesar` devuelve tres cosas:

| Salida | Contenido |
|---|---|
| `posiciones` | `[y_j1, y_j2]` suavizadas (0-1). Si se perdió el guante, conserva la última; `None` solo si nunca se vio. |
| `regiones` | Lo detectado **en este cuadro** (o `None`): centroide, área, rectángulo. |
| `mascara` | Máscara limpia completa, para depuración/visualización. |

---

## 13. Calibración: prueba_camara.py y calibracion.json

### Por qué hace falta

El color que ve la cámara **no es el color real** del guante: depende de la **iluminación** (luz
cálida → más rojo; luz fría/LED → más azul; poca luz → todo más oscuro), del balance de blancos
automático de la cámara y del fondo. Unos umbrales fijos que funcionan en un salón pueden fallar en
otro. Por eso los umbrales son **ajustables en vivo y persistentes**.

### Cómo se usa

```
python PDI/prueba_camara.py        # cámara por defecto
python PDI/prueba_camara.py 1      # otra cámara
```

Tres ventanas:

| Ventana | Qué muestra |
|---|---|
| **PDI - Camara** | Imagen en espejo, línea divisoria de jugadores, rectángulo + centroide de cada guante, línea en la Y suavizada y el valor `Y = 0.xx` (o "sin guante" / "perdido"). |
| **PDI - Mascara** | La máscara después de umbral + morfología (blanco = amarillo). **El objetivo de calibrar es que aquí solo se vean los guantes.** |
| **PDI - Umbrales** | Barras: `R min`, `G min`, `B max`, `\|R-G\| max`, `Area min x100` (el área se multiplica por 100 porque las barras de OpenCV solo manejan enteros pequeños con comodidad). |

Procedimiento recomendado (para contarlo en la sustentación):

1. Poner el guante frente a la cámara y **hacer clic sobre él**: se imprimen sus valores R, G, B
   (lectura del píxel original, antes de dibujar encima).
2. Hacer clic sobre el fondo, la piel y la ropa para ver sus valores.
3. Ajustar las barras para que el guante quede **dentro** de las reglas y lo demás **fuera**:
   - Si aparece la pared blanca → bajar `B max`.
   - Si aparece la piel o algo naranja → bajar `|R-G| max` o subir `G min`.
   - Si el guante sale con huecos o se pierde en sombra → bajar `G min` / `R min` o subir `B max`.
   - Si aparecen manchas amarillas pequeñas que se toman como guante → subir `Area min`.
4. Pulsar **G** → se guarda `calibracion.json` y aparece "Calibracion guardada".
5. **Q / Esc** para salir.

### Cómo se carga

En `config.py`, al importarse el módulo:

```python
CALIBRACION_CARGADA = cargar_calibracion()   # reemplaza R_MIN, G_MIN, B_MAX, DIF_RG_MAX, AREA_MINIMA
```

- Solo se sobrescriben los parámetros de `CALIBRABLES` (lista blanca): un JSON con claves extra no
  rompe nada.
- Si el archivo no existe → se usan los valores por defecto. **Para resetear basta con borrar
  `calibracion.json`.**
- El bridge imprime al arrancar si usa calibración "guardada" o "por defecto".
- Los tamaños de kernel y el suavizado **no** se calibran (dependen de la cámara/ruido, no de la
  luz), se cambian en `config.py`.

---

## 14. El bridge (bridge.py)

Clase `PuenteCamara`. Es el **adaptador** entre PDI y el juego.

### 14.1 Por qué un hilo aparte (concurrencia)

- La cámara entrega **~15-30 cuadros por segundo** y `captura.read()` **bloquea** hasta que llega
  un cuadro nuevo (hasta ~33-66 ms).
- El juego dibuja a **60 fps** (≈ 16.7 ms por cuadro).
- Si el juego leyera la cámara en su propio bucle, **se trabaría** al ritmo de la cámara y además
  cargaría con el tiempo del procesamiento.

Solución: **patrón productor-consumidor con "último valor"**:

```
Hilo cámara (productor):  read() → flip → detector.procesar() → _a_campo() → vistas → [candado] guarda
Hilo juego (consumidor):  cada cuadro → [candado] lee posiciones()/vista_previa() → mueve paletas
```

El juego **nunca espera** a la cámara: siempre toma el resultado más reciente disponible.

- `daemon=True`: si el juego se cierra, el hilo no impide que el programa termine.
- `detener()`: pone `_activo = False`, espera al hilo (`join(timeout=1)`) y **libera la cámara**
  (`release()`) para que otros programas la puedan usar. `main.py` lo llama en un `finally`, así se
  libera incluso si el juego falla.
- Si la cámara no abre, `iniciar()` devuelve `False` y el juego sigue **solo con teclado**
  (degradación elegante).

### 14.2 El candado (`threading.Lock`)

Las listas `_posiciones` y `_vistas` las **escribe** el hilo de la cámara y las **lee** el del juego.
Sin sincronización, el juego podría leer mientras se escriben (condición de carrera). Con
`with self._candado:` la escritura y la lectura son **atómicas**. Además, `posiciones()` y
`vista_previa()` devuelven **copias** (`list(...)`), para que el juego no comparta la lista interna.

El trabajo pesado (procesar, dibujar vistas) se hace **fuera** del candado; dentro solo se asignan
referencias → el candado se mantiene durante microsegundos y no frena al juego.

### 14.3 Solo se entrega la posición si el guante se ve **en este cuadro**

```python
actuales = [self._a_campo(y) if region is not None else None
            for y, region in zip(posiciones, regiones)]
```

Aunque el detector recuerde la última Y, el bridge envía `None` cuando el guante no se ve ahora. El
juego interpreta `None` como "usa el teclado para este jugador" (W/S o ↑/↓). Así un jugador puede
jugar con guante y otro con teclado, y si alguien baja la mano la paleta no se queda "pegada"
obedeciendo a un guante que ya no está.

### 14.4 Mapeo de cámara a campo: `RANGO_Y = (0.15, 0.85)`

```python
y_campo = clamp((y - 0.15) / (0.85 - 0.15), 0, 1)
```

Es una **transformación lineal (normalización min-max) con saturación**:

| Y en cámara | Y en campo |
|---|---|
| 0.00 - 0.15 | 0.0 (arriba del todo) |
| 0.15 | 0.0 |
| 0.30 | 0.214 |
| 0.50 | 0.5 |
| 0.85 | 1.0 |
| 0.85 - 1.00 | 1.0 (abajo del todo) |

Por qué no usar la imagen completa (0 a 1):

- Cerca de los **bordes** de la imagen el guante queda **cortado**: su área baja y su centroide se
  desplaza hacia dentro → nunca llegaría realmente a 0 o a 1, y la paleta no alcanzaría las esquinas.
- Es **incómodo** llevar la mano hasta el borde de la cámara (encima de la cabeza / a la cintura).
- Con el 70 % central de la imagen se recorre **todo** el campo. El margen (15 % arriba y abajo) se
  satura → la paleta queda en el borde sin salirse.
- Se ve en la vista previa del juego como **dos líneas grises**.

Nota: el suavizado se aplica antes del mapeo; como el mapeo es lineal (dentro del rango), el orden
no cambia el resultado.

### 14.5 Vista previa

`_crear_vistas` dibuja sobre una **copia** del cuadro (el original no se altera):
las líneas grises de `RANGO_Y`, el rectángulo del guante y la línea de la Y suavizada con el color de
cada jugador (rojo J1, azul J2). Luego:

- Divide la imagen en **dos mitades** (una por jugador).
- La reduce al **25 %** (`ESCALA_VISTA`) con `INTER_AREA`, la interpolación recomendada para
  **reducir** imágenes (promedia los píxeles del área, evita aliasing / "dientes de sierra").
- Convierte **BGR → RGB**, porque pygame usa RGB.

### 14.6 Contrato con el juego

| Método | Devuelve |
|---|---|
| `posiciones()` | `[y_j1, y_j2]`, cada uno en 0.0 (arriba) - 1.0 (abajo) o `None` si no se ve. |
| `vista_previa()` | `[img_j1, img_j2]` (arreglos NumPy RGB) o `None` si todavía no hay imagen. |

El juego convierte ese 0-1 a píxeles del campo y mueve la paleta hacia ahí con una **velocidad
máxima** (`CAMERA_PADDLE_SPEED`), lo que añade una segunda capa de suavidad (la paleta no se
teletransporta). Eso ya es parte del juego, no del PDI.

---

## 15. Tabla resumen de parámetros y por qué esos valores

| Parámetro | Valor | Dónde | Justificación corta |
|---|---|---|---|
| `CAMARA` | 0 | config | Primera cámara del sistema. |
| `ANCHO × ALTO` | 640 × 480 | config | Estándar, rápido, suficiente precisión. |
| `ESPEJO` | True | config | Movimiento intuitivo; jugador izquierdo = mitad izquierda. |
| `KERNEL_DESENFOQUE` | 5 | config | Quita ruido de 1-2 px, σ ≈ 1.1, no borra el guante; impar. |
| `R_MIN` | 150 (calib. 0) | config/json | Rojo alto; en la calibración lo garantizan G y \|R−G\|. |
| `G_MIN` | 150 (calib. 173) | config/json | Verde alto; descarta rojos, naranjas, piel, sombras. |
| `B_MAX` | 110 (calib. 167) | config/json | Poco azul; descarta blancos y grises. |
| `DIF_RG_MAX` | 70 (calib. 48) | config/json | R ≈ G: tono amarillo; descarta naranja y verde. |
| `KERNEL_MORFOLOGIA` | 7 (elipse) | config | Mayor que el ruido, menor que el guante; isotrópico. |
| `AREA_MINIMA` | 1500 (calib. 1000) | config/json | ≈ 1 % de la mitad de imagen; ignora objetos pequeños. |
| `connectivity` | 8 | deteccion | No partir el guante por bordes diagonales. |
| `SUAVIZADO` (α) | 0.5 | config | ~100 ms de respuesta a 30 fps; temblor reducido ~42 %. |
| `RANGO_Y` | (0.15, 0.85) | bridge | Evita bordes (guante cortado), más cómodo. |
| `ESCALA_VISTA` | 0.25 | bridge | Vista previa pequeña que no tapa el juego. |

---

## 16. Rendimiento

- Todas las operaciones son **O(N)** en el número de píxeles (N = 307 200) y están implementadas en
  C/C++ (OpenCV) o vectorizadas (NumPy). Tiempo típico por cuadro: **pocos milisegundos**, muy por
  debajo de los 33 ms que hay entre cuadros de una cámara a 30 fps.
- El filtro gaussiano es **separable** (10 operaciones por píxel en vez de 25).
- Los pasos 1-3 se hacen **una sola vez** para los dos jugadores.
- El cuello de botella real es la **cámara** (fps), no el procesamiento; por eso se aisla en un hilo.
- **Latencia total** aproximada: captura (~33 ms) + procesamiento (pocos ms) + suavizado (~1-3
  cuadros para converger) + velocidad máxima de la paleta. Se siente inmediato para jugar.

---

## 17. Limitaciones y mejoras posibles

Ser honesto con las limitaciones **suma puntos** en una sustentación.

| Limitación | Por qué pasa | Mejora posible |
|---|---|---|
| Sensible a la iluminación | RGB mezcla color y brillo | Umbralizar en **HSV** o **YCrCb / Lab** (separan tono de brillo); normalizar por brillo (cromaticidad `r = R/(R+G+B)`); fijar exposición y balance de blancos de la cámara. |
| Objetos amarillos grandes en el fondo | La regla elige "la región más grande" | Máscara de región de interés, **sustracción de fondo**, o elegir la región más cercana a la posición anterior (seguimiento). |
| Un jugador que cruza a la mitad del otro | La división es fija por la mitad | División dinámica o seguimiento por identidad. |
| Guante cortado en el borde | Centroide desplazado | Ya mitigado con `RANGO_Y`. |
| Al reaparecer el guante, el suavizado parte del último valor viejo | `Suavizado` conserva el valor | Reiniciar el filtro tras N cuadros sin detección. |
| Movimientos muy rápidos se ven borrosos | *Motion blur* de la cámara | Más luz (menos tiempo de exposición), cámara de más fps. |
| Umbral fijo (no adaptativo) | Se calibra a mano | Calibración automática: muestrear el color del guante en un recuadro y fijar umbrales alrededor (media ± k·desviación). Umbral de **Otsu** sobre un canal de tono. |
| Predicción | Solo se usa la posición actual | **Filtro de Kalman** (posición + velocidad) para compensar latencia. |

---

## 18. Guion sugerido para la sustentación

Duración sugerida: 8-12 minutos. Puntos que **no pueden faltar** en negrita.

1. **Problema y restricción** (1 min): controlar el juego con la mano, **sin IA**, solo PDI clásico;
   por qué **amarillo** (color poco común, firma RGB clara).
2. **Arquitectura** (1 min): diagrama de la sección 2; **PDI independiente del juego**, el bridge
   como único punto de unión.
3. **Pipeline** (4-5 min) — ideal mostrar la imagen/máscara de cada etapa:
   - **Filtro gaussiano 5×5**: ruido, kernel [1 4 6 4 1]/16, pesos suman 1, separable, ejemplo del
     píxel de ruido que baja a 36.
   - **Umbral RGB**: las 4 reglas y qué descarta cada una, **por qué int16**, vectorización.
   - **Morfología**: apertura (quita ruido) + cierre (rellena huecos), **orden**, **elemento
     elíptico 7×7**.
   - **Componentes conectados**: conectividad 8, región más grande, **área mínima**.
   - **Centroide** y normalización 0-1.
   - **Suavizado exponencial** α = 0.5: espacial vs temporal.
4. **Dos jugadores** (30 s): pasos 1-3 una vez, segmentación por mitad, corrección de coordenadas.
5. **Calibración** (1 min): por qué depende de la luz, **demo en vivo** con las barras y el clic.
6. **Bridge** (1-2 min): **hilo + candado** (cámara 30 fps vs juego 60 fps), `None` → teclado,
   **mapeo RANGO_Y**, vista previa (BGR→RGB, INTER_AREA).
7. **Demo del juego** (1-2 min).
8. **Limitaciones y mejoras** (1 min): iluminación / HSV, fondo amarillo, Kalman.

**Consejos para la demo**

- Calibrar **en el lugar de la sustentación** antes de empezar (la luz cambia).
- Evitar ropa amarilla/naranja y fondos blancos muy iluminados.
- Tener abierta la ventana **PDI - Mascara** para mostrar que solo aparecen los guantes.
- Mostrar qué pasa al subir/bajar una barra (p. ej. subir `B max` hasta que aparezca la pared:
  demuestra por qué existe esa regla).
- Tener plan B: si falla la cámara, el juego funciona con teclado.

---

## 19. Preguntas probables del jurado (con respuesta)

**¿Por qué RGB y no HSV?**
HSV separa el tono del brillo y suele ser más robusto a la iluminación. Elegimos RGB porque las
reglas son **directamente interpretables** con los valores que muestra la calibración (clic → R, G,
B) y, combinadas, **aproximan** una umbralización por tono (|R−G|), saturación (B bajo) y brillo (R,
G altos). La dependencia de la luz se compensa con la calibración guardada. HSV es la primera
mejora que haríamos.

**¿Por qué filtrar antes de umbralizar y no después?**
El filtro trabaja sobre la imagen en color (valores continuos): promedia el ruido **antes** de tomar
la decisión binaria. Después de umbralizar, el ruido ya se convirtió en píxeles blancos/negros y se
limpia con morfología, que es lo que hacemos en el paso 3. Son complementarios.

**¿Qué pasa si el kernel es par?**
No hay píxel central: el filtro queda desplazado medio píxel. OpenCV exige tamaño impar en
`GaussianBlur`.

**¿Qué diferencia hay entre apertura y erosión?**
La erosión sola adelgaza **todo**, incluido el guante. La apertura (erosión + dilatación) elimina
lo pequeño y **restaura** el tamaño de lo que sobrevive, así el centroide no se mueve.

**¿Por qué no usar `findContours`?**
Podría usarse (contorno más grande + `moments`). `connectedComponentsWithStats` da en una sola
llamada área, rectángulo y centroide de todas las regiones, sin calcular momentos aparte.

**¿Qué pasa si los dos jugadores están en la misma mitad?**
Se tomaría el guante más grande de esa mitad y el otro jugador se ignoraría. La división por mitades
es una regla del juego (cada uno en su lado).

**¿Qué pasa si no se detecta el guante?**
El detector conserva la última Y (suavizada) pero el bridge envía `None`, y el juego cambia ese
jugador a teclado hasta que el guante vuelva a verse.

**¿Por qué un hilo? ¿No es peligroso?**
La lectura de la cámara bloquea; sin hilo, el juego iría a la velocidad de la cámara. El peligro
(condición de carrera) se evita con un `Lock`, y el hilo es `daemon` y se detiene y libera la cámara
en un `finally`.

**¿Por qué `int16` en la umbralización?**
Porque `uint8` no tiene negativos: `10 − 20 = 246`. Con `int16` la resta y el valor absoluto son
correctos.

**¿Cómo eligieron los valores de los umbrales?**
Midiendo con clic el color real del guante, la piel, la pared y la ropa en la escena, y ajustando las
barras hasta que en la máscara solo quedara el guante. Los valores por defecto son un punto de
partida; los reales se guardan por escena en `calibracion.json`.

**¿Por qué α = 0.5?**
Compromiso entre estabilidad y latencia: el temblor baja a ~58 % y en 3 cuadros (~100 ms a 30 fps)
se alcanza el 87 % de un movimiento.

**¿Qué es `RANGO_Y`?**
Una normalización lineal con saturación: la franja 15 %-85 % de la cámara se estira a todo el campo,
porque en los bordes el guante se corta y porque es más cómodo.

**¿Por qué el efecto espejo?**
Para que el movimiento sea natural (como un espejo) y para que el jugador de la izquierda quede en
la mitad izquierda de la imagen.

**¿Complejidad?**
Lineal en el número de píxeles para todas las etapas; en la práctica pocos ms por cuadro, muy por
debajo del intervalo entre cuadros de la cámara.

---

## 20. Glosario rápido

| Término | Definición |
|---|---|
| **Píxel** | Unidad mínima de la imagen; en color, 3 valores 0-255. |
| **Canal** | Una de las componentes de color (B, G o R). |
| **Kernel / máscara de convolución** | Matriz pequeña de pesos que se desliza sobre la imagen. |
| **Convolución** | Suma ponderada de la vecindad de cada píxel con los pesos del kernel. |
| **Filtro pasa-bajos** | Deja pasar variaciones lentas (formas) y atenúa las rápidas (ruido). |
| **Umbralización** | Convertir una imagen en binaria comparando cada píxel con un umbral. |
| **Máscara binaria** | Imagen de 0/255 que marca qué píxeles cumplen una condición. |
| **Elemento estructurante** | Forma que define la vecindad en morfología. |
| **Erosión / dilatación** | Mínimo / máximo sobre la vecindad del EE. |
| **Apertura / cierre** | Erosión+dilatación / dilatación+erosión. |
| **Componente conectado** | Grupo máximo de píxeles blancos conectados entre sí. |
| **Conectividad 4 / 8** | Vecinos ortogonales / ortogonales + diagonales. |
| **Bounding box** | Rectángulo mínimo que contiene la región. |
| **Centroide** | Centro de masa de la región (promedio de coordenadas). |
| **EMA** | Media móvil exponencial; filtro temporal de primer orden. |
| **Hilo (thread)** | Flujo de ejecución concurrente dentro del mismo programa. |
| **Lock / candado** | Mecanismo que impide que dos hilos accedan a la vez a un dato. |
| **Calibración** | Ajuste de parámetros a las condiciones reales de la escena. |

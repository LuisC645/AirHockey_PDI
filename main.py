from game import run
from bridge import PuenteCamara


if __name__ == "__main__":
    # la cámara controla las paletas con los guantes amarillos; si no hay cámara se juega con teclado
    puente = PuenteCamara()
    puente.iniciar()
    try:
        run(control=puente)
    finally:
        puente.detener()

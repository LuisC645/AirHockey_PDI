from . import constants as const
import pygame
import os

auxDirectory = os.path.join(os.path.dirname(__file__), 'assets')

smallfont = None
score1, score2 = 0, 0

# Sound globals.
paddleHit = None
goal_whistle = None

play_image = pygame.image.load(os.path.join(auxDirectory, 'play.png'))
pause_image = pygame.image.load(os.path.join(auxDirectory, 'pause.png'))


def load_background(filename):
    """Loads a background image from assets scaled to the window, or None if it does not exist."""
    path = os.path.join(auxDirectory, filename)
    if not os.path.isfile(path):
        return None
    return pygame.transform.smoothscale(pygame.image.load(path), (const.WIDTH, const.HEIGHT))


_fonts = {}


def get_font(size, bold=False):
    """Returns the game font (JetBrains Mono) with the given size."""
    key = (size, bold)
    if key not in _fonts:
        name = const.FONT_BOLD if bold else const.FONT_REGULAR
        _fonts[key] = pygame.font.Font(os.path.join(auxDirectory, name), size)
    return _fonts[key]


field_image = load_background(const.FIELD_IMAGE)

# game globals.
clock = None
screen = None

# width and height of the screen.
width, height = const.WIDTH, const.HEIGHT

# button constants
buttonRadius = 60

# color globals
# (dimgreen, green) , (dimred, red) , (dimblue, blue ) , (yellow, dimyellow), (orange, dimorange)
colors = [[(46, 120, 50), (66, 152, 60)], [(200, 72, 72), (255, 92, 92)],
          [(0, 158, 239), (100, 189, 219)], [(221, 229, 2), (252, 255, 59)],
          [(232, 114, 46), (244, 133, 51)]]

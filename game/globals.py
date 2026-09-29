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


def find_asset(filenames):
    """Path of the first of these files that exists in assets, or None."""
    for filename in filenames:
        path = os.path.join(auxDirectory, filename)
        if os.path.isfile(path):
            return path
    return None


def load_background(filenames):
    """Loads the first background image found in assets, scaled to the window, or None if there is none."""
    path = find_asset(filenames)
    if path is None:
        return None
    return pygame.transform.smoothscale(pygame.image.load(path), (const.WIDTH, const.HEIGHT))


def load_round_image(filenames, radius):
    """
    Loads the first image found in assets, takes its central square (so it is never stretched), scales it
    to (2 * radius) x (2 * radius) and crops it to a circle, so it has exactly the size of the paddle or
    puck it replaces. None if there is no image.
    """
    path = find_asset(filenames)
    if path is None:
        return None

    image = pygame.image.load(path)
    w, h = image.get_size()
    side = min(w, h)
    image = image.subsurface(((w - side) // 2, (h - side) // 2, side, side))

    size = 2 * radius
    image = pygame.transform.smoothscale(image, (size, size))

    # copy it to a surface with transparency and erase everything outside the circle
    round_image = pygame.Surface((size, size), pygame.SRCALPHA)
    round_image.blit(image, (0, 0))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
    round_image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return round_image


_fonts = {}


def get_font(size, bold=False):
    """Returns the game font (JetBrains Mono) with the given size."""
    key = (size, bold)
    if key not in _fonts:
        name = const.FONT_BOLD if bold else const.FONT_REGULAR
        _fonts[key] = pygame.font.Font(os.path.join(auxDirectory, name), size)
    return _fonts[key]


field_image = load_background(const.FIELD_IMAGES)
paddle1_image = load_round_image(const.PADDLE1_IMAGES, const.PADDLE_SIZE)
paddle2_image = load_round_image(const.PADDLE2_IMAGES, const.PADDLE_SIZE)
puck_image = load_round_image(const.PUCK_IMAGES, const.PUCK_SIZE)

# game globals.
clock = None
screen = None

# width and height of the screen.
width, height = const.WIDTH, const.HEIGHT

# color globals
# (dimgreen, green) , (dimred, red) , (dimblue, blue ) , (yellow, dimyellow), (orange, dimorange)
colors = [[(46, 120, 50), (66, 152, 60)], [(200, 72, 72), (255, 92, 92)],
          [(0, 158, 239), (100, 189, 219)], [(221, 229, 2), (252, 255, 59)],
          [(232, 114, 46), (244, 133, 51)]]

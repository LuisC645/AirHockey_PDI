from .globals import *

# function to render font


def text_obj(text, font, color):
    text_surface = font.render(text, True, color)
    return text_surface, text_surface.get_rect()


# function to display text


def disp_text(screen, text, center, font_and_size, color):
    text_surf, text_rect = text_obj(text, font_and_size, color)
    text_rect.center = center
    screen.blit(text_surf, text_rect)


# function to render a rectangular button, returns True if the mouse is over it


def button_rect(screen, rect, color, hover_color, text, font, mouse):
    hovered = rect.collidepoint(mouse)
    pygame.draw.rect(screen, hover_color if hovered else color, rect, border_radius=6)
    disp_text(screen, text, rect.center, font, const.WHITE)
    return hovered


# function to render a translucent dark panel behind overlay texts


def draw_panel(screen, rect):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (20, 24, 28, 200), panel.get_rect(), border_radius=12)
    screen.blit(panel, rect.topleft)

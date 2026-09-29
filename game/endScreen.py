import sys
from .ui import *
from .globals import *

# game end screen function


def game_end(screen, clock, background_color, player_name):
    """Shows the winner. Returns when the game has to be reset, exits if Quit is pressed."""

    celeb_text = get_font(72, bold=True)
    large_text = get_font(30, bold=True)
    small_text = get_font(26, bold=True)

    reset_pos = (width / 2 - 200, 470)
    quit_pos = (width / 2 + 200, 470)

    while True:

        if field_image:
            screen.blit(field_image, (0, 0))
        else:
            screen.fill(background_color)

        # Get inputs
        mouse_pos = pygame.mouse.get_pos()
        mouse_press = pygame.mouse.get_pressed()

        for event in pygame.event.get():
            # Press R to reset game
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                return
            # Press esc or Q to quit
            elif event.type == pygame.KEYDOWN and (event.key == pygame.K_q or event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # print which player won
        disp_text(screen, "{0} WINS".format(player_name.upper()), (width / 2, height / 2 - 120),
                  celeb_text, const.BLACK)

        # Reset button
        if abs(mouse_pos[0] - reset_pos[0]) < buttonRadius and abs(mouse_pos[1] - reset_pos[1]) < buttonRadius:
            button_circle(screen, colors[0][0], reset_pos, "Reset", large_text, const.WHITE, reset_pos)
            if mouse_press[0] == 1:
                return
        else:
            button_circle(screen, colors[0][0], reset_pos, "Reset", small_text, const.WHITE, reset_pos)

        # Quit button
        if abs(mouse_pos[0] - quit_pos[0]) < buttonRadius and abs(mouse_pos[1] - quit_pos[1]) < buttonRadius:
            button_circle(screen, colors[1][1], quit_pos, "Quit", large_text, const.WHITE, quit_pos)
            if mouse_press[0] == 1:
                pygame.quit()
                sys.exit()
        else:
            button_circle(screen, colors[1][0], quit_pos, "Quit", small_text, const.WHITE, quit_pos)

        pygame.display.update()
        clock.tick(10)

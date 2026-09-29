import sys
from pygame.locals import *
from .paddle import Paddle
from .puck import Puck
from .ui import disp_text, button_rect, draw_panel
from .globals import *

# Globals, initialized in method `init()`

# Create game objects.
paddle1 = Paddle(const.PADDLE1X, const.PADDLE1Y)
paddle2 = Paddle(const.PADDLE2X, const.PADDLE2Y)
puck = Puck(width / 2, height / 2)

# External control (camera bridge), set in run(). It must have:
#   posiciones()   -> [y_player1, y_player2] from 0.0 (top) to 1.0 (bottom), None to use the keyboard
#   vista_previa() -> [image_player1, image_player2] RGB numpy arrays, or None
external_control = None


def init():
    global paddleHit, goal_whistle, clock, screen, smallfont, boldfont, scorefont
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()
    pygame.init()

    gamelogo = pygame.image.load(os.path.join(auxDirectory, 'AHlogo.png'))
    pygame.display.set_icon(gamelogo)
    pygame.display.set_caption('Air Hockey')
    screen = pygame.display.set_mode((width, height))

    paddleHit = pygame.mixer.Sound(os.path.join(auxDirectory, 'hit.wav'))
    goal_whistle = pygame.mixer.Sound(os.path.join(auxDirectory, 'goal.wav'))

    smallfont = get_font(22)
    boldfont = get_font(26, bold=True)
    scorefont = get_font(40, bold=True)

    clock = pygame.time.Clock()


def draw_label(text, font, color, **position):
    """
    Draws a text over a small translucent dark panel, so it can be read over any background.
    `position` is passed to get_rect(), e.g. center=(x, y) or midleft=(x, y).
    """
    text_image = font.render(text, True, color)
    rect = text_image.get_rect(**position)
    draw_panel(screen, rect.inflate(const.LABEL_PADDING * 2, const.LABEL_PADDING))
    screen.blit(text_image, rect)


def draw_hud():
    """Player names on the sides (in their paddle color) and the score of the current game in the center."""
    y = const.MARGIN + 12
    pad = const.LABEL_PADDING
    draw_label(const.PLAYER1_NAME, boldfont, const.PLAYER1_COLOR, midleft=(const.MARGIN + pad, y))
    draw_label(const.PLAYER2_NAME, boldfont, const.PLAYER2_COLOR, midright=(width - const.MARGIN - pad, y))
    draw_label("{0} : {1}".format(score1, score2), scorefont, const.HUD_TEXT_COLOR, center=(width / 2, y))


def show_winner(winner_name):
    """Shows who won the game and the final score, then returns so a new game can start."""
    # the field behind the overlay, redrawn every frame so the panel keeps its transparency
    background = screen.copy()
    panel_rect = pygame.Rect(0, 0, 560, 220)
    panel_rect.center = (width / 2, height / 2)
    winner_font = get_font(48, bold=True)

    start = pygame.time.get_ticks()
    total = const.WINNER_DELAY * 1000
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        elapsed = pygame.time.get_ticks() - start
        if elapsed >= total:
            return

        screen.blit(background, (0, 0))
        draw_panel(screen, panel_rect)
        disp_text(screen, "{0} WINS".format(winner_name.upper()), (width / 2, height / 2 - 55), winner_font,
                  colors[3][1])
        disp_text(screen, "{0}  :  {1}".format(score1, score2), (width / 2, height / 2 + 5), scorefont,
                  const.WHITE)
        disp_text(screen, "next game in {0}".format(const.WINNER_DELAY - elapsed // 1000),
                  (width / 2, height / 2 + 65), smallfont, const.WHITE)

        pygame.display.flip()
        clock.tick(const.FPS)


# function to display pause screen


def show_pause_screen():
    """
        Shows the pause screen,
        This function will return,
        2 if the game is to be restarted,
        1 if the game is to be continued
        and exit here itself if exit is pressed
    """

    # the field behind the overlay, redrawn every frame so the panel keeps its transparency
    background = screen.copy()
    panel_rect = pygame.Rect(0, 0, 760, 300)
    panel_rect.center = (width / 2, 310)

    while True:
        screen.blit(background, (0, 0))
        draw_panel(screen, panel_rect)

        disp_text(screen, "PAUSED", (width / 2, 200), boldfont, const.WHITE)
        screen.blit(play_image, [width / 2 - 32, height - 70])

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        # buttons: RESET, CONTINUE and EXIT
        reset_rect = pygame.Rect(0, 0, 180, 44)
        reset_rect.center = (width / 2 - 220, height - 180)
        cont_rect = pygame.Rect(0, 0, 180, 44)
        cont_rect.center = (width / 2, height - 180)
        exit_rect = pygame.Rect(0, 0, 180, 44)
        exit_rect.center = (width / 2 + 220, height - 180)

        if button_rect(screen, reset_rect, colors[4][1], colors[4][0], "RESET", smallfont, mouse) and click[0] == 1:
            return 2
        if button_rect(screen, cont_rect, colors[0][1], colors[0][0], "CONTINUE", smallfont, mouse) and click[0] == 1:
            return 1
        if button_rect(screen, exit_rect, colors[1][1], colors[1][0], "EXIT", smallfont, mouse) and click[0] == 1:
            pygame.quit()
            sys.exit()

        for event in pygame.event.get():
            # removing pause using space
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return 1

            # continue by pressing play button as well
            if event.type == pygame.MOUSEBUTTONUP:
                if hits_pause_area(mouse):
                    return 1

            if event.type == QUIT:
                sys.exit()

        pygame.display.flip()
        clock.tick(10)


# function to check is pause area is hit


def hits_pause_area(mouse_xy):
    """ Returns True if the mouse is clicked within the pause area"""

    return (abs(mouse_xy[0] - width / 2) < const.PAUSE_BUTTON_RADIUS) and \
           (abs(mouse_xy[1] - (height - 70 + 32)) < const.PAUSE_BUTTON_RADIUS)


def render_field(background_color):
    # Render Logic
    if field_image:
        screen.blit(field_image, (0, 0))
    else:
        screen.fill(background_color)

    # field lines: a background image usually brings its own, so they are only drawn over it if asked
    if field_image is None or const.FIELD_LINES_OVER_IMAGE:
        # center circle
        pygame.draw.circle(screen, const.WHITE, (width / 2, height / 2), 70, 5)
        # borders
        pygame.draw.rect(screen, const.WHITE, (0, 0, width, height), 5)
        # D-box
        pygame.draw.rect(screen, const.WHITE, (0, height / 2 - 150, 150, 300), 5)
        pygame.draw.rect(screen, const.WHITE, (width - 150, height / 2 - 150, 150, 300), 5)
        # Divider
        pygame.draw.rect(screen, const.WHITE, (width / 2, 0, 3, height))

    # goals
    pygame.draw.rect(screen, const.BLACK, (0, const.GOAL_Y1, 5, const.GOAL_WIDTH))
    pygame.draw.rect(screen, const.BLACK, (width - 5, const.GOAL_Y1, 5, const.GOAL_WIDTH))

    # PAUSE
    screen.blit(pause_image, (width / 2 - 32, height - 70))


def draw_game():
    """Draws the field, the scores, the paddles and the puck."""
    render_field(const.FIELD_COLOR)
    draw_hud()
    draw_camera()
    paddle1.draw(screen, const.PLAYER1_COLOR, paddle1_image)
    paddle2.draw(screen, const.PLAYER2_COLOR, paddle2_image)
    puck.draw(screen, puck_image)


def draw_camera():
    """Small camera preview split in two: player 1 at the bottom left, player 2 at the bottom right."""
    views = external_control.vista_previa() if external_control is not None else None
    if views is None:
        return

    for i, (view, color) in enumerate(zip(views, (const.PLAYER1_COLOR, const.PLAYER2_COLOR))):
        h, w = view.shape[:2]
        image = pygame.image.frombuffer(view.tobytes(), (w, h), "RGB")
        x = const.CAMERA_VIEW_MARGIN if i == 0 else width - const.CAMERA_VIEW_MARGIN - w
        y = height - const.CAMERA_VIEW_MARGIN - h
        screen.blit(image, (x, y))
        pygame.draw.rect(screen, color, (x - 3, y - 3, w + 6, h + 6), 3, border_radius=4)


def countdown():
    """Shows a countdown over the field while everything stays still."""
    number_font = get_font(96, bold=True)
    panel_rect = pygame.Rect(0, 0, 160, 160)
    panel_rect.center = (width / 2, height / 2 - 140)

    start = pygame.time.get_ticks()
    total = const.COUNTDOWN * 1000
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        elapsed = pygame.time.get_ticks() - start
        if elapsed >= total:
            return

        draw_game()
        draw_panel(screen, panel_rect)
        disp_text(screen, str(const.COUNTDOWN - elapsed // 1000), panel_rect.center, number_font, const.WHITE)

        pygame.display.flip()
        clock.tick(const.FPS)


def start_match():
    """Starts a new game at 0 : 0, shows the countdown and releases the puck from the center."""
    global score1, score2
    score1, score2 = 0, 0

    paddle1.reset()
    paddle2.reset()
    puck.kickoff(const.GAME_SPEED)  # puck stays still at the center until the countdown ends

    countdown()


def reset_game(speed, player):
    puck.reset(speed, player)
    paddle1.reset()
    paddle2.reset()


def inside_goal(side):
    """ Returns true if puck is within goal boundary"""
    if side == 0:
        return (puck.x - puck.radius <= 0) and (puck.y >= const.GOAL_Y1) and (puck.y <= const.GOAL_Y2)

    if side == 1:
        return (puck.x + puck.radius >= width) and (puck.y >= const.GOAL_Y1) and (puck.y <= const.GOAL_Y2)


def field_y(y_norm):
    """Converts a Y from 0.0 (top) to 1.0 (bottom) to a paddle position inside the field."""
    radius = const.PADDLE_SIZE
    return radius + y_norm * (height - 2 * radius)


# Game Loop
def game_loop():
    global score1, score2
    speed = const.GAME_SPEED

    pygame.mixer.music.load(os.path.join(auxDirectory, 'back.mp3'))  # background music
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(.2)

    start_match()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # pause with the space bar or by clicking the pause button
            pause = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
                    (event.type == pygame.MOUSEBUTTONUP and hits_pause_area(event.pos))

            # if the pause screen returns 2 reset everything
            if pause and show_pause_screen() == 2:
                start_match()

        key_presses = pygame.key.get_pressed()

        # Process Player 1 Input (only up and down, x is locked)
        w = key_presses[pygame.K_w]
        s = key_presses[pygame.K_s]

        # Process Player 2 Input (only up and down, x is locked)
        up = key_presses[pygame.K_UP]
        down = key_presses[pygame.K_DOWN]

        # time period between two consecutive frames.
        time_delta = clock.get_time() / 1000.0

        # external control (camera bridge): Y of each player from 0.0 (top) to 1.0 (bottom),
        # None when that player is not detected, then the keyboard is used
        y1, y2 = external_control.posiciones() if external_control is not None else (None, None)

        # Update Paddle1
        if y1 is not None:
            paddle1.move_to(field_y(y1), time_delta, const.CAMERA_PADDLE_SPEED)
        else:
            paddle1.move(w, s, time_delta)
        paddle1.check_vertical_bounds(height)

        # Update Paddle2
        if y2 is not None:
            paddle2.move_to(field_y(y2), time_delta, const.CAMERA_PADDLE_SPEED)
        else:
            paddle2.move(up, down, time_delta)
        paddle2.check_vertical_bounds(height)

        puck.move(time_delta)

        # Hits the left goal!
        if inside_goal(0):
            pygame.mixer.Sound.play(goal_whistle)
            score2 += 1
            reset_game(speed, 1)

        # Hits the right goal!
        if inside_goal(1):
            pygame.mixer.Sound.play(goal_whistle)
            score1 += 1
            reset_game(speed, 2)

        # check puck collisions and update if necessary.
        puck.check_boundary(width, height)

        if puck.collision_paddle(paddle1):
            pygame.mixer.Sound.play(paddleHit)

        if puck.collision_paddle(paddle2):
            pygame.mixer.Sound.play(paddleHit)

        # collisions push the paddles, keep them on their fixed x and inside the field
        for paddle in (paddle1, paddle2):
            paddle.lock_x()
            paddle.check_vertical_bounds(height)

        draw_game()

        # the first player to reach SCORE_LIMIT goals wins, then a new game starts at 0 : 0
        if score1 == const.SCORE_LIMIT or score2 == const.SCORE_LIMIT:
            show_winner(const.PLAYER1_NAME if score1 == const.SCORE_LIMIT else const.PLAYER2_NAME)
            start_match()
            continue

        # refresh screen.
        pygame.display.flip()
        clock.tick(const.FPS)


def run(control=None):
    """Punto de entrada del juego de Air Hockey. `control` es el bridge de la cámara (opcional)."""
    global external_control
    external_control = control
    init()
    game_loop()

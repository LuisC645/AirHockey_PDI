""" All sizes in pixels and speeds in pixels per second """
FPS = 60

# Screen size
HEIGHT = 600
WIDTH = 1200

# Paddle
PADDLE_SIZE = 40
PADDLE_SPEED = 400
PADDLE_MASS = 2000

# Max speed of a paddle following a glove (camera control)
CAMERA_PADDLE_SPEED = 1500

# Distance from the screen corners to the small camera preview
CAMERA_VIEW_MARGIN = 20

# Paddles are locked on the x axis, this far from their goal line
PADDLE_GOAL_DISTANCE = 70

# Paddle 1 position (x is fixed, y is the start position).
PADDLE1X = PADDLE_GOAL_DISTANCE
PADDLE1Y = HEIGHT / 2

# Paddle 2 position (x is fixed, y is the start position).
PADDLE2X = WIDTH - PADDLE_GOAL_DISTANCE
PADDLE2Y = HEIGHT / 2

# Puck
PUCK_SIZE = 30
PUCK_SPEED = 450
PUCK_MASS = 500

# Goal Position
GOAL_WIDTH = 180
GOAL_Y1 = HEIGHT / 2 - GOAL_WIDTH / 2
GOAL_Y2 = HEIGHT / 2 + GOAL_WIDTH / 2

# Puck speed after each goal
GAME_SPEED = 450

# color
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Default playing field color
FIELD_COLOR = (255, 169, 119)

# Fonts (inside the assets folder)
FONT_REGULAR = "JetBrainsMono-Regular.ttf"
FONT_BOLD = "JetBrainsMono-Bold.ttf"

# Space between the screen edges and texts/buttons
MARGIN = 30

# Optional background image for the field (inside the assets folder), drawn below everything else.
# The first file that exists is used instead of FIELD_COLOR, stretched to WIDTH x HEIGHT (1200 x 600).
FIELD_IMAGES = ("field.png", "field.jpg", "field.jpeg")

# Optional images for the paddles and the puck (inside the assets folder). The first file that exists
# is used; it is scaled to the same size as the circle (paddle 80 x 80, puck 60 x 60) and cropped round,
# so it matches exactly the collision area.
PADDLE1_IMAGES = ("paddle1.png", "paddle1.jpg", "paddle1.jpeg")
PADDLE2_IMAGES = ("paddle2.png", "paddle2.jpg", "paddle2.jpeg")
PUCK_IMAGES = ("puck.png", "puck.jpg", "puck.jpeg")

# Width of the ring in the player color drawn around a paddle image (0 = no ring)
PADDLE_IMAGE_RING = 3

# Draw the white field lines also over the background image (False if the image has its own lines)
FIELD_LINES_OVER_IMAGE = False

# Score and names: text color and space around the text of its dark translucent panel
HUD_TEXT_COLOR = (255, 255, 255)
LABEL_PADDING = 12

# Player paddle colors
PLAYER1_COLOR = (255, 92, 92)
PLAYER2_COLOR = (100, 189, 219)

# Player names
PLAYER1_NAME = "Player 1"
PLAYER2_NAME = "Player 2"

# Countdown before the puck is released, in seconds
COUNTDOWN = 3

# Scoring
SCORE_LIMIT = 5     # goals needed to win a game
WINNER_DELAY = 3    # seconds the winner is shown before the next game

# Environment
FRICTION = 0.998
MAX_SPEED = 1500

# pause button
PAUSE_BUTTON_RADIUS = 32


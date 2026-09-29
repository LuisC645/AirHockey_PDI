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
PADDLE_GOAL_DISTANCE = 90

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

# Optional background image for the field (inside the assets folder).
# If the file exists it is used instead of the color, stretched to the window size.
FIELD_IMAGE = "field.png"

# Player paddle colors
PLAYER1_COLOR = (255, 92, 92)
PLAYER2_COLOR = (100, 189, 219)

# Player names
PLAYER1_NAME = "Player 1"
PLAYER2_NAME = "Player 2"

# Countdown before the puck is released, in seconds
COUNTDOWN = 3

# Scoring
SCORE_LIMIT = 5
ROUND_LIMIT = 2

# Environment
FRICTION = 0.998
MAX_SPEED = 1500

# pause button
PAUSE_BUTTON_RADIUS = 32


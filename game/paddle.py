import pygame
import math
from . import constants as const


class Paddle:
    """Paddle locked on the x axis: it only moves up and down in front of its goal."""

    def __init__(self, x, y):
        self.home_x = x  # fixed x position
        self.home_y = y  # start y position
        self.x = x
        self.y = y
        self.radius = const.PADDLE_SIZE
        self.speed = const.PADDLE_SPEED
        self.mass = const.PADDLE_MASS
        self.angle = 0

    def check_vertical_bounds(self, height):
        # top
        if self.y - self.radius <= 0:
            self.y = self.radius
        # bottom
        elif self.y + self.radius > height:
            self.y = height - self.radius

    def lock_x(self):
        """Puts the paddle back on its fixed x (collisions with the puck can push it)."""
        self.x = self.home_x

    def move(self, up, down, time_delta):
        """Moves the paddle only on the y axis."""
        old_y = self.y
        self.y += (down - up) * self.speed * time_delta
        self.angle = math.atan2(self.y - old_y, 0)

    def move_to(self, target_y, time_delta, max_speed):
        """Moves towards target_y (only on the y axis) without going faster than max_speed."""
        old_y = self.y
        step = max_speed * time_delta
        self.y += max(-step, min(step, target_y - self.y))
        self.angle = math.atan2(self.y - old_y, 0)

    def draw(self, screen, color):
        position = (int(self.x), int(self.y))

        pygame.draw.circle(screen, color, position, self.radius, 0)
        pygame.draw.circle(screen, (0, 0, 0), position, self.radius, 2)
        pygame.draw.circle(screen, (0, 0, 0), position, self.radius - 5, 2)
        pygame.draw.circle(screen, (0, 0, 0), position, self.radius - 10, 2)

    def reset(self):
        """Back to the start position."""
        self.x = self.home_x
        self.y = self.home_y

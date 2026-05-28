import pygame
import random
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT, RED, WHITE


class Ball:
    def __init__(self, x, y):
        self.radius = 7
        self.x = x
        self.y = y
        self.speed_x = random.choice([-4, 4])
        self.speed_y = -5
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius,
                                self.radius * 2, self.radius * 2)
        self.active = True

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.rect.center = (self.x, self.y)

        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.speed_x = -self.speed_x
        if self.rect.top <= 0:
            self.speed_y = -self.speed_y

    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 2)

    def is_off_screen(self):
        return self.rect.bottom >= SCREEN_HEIGHT

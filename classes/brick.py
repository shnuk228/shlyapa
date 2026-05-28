import pygame
from .constants import ORANGE, YELLOW, WHITE


class Brick:
    def __init__(self, x, y, color, strength=1, special=False):
        self.width = 70
        self.height = 22
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = color
        self.strength = strength
        self.special = special

    def hit(self):
        self.strength -= 1
        if self.strength == 2:
            self.color = ORANGE
        elif self.strength == 1:
            self.color = YELLOW
        return self.strength == 0

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        if self.strength > 1:
            font = pygame.font.Font(None, 18)
            text = font.render('●' * self.strength, True, WHITE)
            screen.blit(text, (self.rect.centerx - 10, self.rect.centery - 8))

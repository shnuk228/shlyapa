import pygame
from .constants import BONUS_EXTRA_LIFE, BONUS_MULTI_BALL, BONUS_BIG_PADDLE, RED, GREEN, BLUE, WHITE


class Bonus:
    def __init__(self, x, y, bonus_type):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.type = bonus_type
        self.speed_y = 3
        self.active = True

    def update(self):
        self.rect.y += self.speed_y

    def draw(self, screen):
        color = {
            BONUS_EXTRA_LIFE: RED,
            BONUS_MULTI_BALL: GREEN,
            BONUS_BIG_PADDLE: BLUE,
        }.get(self.type, WHITE)

        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)

        font = pygame.font.Font(None, 16)
        symbol = {
            BONUS_EXTRA_LIFE: '+1',
            BONUS_MULTI_BALL: '3x',
            BONUS_BIG_PADDLE: '⇔',
        }.get(self.type, '?')
        text = font.render(symbol, True, WHITE)
        screen.blit(text, (self.rect.x + 2, self.rect.y + 2))

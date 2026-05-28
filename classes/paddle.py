import pygame
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLUE, CYAN, WHITE


class Paddle:
    def __init__(self, width=120):
        self.normal_width = 120
        self.big_width = 180
        self.width = width
        self.height = 15
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = SCREEN_HEIGHT - self.height - 30
        self.speed = 8
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.big_paddle_timer = 0

    def move(self, direction):
        if direction == 'left' and self.rect.left > 0:
            self.rect.x -= self.speed
        elif direction == 'right' and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

    def make_big(self, duration=1800):
        if self.width == self.normal_width:
            self.width = self.big_width
            self.big_paddle_timer = duration
            self.rect.width = self.width
            if self.rect.right > SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH

    def update(self):
        if self.big_paddle_timer > 0:
            self.big_paddle_timer -= 1
            if self.big_paddle_timer <= 0:
                self.width = self.normal_width
                self.rect.width = self.width
                if self.rect.right > SCREEN_WIDTH:
                    self.rect.right = SCREEN_WIDTH

    def draw(self, screen):
        color = BLUE if self.big_paddle_timer > 0 else CYAN
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        if self.big_paddle_timer > 0:
            font = pygame.font.Font(None, 20)
            seconds = self.big_paddle_timer // 60
            text = font.render(str(seconds), True, WHITE)
            screen.blit(text, (self.rect.centerx - 10, self.rect.centery - 10))

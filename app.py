import pygame
import sys

# Инициализация Pygame
pygame.init()

# Константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)

# Класс платформы
class Paddle:
    def __init__(self):
        self.width = 120
        self.height = 15
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = SCREEN_HEIGHT - self.height - 30
        self.speed = 8
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def move(self, direction):
        if direction == 'left' and self.rect.left > 0:
            self.rect.x -= self.speed
        elif direction == 'right' and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
    
    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)

# Класс мяча
class Ball:
    def __init__(self):
        self.radius = 8
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.speed_x = 5
        self.speed_y = -5
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, 
                                self.radius * 2, self.radius * 2)
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.rect.center = (self.x, self.y)
        
        # Столкновение со стенами
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.speed_x = -self.speed_x
        if self.rect.top <= 0:
            self.speed_y = -self.speed_y
    
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 2)
    
    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.speed_x = 5
        self.speed_y = -5
        self.rect.center = (self.x, self.y)

# Класс кирпича (исправленный)
class Brick:
    def __init__(self, x, y, color, strength=1):
        self.width = 75
        self.height = 20
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = color
        self.strength = strength
    
    def hit(self):
        self.strength -= 1
        if self.strength == 2:
            self.color = ORANGE
        elif self.strength == 1:
            self.color = YELLOW
        return self.strength == 0
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 1)
        if self.strength > 1:
            font = pygame.font.Font(None, 20)
            text = font.render('★' * self.strength, True, WHITE)
            screen.blit(text, (self.rect.centerx - 10, self.rect.centery - 10))

# Главный класс игры
class Arkanoid:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Арканоид")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Создание объектов
        self.paddle = Paddle()
        self.ball = Ball()
        self.bricks = []
        self.score = 0
        self.lives = 3
        self.running = True
        self.paused = False
        self.game_over = False
        
        self.create_bricks()
    
    def create_bricks(self):
        """Создание сетки кирпичей"""
        colors = [GREEN, BLUE, ORANGE, RED]
        start_x = 20
        start_y = 50
        brick_width = 75
        brick_height = 20
        spacing = 5
        
        for row in range(5):
            for col in range(9):
                x = start_x + col * (brick_width + spacing)
                y = start_y + row * (brick_height + spacing)
                strength = 3 if row < 1 else 2 if row < 3 else 1
                color = colors[min(row, 3)]
                brick = Brick(x, y, color, strength)
                self.bricks.append(brick)
    
    def handle_collisions(self):
        # Столкновение с платформой
        if self.ball.rect.colliderect(self.paddle.rect):
            # Изменение направления в зависимости от места удара
            hit_pos = (self.ball.rect.centerx - self.paddle.rect.left) / self.paddle.width
            self.ball.speed_x = (hit_pos - 0.5) * 10
            self.ball.speed_y = -abs(self.ball.speed_y)
        
        # Столкновение с кирпичами
        for brick in self.bricks[:]:
            if self.ball.rect.colliderect(brick.rect):
                self.ball.speed_y = -self.ball.speed_y
                if brick.hit():
                    self.bricks.remove(brick)
                    self.score += 10
                break
    
    def update(self):
        if self.paused or self.game_over:
            return
        
        self.ball.update()
        
        # Проверка выхода мяча за нижнюю границу
        if self.ball.rect.bottom >= SCREEN_HEIGHT:
            self.lives -= 1
            if self.lives > 0:
                self.ball.reset()
                self.paddle = Paddle()
            else:
                self.game_over = True
        
        self.handle_collisions()
        
        # Проверка победы
        if len(self.bricks) == 0:
            self.game_over = True
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Отрисовка объектов
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        
        for brick in self.bricks:
            brick.draw(self.screen)
        
        # Отображение счета и жизней
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        self.screen.blit(lives_text, (SCREEN_WIDTH - 120, 10))
        
        # Отображение паузы
        if self.paused:
            pause_text = self.font.render("PAUSED", True, WHITE)
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(pause_text, text_rect)
        
        # Отображение Game Over
        if self.game_over:
            if len(self.bricks) == 0:
                message = "YOU WIN!"
            else:
                message = "GAME OVER"
            game_over_text = self.font.render(message, True, WHITE)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(game_over_text, text_rect)
            
            restart_text = self.small_font.render("Press R to restart or ESC to quit", True, WHITE)
            text_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(restart_text, text_rect)
        
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_r and self.game_over:
                    # Перезапуск игры
                    self.__init__()
        
        # Управление платформой
        if not self.paused and not self.game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.paddle.move('left')
            if keys[pygame.K_RIGHT]:
                self.paddle.move('right')
        
        return True
    
    def run(self):
        while self.running:
            self.running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# Запуск игры
if __name__ == "__main__":
    game = Arkanoid()
    game.run()
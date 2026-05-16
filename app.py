import pygame
import sys
import json
import random
import math
import os

# Инициализация Pygame
pygame.init()

# Константы
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# Типы бонусов
BONUS_EXTRA_LIFE = 1
BONUS_MULTI_BALL = 2
BONUS_BIG_PADDLE = 3

# Класс бонуса
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
            BONUS_BIG_PADDLE: BLUE
        }.get(self.type, WHITE)
        
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        # Рисуем символ бонуса
        font = pygame.font.Font(None, 16)
        symbol = {
            BONUS_EXTRA_LIFE: '+1',
            BONUS_MULTI_BALL: '3x',
            BONUS_BIG_PADDLE: '⇔'
        }.get(self.type, '?')
        text = font.render(symbol, True, WHITE)
        screen.blit(text, (self.rect.x + 2, self.rect.y + 2))

# Класс шарика
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
        
        # Столкновение со стенами
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.speed_x = -self.speed_x
        if self.rect.top <= 0:
            self.speed_y = -self.speed_y
    
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 2)
    
    def is_off_screen(self):
        return self.rect.bottom >= SCREEN_HEIGHT

# Класс платформы
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
    
    def make_big(self, duration=900):
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
            text = font.render(f"{self.big_paddle_timer // 60}", True, WHITE)
            screen.blit(text, (self.rect.centerx - 10, self.rect.centery - 10))

# Класс кирпича
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

# Класс меню
class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font_big = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.options = ["Начать игру", "Выбрать уровень", "Выход"]
        self.selected = 0
        self.select_level_mode = False
        self.available_levels = []
        
    def load_progress(self):
        try:
            with open('progress.json', 'r') as f:
                data = json.load(f)
                return data.get('unlocked_levels', [1])
        except:
            return [1]
    
    def draw(self, unlocked_levels):
        self.screen.fill(BLACK)
        
        # Заголовок
        title = self.font_big.render("АРКАНОИД", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        if not self.select_level_mode:
            # Главное меню
            for i, option in enumerate(self.options):
                color = YELLOW if i == self.selected else WHITE
                text = self.font_medium.render(option, True, color)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 70))
                self.screen.blit(text, text_rect)
            
            # Отображение прогресса
            progress_text = self.font_small.render(f"Доступно уровней: {len(unlocked_levels)}", True, GREEN)
            progress_rect = progress_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            self.screen.blit(progress_text, progress_rect)
        else:
            # Меню выбора уровня
            select_text = self.font_medium.render("Выберите уровень:", True, WHITE)
            select_rect = select_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(select_text, select_rect)
            
            # Отображение уровней
            cols = 5
            for i, level in enumerate(self.available_levels):
                row = i // cols
                col = i % cols
                x = 150 + col * 140
                y = 280 + row * 80
                
                is_unlocked = level in unlocked_levels
                color = GREEN if is_unlocked else GRAY
                
                pygame.draw.rect(self.screen, color, (x, y, 100, 50), 0, 10)
                pygame.draw.rect(self.screen, WHITE, (x, y, 100, 50), 2, 10)
                
                text = self.font_small.render(str(level), True, WHITE)
                text_rect = text.get_rect(center=(x + 50, y + 25))
                self.screen.blit(text, text_rect)
                
                if i == self.selected:
                    pygame.draw.rect(self.screen, YELLOW, (x - 5, y - 5, 110, 60), 3, 10)
            
            back_text = self.font_small.render("Нажмите ESC для возврата", True, WHITE)
            back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            self.screen.blit(back_text, back_rect)
        
        pygame.display.flip()
    
    def handle_events(self, unlocked_levels):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit', None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.select_level_mode:
                        self.select_level_mode = False
                        self.selected = 0
                        self.options = ["Начать игру", "Выбрать уровень", "Выход"]
                    else:
                        return 'quit', None
                
                if event.key == pygame.K_UP:
                    if self.select_level_mode:
                        self.selected = max(0, self.selected - 5)
                    else:
                        self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    if self.select_level_mode:
                        self.selected = min(len(self.available_levels) - 1, self.selected + 5)
                    else:
                        self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pygame.K_LEFT and self.select_level_mode:
                    self.selected = max(0, self.selected - 1)
                elif event.key == pygame.K_RIGHT and self.select_level_mode:
                    self.selected = min(len(self.available_levels) - 1, self.selected + 1)
                elif event.key == pygame.K_RETURN:
                    if self.select_level_mode:
                        selected_level = self.available_levels[self.selected]
                        if selected_level in unlocked_levels:
                            return 'play', selected_level
                    else:
                        if self.selected == 0:  # Начать игру
                            # Начинаем с последнего доступного уровня
                            return 'play', max(unlocked_levels)
                        elif self.selected == 1:  # Выбрать уровень
                            self.select_level_mode = True
                            self.available_levels = list(range(1, 11))
                            self.selected = 0
                        elif self.selected == 2:  # Выход
                            return 'quit', None
        return 'menu', None

# Основной класс игры
class Arkanoid:
    def __init__(self, start_level=1):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Арканоид")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Загрузка уровней
        self.load_levels()
        
        # Загрузка прогресса
        self.load_progress()
        
        self.current_level = start_level
        self.score = 0
        self.lives = 3
        self.running = True
        self.paused = False
        self.game_over = False
        self.level_complete = False
        
        # Инициализация игровых объектов
        self.init_game_objects()
        
    def load_levels(self):
        try:
            with open('levels.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.levels = data['levels']
        except FileNotFoundError:
            # Создание уровней по умолчанию
            self.levels = []
            for i in range(1, 11):
                self.levels.append({
                    "id": i,
                    "rows": min(3 + i // 2, 8),
                    "cols": min(8 + i // 2, 15),
                    "bricks_layout": "classic",
                    "description": f"Уровень {i}"
                })
    
    def load_progress(self):
        try:
            with open('progress.json', 'r') as f:
                data = json.load(f)
                self.unlocked_levels = data.get('unlocked_levels', [1])
                self.high_scores = data.get('high_scores', {})
        except:
            self.unlocked_levels = [1]
            self.high_scores = {}
    
    def save_progress(self):
        data = {
            'unlocked_levels': self.unlocked_levels,
            'high_scores': self.high_scores
        }
        with open('progress.json', 'w') as f:
            json.dump(data, f, indent=4)
    
    def init_game_objects(self):
        self.paddle = Paddle()
        self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
        self.bricks = []
        self.bonuses = []
        self.create_bricks()
        
        # Подсчет количества бонусов
        total_bricks = len(self.bricks)
        self.bonus_count = max(1, total_bricks // 5)
        self.bonuses_spawned = 0
    
    def create_bricks(self):
        """Создание кирпичей в зависимости от уровня"""
        level_data = self.levels[self.current_level - 1]
        rows = level_data['rows']
        cols = level_data['cols']
        layout = level_data['bricks_layout']
        
        brick_width = 70
        brick_height = 22
        start_x = (SCREEN_WIDTH - (cols * (brick_width + 5))) // 2
        start_y = 60
        spacing = 5
        
        colors = [RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE, PINK]
        
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (brick_width + spacing)
                y = start_y + row * (brick_height + spacing)
                
                # Разные раскладки кирпичей
                if layout == "classic":
                    strength = 1
                    color = colors[row % len(colors)]
                
                elif layout == "pyramid":
                    if col < rows - row - 1 or col > cols - (rows - row):
                        continue
                    strength = 1
                    color = colors[row % len(colors)]
                
                elif layout == "zigzag":
                    strength = 2 if (row + col) % 3 == 0 else 1
                    color = colors[(row + col) % len(colors)]
                
                elif layout == "double":
                    strength = 3 if row < 2 else 1
                    color = colors[row % len(colors)]
                
                elif layout == "rainbow":
                    strength = 1
                    color = colors[(row + col) % len(colors)]
                
                elif layout == "checkerboard":
                    if (row + col) % 2 == 0:
                        continue
                    strength = 1
                    color = colors[row % len(colors)]
                
                elif layout == "castle":
                    if col == 0 or col == cols - 1 or row == rows - 1:
                        strength = 3
                    else:
                        strength = 1
                    color = colors[row % len(colors)]
                
                elif layout == "spiral":
                    if min(row, col, rows - row - 1, cols - col - 1) % 2 == 0:
                        strength = 2
                    else:
                        strength = 1
                    color = colors[row % len(colors)]
                
                elif layout == "dense":
                    strength = min(3, 1 + row // 2)
                    color = colors[strength - 1]
                
                else:  # boss
                    strength = 3
                    color = PURPLE
                
                brick = Brick(x, y, color, strength)
                self.bricks.append(brick)
    
    def spawn_bonus(self, x, y):
        """Создание бонуса при разрушении кирпича"""
        if self.bonuses_spawned >= self.bonus_count:
            return
        
        # Редкость бонусов
        rand = random.random()
        if rand < 0.15:  # +1 жизнь (редкий)
            bonus_type = BONUS_EXTRA_LIFE
        elif rand < 0.4:  # +3 шарика (средний)
            bonus_type = BONUS_MULTI_BALL
        else:  # Увеличение платформы (частый)
            bonus_type = BONUS_BIG_PADDLE
        
        self.bonuses.append(Bonus(x, y, bonus_type))
        self.bonuses_spawned += 1
    
    def apply_bonus(self, bonus):
        """Применение эффекта бонуса"""
        if bonus.type == BONUS_EXTRA_LIFE:
            self.lives += 1
        elif bonus.type == BONUS_MULTI_BALL:
            # Добавляем 3 новых шарика
            for _ in range(3):
                new_ball = Ball(self.paddle.rect.centerx, self.paddle.rect.top - 10)
                new_ball.speed_x = random.uniform(-5, 5)
                new_ball.speed_y = -abs(new_ball.speed_y)
                self.balls.append(new_ball)
        elif bonus.type == BONUS_BIG_PADDLE:
            self.paddle.make_big()
    
    def handle_collisions(self):
        # Столкновение шариков с платформой
        for ball in self.balls[:]:
            if ball.rect.colliderect(self.paddle.rect):
                # Изменение направления в зависимости от места удара
                hit_pos = (ball.rect.centerx - self.paddle.rect.left) / self.paddle.width
                ball.speed_x = (hit_pos - 0.5) * 8
                ball.speed_y = -abs(ball.speed_y)
        
        # Столкновение шариков с кирпичами
        for ball in self.balls[:]:
            for brick in self.bricks[:]:
                if ball.rect.colliderect(brick.rect):
                    ball.speed_y = -ball.speed_y
                    if brick.hit():
                        self.bricks.remove(brick)
                        self.score += 10
                        # Создание бонуса
                        self.spawn_bonus(brick.rect.centerx, brick.rect.centery)
                    break
        
        # Столкновение бонусов с платформой
        for bonus in self.bonuses[:]:
            if bonus.rect.colliderect(self.paddle.rect):
                self.apply_bonus(bonus)
                self.bonuses.remove(bonus)
    
    def update(self):
        if self.paused or self.game_over or self.level_complete:
            return
        
        # Обновление платформы
        self.paddle.update()
        
        # Обновление шариков
        for ball in self.balls[:]:
            ball.update()
        
        # Обновление бонусов
        for bonus in self.bonuses[:]:
            bonus.update()
            if bonus.rect.top > SCREEN_HEIGHT:
                self.bonuses.remove(bonus)
        
        # Проверка выхода шариков
        lost_balls = [ball for ball in self.balls if ball.is_off_screen()]
        for ball in lost_balls:
            self.balls.remove(ball)
        
        # Если все шарики потеряны
        if len(self.balls) == 0:
            self.lives -= 1
            if self.lives > 0:
                # Создаем один шарик
                self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
                self.paddle = Paddle()  # Сброс платформы
            else:
                self.game_over = True
        
        self.handle_collisions()
        
        # Проверка победы на уровне
        if len(self.bricks) == 0:
            self.level_complete = True
            
            # Сохранение прогресса
            next_level = self.current_level + 1
            if next_level <= 10 and next_level not in self.unlocked_levels:
                self.unlocked_levels.append(next_level)
                self.save_progress()
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Отрисовка объектов
        self.paddle.draw(self.screen)
        
        for ball in self.balls:
            ball.draw(self.screen)
        
        for brick in self.bricks:
            brick.draw(self.screen)
        
        for bonus in self.bonuses:
            bonus.draw(self.screen)
        
        # Информация об уровне
        level_text = self.font.render(f"Уровень: {self.current_level}", True, WHITE)
        self.screen.blit(level_text, (10, 10))
        
        # Отображение счета
        score_text = self.font.render(f"Счет: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 50))
        
        # Отображение жизней
        lives_text = self.font.render(f"Жизни: {self.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 90))
        
        # Отображение количества шариков
        balls_text = self.small_font.render(f"Шарики: {len(self.balls)}", True, WHITE)
        self.screen.blit(balls_text, (10, 130))
        
        # Отображение оставшихся бонусов
        bonuses_left = self.bonus_count - self.bonuses_spawned
        bonuses_text = self.small_font.render(f"Бонусов осталось: {bonuses_left}", True, YELLOW)
        self.screen.blit(bonuses_text, (10, 160))
        
        # Отображение паузы
        if self.paused:
            pause_text = self.font.render("ПАУЗА", True, WHITE)
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(pause_text, text_rect)
        
        # Отображение завершения уровня
        if self.level_complete:
            complete_text = self.font.render("УРОВЕНЬ ПРОЙДЕН!", True, GREEN)
            text_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            self.screen.blit(complete_text, text_rect)
            
            continue_text = self.small_font.render("Нажмите ENTER для продолжения", True, WHITE)
            text_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(continue_text, text_rect)
        
        # Отображение Game Over
        if self.game_over:
            game_over_text = self.font.render("ИГРА ОКОНЧЕНА", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            self.screen.blit(game_over_text, text_rect)
            
            restart_text = self.small_font.render("Нажмите R для перезапуска или ESC для выхода в меню", True, WHITE)
            text_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
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
                    # Перезапуск игры с текущего уровня
                    self.__init__(self.current_level)
                elif event.key == pygame.K_RETURN and self.level_complete:
                    # Переход на следующий уровень
                    if self.current_level < 10:
                        self.current_level += 1
                        self.init_game_objects()
                        self.level_complete = False
                    else:
                        # Игра пройдена
                        self.game_over = True
        
        # Управление платформой
        if not self.paused and not self.game_over and not self.level_complete:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.paddle.move('left')
            if keys[pygame.K_RIGHT]:
                self.paddle.move('right')
        
        return True
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        return self.score

# Главная функция
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Арканоид")
    
    menu = Menu(screen)
    
    while True:
        unlocked_levels = menu.load_progress()
        menu.draw(unlocked_levels)
        action, level = menu.handle_events(unlocked_levels)
        
        if action == 'quit':
            pygame.quit()
            sys.exit()
        elif action == 'play':
            game = Arkanoid(level)
            game.run()
            # Сохраняем прогресс после игры
            game.save_progress()

if __name__ == "__main__":
    main()
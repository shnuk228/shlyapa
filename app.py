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
                unlocked_levels = data.get('unlocked_levels', [1])
                high_scores = data.get('high_scores', {})
                tutorial_shown = data.get('tutorial_shown', False)
                return unlocked_levels, high_scores, tutorial_shown
        except:
            return [1], {}, False
    
    def save_tutorial_shown(self):
        try:
            with open('progress.json', 'r') as f:
                data = json.load(f)
        except:
            data = {'unlocked_levels': [1], 'high_scores': {}, 'tutorial_shown': False}
        
        data['tutorial_shown'] = True
        with open('progress.json', 'w') as f:
            json.dump(data, f, indent=4)
    
    def draw(self, unlocked_levels, high_scores):
        self.screen.fill(BLACK)
        
        # Заголовок
        title = self.font_big.render("АРКАНОИД", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
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
            progress_rect = progress_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
            self.screen.blit(progress_text, progress_rect)
            
            # Отображение общего рекорда
            if high_scores:
                total_score = sum(high_scores.values())
                total_text = self.font_small.render(f"Общий рекорд: {total_score}", True, YELLOW)
                total_rect = total_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
                self.screen.blit(total_text, total_rect)
        else:
            # Меню выбора уровня
            select_text = self.font_medium.render("Выберите уровень:", True, WHITE)
            select_rect = select_text.get_rect(center=(SCREEN_WIDTH // 2, 160))
            self.screen.blit(select_text, select_rect)
            
            # Отображение уровней
            cols = 5
            for i, level in enumerate(self.available_levels):
                row = i // cols
                col = i % cols
                x = 130 + col * 150
                y = 230 + row * 100
                
                is_unlocked = level in unlocked_levels
                bg_color = GREEN if is_unlocked else GRAY
                
                # Рисуем кнопку уровня
                pygame.draw.rect(self.screen, bg_color, (x, y, 120, 70), 0, 10)
                pygame.draw.rect(self.screen, WHITE, (x, y, 120, 70), 2, 10)
                
                # Номер уровня
                text = self.font_medium.render(str(level), True, WHITE)
                text_rect = text.get_rect(center=(x + 60, y + 30))
                self.screen.blit(text, text_rect)
                
                # Рекорд уровня
                if str(level) in high_scores:
                    score_text = self.font_small.render(f"{high_scores[str(level)]}", True, YELLOW)
                    score_rect = score_text.get_rect(center=(x + 60, y + 55))
                    self.screen.blit(score_text, score_rect)
                
                if i == self.selected:
                    pygame.draw.rect(self.screen, YELLOW, (x - 5, y - 5, 130, 80), 3, 10)
            
            back_text = self.font_small.render("Нажмите ESC для возврата", True, WHITE)
            back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
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
                        if self.selected == 0:
                            return 'play', max(unlocked_levels)
                        elif self.selected == 1:
                            self.select_level_mode = True
                            self.available_levels = list(range(1, 11))
                            self.selected = 0
                        elif self.selected == 2:
                            return 'quit', None
        return 'menu', None

# Основной класс игры
class Arkanoid:
    def __init__(self, start_level=1, tutorial_mode=False):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Арканоид")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        
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
        
        # Обучающие элементы
        self.tutorial_mode = tutorial_mode
        self.tutorial_step = 0  # 0 - обучение движению, 1 - обучение бонусу
        self.tutorial_waiting_for_move = False
        self.tutorial_bonus_caught = False
        self.tutorial_message_timer = 0
        self.tutorial_ball_active = False
        self.tutorial_bonus_fall_timer = 0
        self.tutorial_bonus_respawn_delay = 60
        
        # Защита для новичков
        self.noob_protection_active = False
        
        # Инициализация игровых объектов
        self.init_game_objects()
        
        # Если обучение, запускаем первый шаг
        if self.tutorial_mode:
            self.tutorial_waiting_for_move = True
            self.tutorial_ball_active = False
            self.balls = []  # Шарика нет во время обучения
    
    def load_levels(self):
        try:
            with open('levels.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.levels = data['levels']
        except FileNotFoundError:
            self.levels = []
            for i in range(1, 11):
                self.levels.append({
                    "id": i,
                    "name": f"Уровень {i}",
                    "layout": [[1] * (8 + i//2) for _ in range(3 + i//3)]
                })
    
    def load_progress(self):
        try:
            with open('progress.json', 'r') as f:
                data = json.load(f)
                self.unlocked_levels = data.get('unlocked_levels', [1])
                self.high_scores = data.get('high_scores', {})
                if isinstance(self.high_scores, dict):
                    self.high_scores = {str(k): v for k, v in self.high_scores.items()}
        except:
            self.unlocked_levels = [1]
            self.high_scores = {}
    
    def save_progress(self):
        current_level_str = str(self.current_level)
        if current_level_str not in self.high_scores or self.score > self.high_scores[current_level_str]:
            self.high_scores[current_level_str] = self.score
            self.save_progress_callback()
    
    def save_progress_callback(self):
        data = {
            'unlocked_levels': self.unlocked_levels,
            'high_scores': self.high_scores
        }
        with open('progress.json', 'w') as f:
            json.dump(data, f, indent=4)
    
    def spawn_tutorial_bonus(self):
        if len(self.bricks) > 0:
            random_brick = random.choice(self.bricks)
            bonus = Bonus(random_brick.rect.centerx, random_brick.rect.centery, BONUS_BIG_PADDLE)
            bonus.speed_y = 2
            self.bonuses.append(bonus)
            self.tutorial_bonus_fall_timer = 0
    
    def init_game_objects(self):
        self.paddle = Paddle()
        
        if not self.tutorial_mode or self.tutorial_ball_active:
            self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
        else:
            self.balls = []
            
        self.bricks = []
        self.bonuses = []
        self.create_bricks()
        
        total_bricks = len(self.bricks)
        self.bonus_count = max(1, total_bricks // 5)
        
        if total_bricks > 0:
            step = total_bricks / self.bonus_count
            self.bonus_brick_indices = [int(i * step) for i in range(self.bonus_count)]
        else:
            self.bonus_brick_indices = []
        
        self.bricks_hit_count = 0
    
    def create_bricks(self):
        level_data = self.levels[self.current_level - 1]
        layout = level_data.get('layout', [])
        
        if not layout:
            return
        
        rows = len(layout)
        cols = len(layout[0]) if rows > 0 else 0
        
        brick_width = 70
        brick_height = 22
        total_width = cols * (brick_width + 5)
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = 60
        spacing = 5
        
        strength_colors = {
            1: GREEN,
            2: ORANGE,
            3: RED
        }
        
        for row in range(rows):
            for col in range(cols):
                strength = layout[row][col]
                if strength == 0:
                    continue
                strength = max(1, min(3, strength))
                x = start_x + col * (brick_width + spacing)
                y = start_y + row * (brick_height + spacing)
                color = strength_colors[strength]
                brick = Brick(x, y, color, strength)
                self.bricks.append(brick)
    
    def spawn_bonus(self, x, y, brick_index):
        if brick_index in self.bonus_brick_indices:
            bonus_index = self.bonus_brick_indices.index(brick_index)
            bonus_type_index = bonus_index % 3
            if bonus_type_index == 0:
                bonus_type = BONUS_BIG_PADDLE
            elif bonus_type_index == 1:
                bonus_type = BONUS_MULTI_BALL
            else:
                bonus_type = BONUS_EXTRA_LIFE
            self.bonuses.append(Bonus(x, y, bonus_type))
            return True
        return False
    
    def apply_bonus(self, bonus):
        if self.tutorial_mode and self.tutorial_step == 1:
            self.tutorial_bonus_caught = True
            self.tutorial_step = 2
            self.tutorial_message_timer = 180
            self.tutorial_ball_active = True
            if len(self.balls) == 0:
                self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
            return
        
        if bonus.type == BONUS_EXTRA_LIFE:
            self.lives += 1
        elif bonus.type == BONUS_MULTI_BALL:
            for _ in range(3):
                new_ball = Ball(self.paddle.rect.centerx, self.paddle.rect.top - 10)
                new_ball.speed_x = random.uniform(-5, 5)
                new_ball.speed_y = -abs(new_ball.speed_y)
                self.balls.append(new_ball)
        elif bonus.type == BONUS_BIG_PADDLE:
            self.paddle.make_big()
    
    def handle_collisions(self):
        if self.tutorial_mode and not self.tutorial_ball_active:
            for bonus in self.bonuses[:]:
                if bonus.rect.colliderect(self.paddle.rect):
                    self.apply_bonus(bonus)
                    self.bonuses.remove(bonus)
                elif bonus.rect.top > SCREEN_HEIGHT:
                    self.bonuses.remove(bonus)
            return
        
        for ball in self.balls[:]:
            if ball.rect.colliderect(self.paddle.rect):
                hit_pos = (ball.rect.centerx - self.paddle.rect.left) / self.paddle.width
                ball.speed_x = (hit_pos - 0.5) * 8
                ball.speed_y = -abs(ball.speed_y)
        
        for ball in self.balls[:]:
            for brick in self.bricks[:]:
                if ball.rect.colliderect(brick.rect):
                    ball.speed_y = -ball.speed_y
                    if brick.hit():
                        brick_x = brick.rect.centerx
                        brick_y = brick.rect.centery
                        current_brick_index = self.bricks_hit_count
                        self.bricks.remove(brick)
                        self.score += 10
                        self.spawn_bonus(brick_x, brick_y, current_brick_index)
                        self.bricks_hit_count += 1
                    break
        
        for bonus in self.bonuses[:]:
            if bonus.rect.colliderect(self.paddle.rect):
                self.apply_bonus(bonus)
                self.bonuses.remove(bonus)
            elif bonus.rect.top > SCREEN_HEIGHT:
                self.bonuses.remove(bonus)
    
    def update(self):
        if self.paused or self.game_over or self.level_complete:
            return
        
        if self.tutorial_message_timer > 0:
            self.tutorial_message_timer -= 1
        
        self.paddle.update()
        
        # Обновление шариков
        if not self.tutorial_mode or self.tutorial_ball_active:
            for ball in self.balls[:]:
                ball.update()
                
                # Защита для новичков - отскок от низа ТОЛЬКО когда жизни = 0 и уровень = 1
                if self.current_level == 1 and self.lives == 0 and ball.rect.bottom >= SCREEN_HEIGHT:
                    ball.speed_y = -abs(ball.speed_y)
                    ball.y = SCREEN_HEIGHT - ball.radius - 1
        
        for bonus in self.bonuses[:]:
            bonus.update()
        
        # Обучающий режим
        if self.tutorial_mode and self.tutorial_step == 1 and not self.tutorial_bonus_caught:
            if len(self.bonuses) == 0:
                self.tutorial_bonus_fall_timer += 1
                if self.tutorial_bonus_fall_timer >= self.tutorial_bonus_respawn_delay:
                    self.spawn_tutorial_bonus()
            else:
                self.tutorial_bonus_fall_timer = 0
        
        # Проверка выхода шариков (только если игра активна)
        if not self.tutorial_mode or self.tutorial_ball_active:
            lost_balls = [ball for ball in self.balls if ball.is_off_screen()]
            for ball in lost_balls:
                self.balls.remove(ball)
        
        # Обработка потери всех шариков
        if len(self.balls) == 0 and (not self.tutorial_mode or self.tutorial_ball_active):
            if self.current_level == 1 and self.lives == 0:
                # Защита уже активна, но если шариков нет - создаём новый
                self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
                # Платформу НЕ сбрасываем в центр
            elif self.current_level == 1 and self.lives > 0:
                # На первом уровне с жизнями - тратим жизнь
                self.lives -= 1
                if self.lives > 0:
                    self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
                    # Платформу НЕ сбрасываем в центр
                else:
                    # Жизни стали равны 0 - активируем защиту
                    self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
                    # Платформу НЕ сбрасываем в центр
            else:
                # Для других уровней (не первый)
                self.lives -= 1
                if self.lives > 0:
                    self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
                    # Платформу НЕ сбрасываем в центр
                else:
                    self.game_over = True
        
        self.handle_collisions()
        
        if len(self.bricks) == 0:
            self.level_complete = True
            self.save_progress()
            next_level = self.current_level + 1
            if next_level <= 10 and next_level not in self.unlocked_levels:
                self.unlocked_levels.append(next_level)
                self.save_progress_callback()
    
    def draw_tutorial(self):
        if self.tutorial_mode:
            if self.tutorial_step == 0 and self.tutorial_waiting_for_move:
                text_bg = pygame.Surface((SCREEN_WIDTH, 200))
                text_bg.set_alpha(180)
                text_bg.fill(BLACK)
                text_bg_rect = text_bg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(text_bg, text_bg_rect)
                
                text1 = self.big_font.render("ОБУЧЕНИЕ", True, YELLOW)
                text1_rect = text1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
                self.screen.blit(text1, text1_rect)
                
                text2 = self.font.render("Чтобы двигать платформу, используйте стрелки", True, WHITE)
                text2_rect = text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10))
                self.screen.blit(text2, text2_rect)
                
                left_arrow = self.big_font.render("←", True, CYAN)
                right_arrow = self.big_font.render("→", True, CYAN)
                self.screen.blit(left_arrow, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 30))
                self.screen.blit(right_arrow, (SCREEN_WIDTH // 2 + 80, SCREEN_HEIGHT // 2 + 30))
                
                text3 = self.small_font.render("Нажмите любую стрелку, чтобы продолжить", True, GREEN)
                text3_rect = text3.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
                self.screen.blit(text3, text3_rect)
                
            elif self.tutorial_step == 1 and not self.tutorial_bonus_caught:
                text_bg = pygame.Surface((SCREEN_WIDTH, 150))
                text_bg.set_alpha(180)
                text_bg.fill(BLACK)
                text_bg_rect = text_bg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(text_bg, text_bg_rect)
                
                text1 = self.font.render("Отлично! Теперь поймай падающий бонус!", True, YELLOW)
                text1_rect = text1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
                self.screen.blit(text1, text1_rect)
                
                text2 = self.small_font.render("Передвинь платформу под бонус", True, WHITE)
                text2_rect = text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(text2, text2_rect)
                
                if len(self.bonuses) == 0:
                    text3 = self.small_font.render("Бонус скоро появится...", True, CYAN)
                    text3_rect = text3.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
                    self.screen.blit(text3, text3_rect)
                else:
                    text3 = self.small_font.render("Лови бонус платформой!", True, GREEN)
                    text3_rect = text3.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
                    self.screen.blit(text3, text3_rect)
            
            elif self.tutorial_step == 2 and self.tutorial_message_timer > 0:
                text_bg = pygame.Surface((SCREEN_WIDTH, 100))
                text_bg.set_alpha(180)
                text_bg.fill(BLACK)
                text_bg_rect = text_bg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(text_bg, text_bg_rect)
                
                text = self.big_font.render("Отлично! Теперь играй!", True, GREEN)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(text, text_rect)
    
    def draw(self):
        self.screen.fill(BLACK)
        
        self.paddle.draw(self.screen)
        
        for ball in self.balls:
            ball.draw(self.screen)
        
        for brick in self.bricks:
            brick.draw(self.screen)
        
        for bonus in self.bonuses:
            bonus.draw(self.screen)
        
        level_text = self.font.render(f"Уровень: {self.current_level}", True, WHITE)
        self.screen.blit(level_text, (10, 10))
        
        current_level_str = str(self.current_level)
        if current_level_str in self.high_scores:
            record_text = self.small_font.render(f"Рекорд: {self.high_scores[current_level_str]}", True, YELLOW)
            self.screen.blit(record_text, (10, 45))
        
        score_text = self.font.render(f"Счет: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 80))
        
        lives_text = self.font.render(f"Жизни: {self.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 120))
        
        if not self.tutorial_mode or self.tutorial_ball_active:
            balls_text = self.small_font.render(f"Шарики: {len(self.balls)}", True, WHITE)
            self.screen.blit(balls_text, (10, 160))
        
        bonuses_text = self.small_font.render(f"Бонусов на уровне: {self.bonus_count}", True, GREEN)
        self.screen.blit(bonuses_text, (10, 190))
        
        if self.current_level == 1 and self.lives == 0:
            protect_text = self.small_font.render("РЕЖИМ ПОМОЩИ: шарик не падает", True, CYAN)
            self.screen.blit(protect_text, (SCREEN_WIDTH - 280, 10))
        
        if self.paused:
            pause_text = self.font.render("ПАУЗА", True, WHITE)
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(pause_text, text_rect)
        
        if self.level_complete:
            complete_text = self.font.render("УРОВЕНЬ ПРОЙДЕН!", True, GREEN)
            text_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            self.screen.blit(complete_text, text_rect)
            
            continue_text = self.small_font.render("Нажмите ENTER для продолжения", True, WHITE)
            text_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(continue_text, text_rect)
        
        if self.game_over:
            game_over_text = self.font.render("ИГРА ОКОНЧЕНА", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            self.screen.blit(game_over_text, text_rect)
            
            restart_text = self.small_font.render("Нажмите R для перезапуска или ESC для выхода в меню", True, WHITE)
            text_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(restart_text, text_rect)
        
        self.draw_tutorial()
        
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
                    self.__init__(self.current_level, self.tutorial_mode)
                elif event.key == pygame.K_RETURN and self.level_complete:
                    if self.current_level < 10:
                        self.current_level += 1
                        self.init_game_objects()
                        self.level_complete = False
                        self.noob_protection_active = False
                    else:
                        self.game_over = True
                
                if self.tutorial_mode and self.tutorial_step == 0 and self.tutorial_waiting_for_move:
                    if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                        self.tutorial_waiting_for_move = False
                        self.tutorial_step = 1
                        self.spawn_tutorial_bonus()
        
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
        unlocked_levels, high_scores, tutorial_shown = menu.load_progress()
        menu.draw(unlocked_levels, high_scores)
        action, level = menu.handle_events(unlocked_levels)
        
        if action == 'quit':
            pygame.quit()
            sys.exit()
        elif action == 'play':
            is_tutorial = (not tutorial_shown and level == 1)
            game = Arkanoid(level, is_tutorial)
            game.run()
            
            if is_tutorial and game.tutorial_bonus_caught:
                menu.save_tutorial_shown()

if __name__ == "__main__":
    main()
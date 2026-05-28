import pygame
import json
import random
import os
from .constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BLACK, WHITE, RED, GREEN, ORANGE, YELLOW, PURPLE, CYAN, GRAY, DARK_GRAY,
    BONUS_EXTRA_LIFE, BONUS_MULTI_BALL, BONUS_BIG_PADDLE, BONUS_BOTTOM_SHIELD,
    STORED_BONUS_NAMES, STORED_BONUS_COLORS,
    CONFIG_DIR,
)
from .utils import wrap_text
from .ball import Ball
from .paddle import Paddle
from .brick import Brick
from .bonus import Bonus


class Arkanoid:
    def __init__(self, start_level=1, tutorial_mode=False):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Арканоид")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)

        self.load_levels()
        self.load_progress()

        self.current_level = start_level
        self.score = 0
        self.lives = 3
        self.running = True
        self.paused = False
        self.game_over = False
        self.level_complete = False

        self.tutorial_mode = tutorial_mode
        self.tutorial_step = 0
        self.tutorial_waiting_for_move = False
        self.tutorial_bonus_caught = False
        self.tutorial_message_timer = 0
        self.tutorial_ball_active = False
        self.tutorial_bonus_fall_timer = 0
        self.tutorial_bonus_respawn_delay = 60

        self._quiz = None
        self.bottom_shield_timer = 0

        self.init_game_objects()

        if self.tutorial_mode:
            self.tutorial_waiting_for_move = True
            self.tutorial_ball_active = False
            self.balls = []

    def load_levels(self):
        try:
            with open(os.path.join(CONFIG_DIR, 'levels.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.levels = data['levels']
        except FileNotFoundError:
            self.levels = []
            for i in range(1, 11):
                self.levels.append({
                    "id": i,
                    "name": f"Уровень {i}",
                    "layout": [[1] * (8 + i // 2) for _ in range(3 + i // 3)],
                })

    def load_progress(self):
        try:
            with open(os.path.join(CONFIG_DIR, 'progress.json'), 'r') as f:
                data = json.load(f)
            self.unlocked_levels = data.get('unlocked_levels', [1])
            self.high_scores = data.get('high_scores', {})
            if isinstance(self.high_scores, dict):
                self.high_scores = {str(k): v for k, v in self.high_scores.items()}
            self.stored_bonuses = data.get('stored_bonuses', [])
            self.selected_topic = data.get('selected_topic', None)
            self.quiz_used_indices = data.get('quiz_used_indices', {})
        except:
            self.unlocked_levels = [1]
            self.high_scores = {}
            self.stored_bonuses = []
            self.selected_topic = None
            self.quiz_used_indices = {}

    def save_progress(self):
        current_level_str = str(self.current_level)
        if current_level_str not in self.high_scores or self.score > self.high_scores[current_level_str]:
            self.high_scores[current_level_str] = self.score
            self.save_progress_callback()

    def save_progress_callback(self):
        path = os.path.join(CONFIG_DIR, 'progress.json')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        data['unlocked_levels'] = self.unlocked_levels
        data['high_scores'] = self.high_scores
        data['stored_bonuses'] = self.stored_bonuses
        data['selected_topic'] = self.selected_topic
        data['quiz_used_indices'] = self.quiz_used_indices
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    # ── Накопленные бонусы ────────────────────────────────────────────────────

    def _use_stored_bonus(self, index):
        if index >= len(self.stored_bonuses):
            return
        bonus_type = self.stored_bonuses.pop(index)
        if bonus_type == BONUS_BIG_PADDLE:
            self.paddle.make_big()
        elif bonus_type == BONUS_MULTI_BALL:
            spawn_x = self.paddle.rect.centerx
            spawn_y = self.paddle.rect.top - 10
            for _ in range(3):
                b = Ball(spawn_x, spawn_y)
                b.speed_x = random.uniform(-5, 5)
                b.speed_y = -abs(b.speed_y)
                self.balls.append(b)
        elif bonus_type == BONUS_BOTTOM_SHIELD:
            self.bottom_shield_timer = 30 * FPS
        self.save_progress_callback()

    def _draw_stored_bonuses(self):
        slot_w, slot_h = 100, 32
        gap = 4
        x_start = SCREEN_WIDTH - 3 * (slot_w + gap) - 10
        y_label = 5
        y_slots = 24

        label = self.small_font.render("Бонусы (1/2/3):", True, WHITE)
        self.screen.blit(label, (x_start, y_label))

        for i in range(3):
            sx = x_start + i * (slot_w + gap)
            if i < len(self.stored_bonuses):
                btype = self.stored_bonuses[i]
                pygame.draw.rect(self.screen, STORED_BONUS_COLORS[btype], (sx, y_slots, slot_w, slot_h))
                pygame.draw.rect(self.screen, WHITE, (sx, y_slots, slot_w, slot_h), 2)
                surf = self.small_font.render(f"{i + 1}: {STORED_BONUS_NAMES[btype]}", True, WHITE)
                self.screen.blit(surf, (sx + 4, y_slots + 7))
            else:
                pygame.draw.rect(self.screen, DARK_GRAY, (sx, y_slots, slot_w, slot_h))
                pygame.draw.rect(self.screen, GRAY, (sx, y_slots, slot_w, slot_h), 2)
                surf = self.small_font.render(f"{i + 1}: —", True, GRAY)
                self.screen.blit(surf, (sx + 4, y_slots + 7))

    # ── Квиз ──────────────────────────────────────────────────────────────────

    def _get_topic_questions(self):
        with open(os.path.join(CONFIG_DIR, 'questions.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        if self.selected_topic:
            topics = data.get('topics', {})
            if self.selected_topic in topics:
                return topics[self.selected_topic].get('questions', [])
        return data.get('questions', [])

    def _save_quiz_used_indices(self):
        path = os.path.join(CONFIG_DIR, 'progress.json')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except:
            data = {}
        data['quiz_used_indices'] = self.quiz_used_indices
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def _start_quiz(self):
        questions = self._get_topic_questions()
        if not questions:
            self.game_over = True
            return
        topic_key = self.selected_topic or 'general'
        used = self.quiz_used_indices.get(topic_key, [])
        available = [i for i in range(len(questions)) if i not in used]
        if not available:
            used = []
            available = list(range(len(questions)))
        idx = random.choice(available)
        used.append(idx)
        self.quiz_used_indices[topic_key] = used
        self._save_quiz_used_indices()
        self._quiz = {
            'question': questions[idx],
            'selected': 0,
            'phase': 'asking',
            'correct': False,
            'timer': 0,
        }

    def _finish_quiz(self):
        if self._quiz['correct']:
            self.lives = 1
            self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
        else:
            self.game_over = True
        self._quiz = None

    def _draw_quiz(self):
        if self._quiz is None:
            return

        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        self.screen.blit(dim, (0, 0))

        pw, ph = 700, 460
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2

        pygame.draw.rect(self.screen, (20, 20, 60), (px, py, pw, ph))
        pygame.draw.rect(self.screen, YELLOW, (px, py, pw, ph), 3)

        title = self.big_font.render("ШАНС НА ПРОДОЛЖЕНИЕ!", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, py + 38)))
        pygame.draw.line(self.screen, YELLOW, (px + 20, py + 65), (px + pw - 20, py + 65), 1)

        q = self._quiz['question']
        phase = self._quiz['phase']
        labels = ['A', 'B', 'C', 'D']

        q_color = WHITE if phase == 'asking' else GRAY
        lines = wrap_text(q['question'], self.font, pw - 80)
        cy = py + 82
        for line in lines:
            s = self.font.render(line, True, q_color)
            self.screen.blit(s, s.get_rect(center=(SCREEN_WIDTH // 2, cy)))
            cy += self.font.get_linesize()
        cy += 10

        if phase == 'asking':
            for i, opt in enumerate(q['options']):
                oy = cy + i * 50
                sel = (i == self._quiz['selected'])
                pygame.draw.rect(self.screen,
                                 (60, 60, 130) if sel else (30, 30, 70),
                                 (px + 20, oy - 5, pw - 40, 40))
                pygame.draw.rect(self.screen,
                                 YELLOW if sel else GRAY,
                                 (px + 20, oy - 5, pw - 40, 40), 2)
                self.screen.blit(
                    self.font.render(f"  {labels[i]})  {opt}", True, YELLOW if sel else WHITE),
                    (px + 30, oy))
            hint = self.small_font.render(
                "Стрелки вверх/вниз — выбор,   ENTER — ответить", True, GRAY)
            self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, py + ph - 22)))
        else:
            correct_idx = q['answer']
            for i, opt in enumerate(q['options']):
                oy = cy + i * 50
                if i == correct_idx:
                    bg, border, fg = (0, 80, 0), GREEN, GREEN
                elif i == self._quiz['selected'] and not self._quiz['correct']:
                    bg, border, fg = (80, 0, 0), RED, RED
                else:
                    bg, border, fg = (20, 20, 50), GRAY, GRAY
                pygame.draw.rect(self.screen, bg, (px + 20, oy - 5, pw - 40, 40))
                pygame.draw.rect(self.screen, border, (px + 20, oy - 5, pw - 40, 40), 2)
                self.screen.blit(
                    self.font.render(f"  {labels[i]})  {opt}", True, fg),
                    (px + 30, oy))
            if self._quiz['correct']:
                msg = self.big_font.render("Правильно! Продолжаем!", True, GREEN)
            else:
                msg = self.big_font.render("Неверно! Игра окончена...", True, RED)
            self.screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, py + ph - 38)))

    # ── Обучение ──────────────────────────────────────────────────────────────

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

        strength_colors = {1: GREEN, 2: ORANGE, 3: RED}

        for row in range(rows):
            for col in range(cols):
                strength = layout[row][col]
                if strength == 0:
                    continue
                strength = max(1, min(3, strength))
                x = start_x + col * (brick_width + spacing)
                y = start_y + row * (brick_height + spacing)
                self.bricks.append(Brick(x, y, strength_colors[strength], strength))

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
        if self._quiz is not None and self._quiz['phase'] == 'result':
            self._quiz['timer'] -= 1
            if self._quiz['timer'] <= 0:
                self._finish_quiz()
            return

        if self._quiz is not None:
            return

        if self.paused or self.game_over or self.level_complete:
            return

        if self.tutorial_message_timer > 0:
            self.tutorial_message_timer -= 1

        self.paddle.update()

        if not self.tutorial_mode or self.tutorial_ball_active:
            for ball in self.balls[:]:
                ball.update()

        for bonus in self.bonuses[:]:
            bonus.update()

        if self.tutorial_mode and self.tutorial_step == 1 and not self.tutorial_bonus_caught:
            if len(self.bonuses) == 0:
                self.tutorial_bonus_fall_timer += 1
                if self.tutorial_bonus_fall_timer >= self.tutorial_bonus_respawn_delay:
                    self.spawn_tutorial_bonus()
            else:
                self.tutorial_bonus_fall_timer = 0

        if self.bottom_shield_timer > 0:
            self.bottom_shield_timer -= 1
            for ball in self.balls:
                if ball.rect.bottom >= SCREEN_HEIGHT:
                    ball.speed_y = -abs(ball.speed_y)
                    ball.y = SCREEN_HEIGHT - ball.radius
                    ball.rect.center = (int(ball.x), int(ball.y))

        if not self.tutorial_mode or self.tutorial_ball_active:
            for ball in self.balls[:]:
                if ball.is_off_screen():
                    self.balls.remove(ball)

        if len(self.balls) == 0 and (not self.tutorial_mode or self.tutorial_ball_active):
            self.lives -= 1
            if self.lives > 0:
                self.balls = [Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)]
            else:
                self._start_quiz()
                return

        self.handle_collisions()

        if len(self.bricks) == 0:
            self.level_complete = True
            self.save_progress()
            next_level = self.current_level + 1
            if next_level <= 10 and next_level not in self.unlocked_levels:
                self.unlocked_levels.append(next_level)
                self.save_progress_callback()

    def draw_tutorial(self):
        if not self.tutorial_mode:
            return

        if self.tutorial_step == 0 and self.tutorial_waiting_for_move:
            text_bg = pygame.Surface((SCREEN_WIDTH, 200))
            text_bg.set_alpha(180)
            text_bg.fill(BLACK)
            self.screen.blit(text_bg, text_bg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

            text1 = self.big_font.render("ОБУЧЕНИЕ", True, YELLOW)
            self.screen.blit(text1, text1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)))

            text2 = self.font.render("Чтобы двигать платформу, используйте стрелки", True, WHITE)
            self.screen.blit(text2, text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10)))

            left_arrow = self.big_font.render("←", True, CYAN)
            right_arrow = self.big_font.render("→", True, CYAN)
            self.screen.blit(left_arrow, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(right_arrow, (SCREEN_WIDTH // 2 + 80, SCREEN_HEIGHT // 2 + 30))

            text3 = self.small_font.render("Нажмите любую стрелку, чтобы продолжить", True, GREEN)
            self.screen.blit(text3, text3.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)))

        elif self.tutorial_step == 1 and not self.tutorial_bonus_caught:
            text_bg = pygame.Surface((SCREEN_WIDTH, 150))
            text_bg.set_alpha(180)
            text_bg.fill(BLACK)
            self.screen.blit(text_bg, text_bg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

            text1 = self.font.render("Отлично! Теперь поймай падающий бонус!", True, YELLOW)
            self.screen.blit(text1, text1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))

            text2 = self.small_font.render("Передвинь платформу под бонус", True, WHITE)
            self.screen.blit(text2, text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

            if len(self.bonuses) == 0:
                text3 = self.small_font.render("Бонус скоро появится...", True, CYAN)
            else:
                text3 = self.small_font.render("Лови бонус платформой!", True, GREEN)
            self.screen.blit(text3, text3.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))

        elif self.tutorial_step == 2 and self.tutorial_message_timer > 0:
            text_bg = pygame.Surface((SCREEN_WIDTH, 100))
            text_bg.set_alpha(180)
            text_bg.fill(BLACK)
            self.screen.blit(text_bg, text_bg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

            text = self.big_font.render("Отлично! Теперь играй!", True, GREEN)
            self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    def draw(self):
        self.screen.fill(BLACK)

        self.paddle.draw(self.screen)
        for ball in self.balls:
            ball.draw(self.screen)
        for brick in self.bricks:
            brick.draw(self.screen)
        for bonus in self.bonuses:
            bonus.draw(self.screen)

        if self.bottom_shield_timer > 0:
            pygame.draw.line(self.screen, PURPLE,
                             (0, SCREEN_HEIGHT - 2), (SCREEN_WIDTH, SCREEN_HEIGHT - 2), 4)
            secs = self.bottom_shield_timer // FPS + 1
            shield_surf = self.small_font.render(f"Защита дна: {secs}с", True, PURPLE)
            self.screen.blit(shield_surf,
                             shield_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 14)))

        self.screen.blit(self.font.render(f"Уровень: {self.current_level}", True, WHITE), (10, 10))
        lvl_str = str(self.current_level)
        if lvl_str in self.high_scores:
            self.screen.blit(
                self.small_font.render(f"Рекорд: {self.high_scores[lvl_str]}", True, YELLOW),
                (10, 45))
        self.screen.blit(self.font.render(f"Счет: {self.score}", True, WHITE), (10, 80))
        self.screen.blit(self.font.render(f"Жизни: {self.lives}", True, WHITE), (10, 120))
        if not self.tutorial_mode or self.tutorial_ball_active:
            self.screen.blit(
                self.small_font.render(f"Шарики: {len(self.balls)}", True, WHITE), (10, 160))
        self.screen.blit(
            self.small_font.render(f"Бонусов на уровне: {self.bonus_count}", True, GREEN), (10, 190))

        self._draw_stored_bonuses()

        if self.paused:
            t = self.font.render("ПАУЗА", True, WHITE)
            self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

        if self.level_complete:
            t = self.font.render("УРОВЕНЬ ПРОЙДЕН!", True, GREEN)
            self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
            t = self.small_font.render("Нажмите ENTER для продолжения", True, WHITE)
            self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

        if self.game_over:
            t = self.font.render("ИГРА ОКОНЧЕНА", True, RED)
            self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
            t = self.small_font.render("Нажмите R для перезапуска или ESC для выхода в меню", True, WHITE)
            self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

        self.draw_tutorial()
        self._draw_quiz()

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self._quiz is not None:
                    if self._quiz['phase'] == 'asking':
                        opts = self._quiz['question']['options']
                        if event.key == pygame.K_UP:
                            self._quiz['selected'] = (self._quiz['selected'] - 1) % len(opts)
                        elif event.key == pygame.K_DOWN:
                            self._quiz['selected'] = (self._quiz['selected'] + 1) % len(opts)
                        elif event.key == pygame.K_RETURN:
                            correct = (self._quiz['selected'] == self._quiz['question']['answer'])
                            self._quiz['correct'] = correct
                            self._quiz['phase'] = 'result'
                            self._quiz['timer'] = 90
                    continue

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
                    else:
                        self.game_over = True
                elif event.key == pygame.K_1:
                    self._use_stored_bonus(0)
                elif event.key == pygame.K_2:
                    self._use_stored_bonus(1)
                elif event.key == pygame.K_3:
                    self._use_stored_bonus(2)

                if self.tutorial_mode and self.tutorial_step == 0 and self.tutorial_waiting_for_move:
                    if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                        self.tutorial_waiting_for_move = False
                        self.tutorial_step = 1
                        self.spawn_tutorial_bonus()

        if not self.paused and not self.game_over and not self.level_complete and self._quiz is None:
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

import pygame
import json
import random
import os
from .constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BLACK, WHITE, YELLOW, GREEN, RED, GRAY,
    STORED_BONUS_NAMES,
    BONUS_BIG_PADDLE, BONUS_MULTI_BALL, BONUS_BOTTOM_SHIELD,
    CONFIG_DIR,
)
from .utils import wrap_text


class BonusQuizScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font_big = pygame.font.Font(None, 52)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)

    def _load_questions(self):
        with open(os.path.join(CONFIG_DIR, 'questions.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        try:
            with open(os.path.join(CONFIG_DIR, 'progress.json'), 'r') as f:
                progress = json.load(f)
            selected_topic = progress.get('selected_topic', None)
        except:
            selected_topic = None
        if selected_topic:
            topics = data.get('topics', {})
            if selected_topic in topics:
                return topics[selected_topic].get('questions', [])
        return data.get('questions', [])

    def run(self):
        questions = self._load_questions()
        if not questions:
            return None
        q = random.choice(questions)
        selected = 0
        phase = 'asking'
        correct = False
        earned_bonus = None
        result_timer = 0
        clock = pygame.time.Clock()
        labels = ['A', 'B', 'C', 'D']

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if phase == 'asking':
                        if event.key == pygame.K_UP:
                            selected = (selected - 1) % len(q['options'])
                        elif event.key == pygame.K_DOWN:
                            selected = (selected + 1) % len(q['options'])
                        elif event.key == pygame.K_RETURN:
                            correct = (selected == q['answer'])
                            if correct:
                                earned_bonus = random.choice([
                                    BONUS_BIG_PADDLE,
                                    BONUS_MULTI_BALL,
                                    BONUS_BOTTOM_SHIELD,
                                ])
                            phase = 'result'
                            result_timer = 120
                        elif event.key == pygame.K_ESCAPE:
                            return None
                    elif phase == 'result':
                        result_timer = 1

            if phase == 'result':
                result_timer -= 1
                if result_timer <= 0:
                    return earned_bonus

            self._draw(q, selected, phase, correct, earned_bonus, labels)
            clock.tick(FPS)

    def _draw(self, q, selected, phase, correct, earned_bonus, labels):
        self.screen.fill(BLACK)

        pw, ph = 700, 500
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2

        pygame.draw.rect(self.screen, (20, 20, 60), (px, py, pw, ph))
        pygame.draw.rect(self.screen, YELLOW, (px, py, pw, ph), 3)

        title = self.font_big.render("ПОЛУЧИТЬ БОНУС", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, py + 38)))
        pygame.draw.line(self.screen, YELLOW, (px + 20, py + 68), (px + pw - 20, py + 68), 1)

        q_color = WHITE if phase == 'asking' else GRAY
        lines = wrap_text(q['question'], self.font, pw - 80)
        cy = py + 90
        for line in lines:
            s = self.font.render(line, True, q_color)
            self.screen.blit(s, s.get_rect(center=(SCREEN_WIDTH // 2, cy)))
            cy += self.font.get_linesize()
        cy += 10

        if phase == 'asking':
            for i, opt in enumerate(q['options']):
                oy = cy + i * 52
                sel = (i == selected)
                pygame.draw.rect(self.screen,
                                 (60, 60, 130) if sel else (30, 30, 70),
                                 (px + 20, oy - 5, pw - 40, 42))
                pygame.draw.rect(self.screen,
                                 YELLOW if sel else GRAY,
                                 (px + 20, oy - 5, pw - 40, 42), 2)
                self.screen.blit(
                    self.font.render(f"  {labels[i]})  {opt}", True, YELLOW if sel else WHITE),
                    (px + 30, oy + 4))
            hint = self.small_font.render(
                "↑↓ — выбор,   ENTER — ответить,   ESC — назад", True, GRAY)
            self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, py + ph - 22)))
        else:
            correct_idx = q['answer']
            for i, opt in enumerate(q['options']):
                oy = cy + i * 52
                if i == correct_idx:
                    bg, border, fg = (0, 80, 0), GREEN, GREEN
                elif i == selected and not correct:
                    bg, border, fg = (80, 0, 0), RED, RED
                else:
                    bg, border, fg = (20, 20, 50), GRAY, GRAY
                pygame.draw.rect(self.screen, bg, (px + 20, oy - 5, pw - 40, 42))
                pygame.draw.rect(self.screen, border, (px + 20, oy - 5, pw - 40, 42), 2)
                self.screen.blit(
                    self.font.render(f"  {labels[i]})  {opt}", True, fg),
                    (px + 30, oy + 4))
            if correct and earned_bonus is not None:
                msg = self.font_big.render(
                    f"Правильно! Бонус: {STORED_BONUS_NAMES[earned_bonus]}", True, GREEN)
            else:
                msg = self.font_big.render("Неверно! Бонус не получен.", True, RED)
            self.screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, py + ph - 38)))

        pygame.display.flip()

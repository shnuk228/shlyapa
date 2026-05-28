import pygame
import json
import os
from .constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BLACK, WHITE, YELLOW, GREEN, GRAY, CYAN,
    CONFIG_DIR,
)


class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font_big = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.options = ["Начать игру", "Выбрать уровень", "Выбрать тему", "Бонусы", "Выход"]
        self.selected = 0
        self.select_level_mode = False
        self.available_levels = []
        self.topic_select_mode = False
        self.available_topics = []

    def load_progress(self):
        try:
            with open(os.path.join(CONFIG_DIR, 'progress.json'), 'r') as f:
                data = json.load(f)
            unlocked_levels = data.get('unlocked_levels', [1])
            high_scores = data.get('high_scores', {})
            tutorial_shown = data.get('tutorial_shown', False)
            stored_bonuses = data.get('stored_bonuses', [])
            selected_topic = data.get('selected_topic', None)
            return unlocked_levels, high_scores, tutorial_shown, stored_bonuses, selected_topic
        except:
            return [1], {}, False, [], None

    def save_tutorial_shown(self):
        path = os.path.join(CONFIG_DIR, 'progress.json')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except:
            data = {'unlocked_levels': [1], 'high_scores': {}, 'tutorial_shown': False}
        data['tutorial_shown'] = True
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def _load_topics(self):
        try:
            with open(os.path.join(CONFIG_DIR, 'questions.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [(k, v['name']) for k, v in data.get('topics', {}).items()]
        except:
            return []

    def save_selected_topic(self, topic_key):
        path = os.path.join(CONFIG_DIR, 'progress.json')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except:
            data = {'unlocked_levels': [1], 'high_scores': {}}
        data['selected_topic'] = topic_key
        quiz_used = data.get('quiz_used_indices', {})
        quiz_used[topic_key] = []
        data['quiz_used_indices'] = quiz_used
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def draw(self, unlocked_levels, high_scores, stored_bonuses_count=0, selected_topic=None):
        self.screen.fill(BLACK)

        title = self.font_big.render("АРКАНОИД", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 80)))

        if self.topic_select_mode:
            select_text = self.font_medium.render("Выберите тему:", True, WHITE)
            self.screen.blit(select_text, select_text.get_rect(center=(SCREEN_WIDTH // 2, 160)))

            for i, (key, name) in enumerate(self.available_topics):
                y = 270 + i * 100
                is_sel = (i == self.selected)
                pygame.draw.rect(self.screen,
                                 (60, 60, 130) if is_sel else (30, 30, 70),
                                 (200, y - 25, 600, 70), 0, 8)
                pygame.draw.rect(self.screen,
                                 YELLOW if is_sel else GRAY,
                                 (200, y - 25, 600, 70), 2, 8)
                label = name + (" ✓" if key == selected_topic else "")
                text = self.font_medium.render(label, True, YELLOW if is_sel else WHITE)
                self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, y + 10)))

            back_text = self.font_small.render("Нажмите ESC для возврата", True, WHITE)
            self.screen.blit(back_text, back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)))

        elif not self.select_level_mode:
            for i, option in enumerate(self.options):
                bonuses_blocked = (option == "Бонусы" and stored_bonuses_count >= 3)
                if bonuses_blocked:
                    color = GRAY
                    label = option + " (МАКС)"
                elif i == self.selected:
                    color = YELLOW
                    label = option
                else:
                    color = WHITE
                    label = option
                text = self.font_medium.render(label, True, color)
                self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 220 + i * 60)))

            if selected_topic:
                topics_list = self._load_topics()
                topic_name = next((n for k, n in topics_list if k == selected_topic), selected_topic)
                topic_text = self.font_small.render(f"Тема: {topic_name}", True, CYAN)
            else:
                topic_text = self.font_small.render("Тема: не выбрана", True, GRAY)
            self.screen.blit(topic_text,
                             topic_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120)))

            progress_text = self.font_small.render(
                f"Доступно уровней: {len(unlocked_levels)}", True, GREEN)
            self.screen.blit(progress_text,
                             progress_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 90)))

            if high_scores:
                total_score = sum(high_scores.values())
                total_text = self.font_small.render(f"Общий рекорд: {total_score}", True, YELLOW)
                self.screen.blit(total_text,
                                 total_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))

            bonuses_text = self.font_small.render(
                f"Бонусов в запасе: {stored_bonuses_count}/3", True, CYAN)
            self.screen.blit(bonuses_text,
                             bonuses_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 28)))
        else:
            select_text = self.font_medium.render("Выберите уровень:", True, WHITE)
            self.screen.blit(select_text, select_text.get_rect(center=(SCREEN_WIDTH // 2, 160)))

            cols = 5
            for i, level in enumerate(self.available_levels):
                row = i // cols
                col = i % cols
                x = 130 + col * 150
                y = 230 + row * 100

                is_unlocked = level in unlocked_levels
                bg_color = GREEN if is_unlocked else GRAY

                pygame.draw.rect(self.screen, bg_color, (x, y, 120, 70), 0, 10)
                pygame.draw.rect(self.screen, WHITE, (x, y, 120, 70), 2, 10)

                text = self.font_medium.render(str(level), True, WHITE)
                self.screen.blit(text, text.get_rect(center=(x + 60, y + 30)))

                if str(level) in high_scores:
                    score_text = self.font_small.render(f"{high_scores[str(level)]}", True, YELLOW)
                    self.screen.blit(score_text, score_text.get_rect(center=(x + 60, y + 55)))

                if i == self.selected:
                    pygame.draw.rect(self.screen, YELLOW, (x - 5, y - 5, 130, 80), 3, 10)

            back_text = self.font_small.render("Нажмите ESC для возврата", True, WHITE)
            self.screen.blit(back_text, back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)))

        pygame.display.flip()

    def handle_events(self, unlocked_levels, stored_bonuses_count=0):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit', None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.select_level_mode:
                        self.select_level_mode = False
                        self.selected = 0
                    elif self.topic_select_mode:
                        self.topic_select_mode = False
                        self.selected = 0
                    else:
                        return 'quit', None

                if event.key == pygame.K_UP:
                    if self.select_level_mode:
                        self.selected = max(0, self.selected - 5)
                    elif self.topic_select_mode:
                        self.selected = (self.selected - 1) % len(self.available_topics)
                    else:
                        self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    if self.select_level_mode:
                        self.selected = min(len(self.available_levels) - 1, self.selected + 5)
                    elif self.topic_select_mode:
                        self.selected = (self.selected + 1) % len(self.available_topics)
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
                    elif self.topic_select_mode:
                        topic_key, _ = self.available_topics[self.selected]
                        self.save_selected_topic(topic_key)
                        self.topic_select_mode = False
                        self.selected = 0
                    else:
                        if self.selected == 0:
                            return 'play', max(unlocked_levels)
                        elif self.selected == 1:
                            self.select_level_mode = True
                            self.available_levels = list(range(1, 11))
                            self.selected = 0
                        elif self.selected == 2:
                            self.topic_select_mode = True
                            self.available_topics = self._load_topics()
                            self.selected = 0
                        elif self.selected == 3:
                            if stored_bonuses_count < 3:
                                return 'bonus_quiz', None
                        elif self.selected == 4:
                            return 'quit', None
        return 'menu', None

import pygame
import sys
import json
import os

from classes import Menu, Arkanoid, BonusQuizScreen
from classes.constants import SCREEN_WIDTH, SCREEN_HEIGHT, CONFIG_DIR


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Арканоид")

    menu = Menu(screen)

    while True:
        unlocked_levels, high_scores, tutorial_shown, stored_bonuses, selected_topic = menu.load_progress()
        menu.draw(unlocked_levels, high_scores, len(stored_bonuses), selected_topic)
        action, level = menu.handle_events(unlocked_levels, len(stored_bonuses))

        if action == 'quit':
            pygame.quit()
            sys.exit()

        elif action == 'bonus_quiz':
            quiz_screen = BonusQuizScreen(screen)
            earned_bonus = quiz_screen.run()
            if earned_bonus is not None:
                progress_path = os.path.join(CONFIG_DIR, 'progress.json')
                try:
                    with open(progress_path, 'r') as f:
                        data = json.load(f)
                except:
                    data = {'unlocked_levels': [1], 'high_scores': {}, 'tutorial_shown': False}
                stored = data.get('stored_bonuses', [])
                if len(stored) < 3:
                    stored.append(earned_bonus)
                    data['stored_bonuses'] = stored
                    with open(progress_path, 'w') as f:
                        json.dump(data, f, indent=4)

        elif action == 'play':
            is_tutorial = (not tutorial_shown and level == 1)
            game = Arkanoid(level, is_tutorial)
            game.run()

            if is_tutorial and game.tutorial_bonus_caught:
                menu.save_tutorial_shown()


if __name__ == "__main__":
    main()

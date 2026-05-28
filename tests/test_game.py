import os
import sys
import json
import contextlib

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from classes import Ball, Paddle, Brick, Bonus
from classes.constants import (
    BONUS_EXTRA_LIFE, BONUS_MULTI_BALL, BONUS_BIG_PADDLE,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    ORANGE, YELLOW,
)


@contextlib.contextmanager
def _config_dir(tmp_path):
    """Patch CONFIG_DIR in all class modules to point at tmp_path."""
    import classes.game as gm
    import classes.menu as mm
    import classes.quiz_screen as qs
    originals = (gm.CONFIG_DIR, mm.CONFIG_DIR, qs.CONFIG_DIR)
    path = str(tmp_path)
    gm.CONFIG_DIR = mm.CONFIG_DIR = qs.CONFIG_DIR = path
    try:
        yield path
    finally:
        gm.CONFIG_DIR, mm.CONFIG_DIR, qs.CONFIG_DIR = originals


# ── Ball ──────────────────────────────────────────────────────────────────────

class TestBall:
    def test_initial_position(self):
        ball = Ball(500, 600)
        assert ball.x == 500
        assert ball.y == 600

    def test_initial_speed(self):
        ball = Ball(500, 300)
        assert ball.speed_x in [-4, 4]
        assert ball.speed_y == -5

    def test_movement(self):
        ball = Ball(500, 300)
        ball.speed_x = 4
        ball.speed_y = -5
        ball.update()
        assert ball.x == 504
        assert ball.y == 295

    def test_wall_bounce_left(self):
        ball = Ball(5, 300)
        ball.speed_x = -4
        ball.update()
        assert ball.speed_x == 4

    def test_wall_bounce_right(self):
        ball = Ball(SCREEN_WIDTH - 5, 300)
        ball.speed_x = 4
        ball.update()
        assert ball.speed_x == -4

    def test_ceiling_bounce(self):
        ball = Ball(500, 5)
        ball.speed_y = -5
        ball.update()
        assert ball.speed_y == 5

    def test_off_screen(self):
        ball = Ball(500, SCREEN_HEIGHT - 5)
        ball.speed_y = 5
        ball.update()
        assert ball.is_off_screen()

    def test_not_off_screen_in_middle(self):
        ball = Ball(500, 300)
        assert not ball.is_off_screen()

    def test_rect_follows_position(self):
        ball = Ball(500, 300)
        ball.speed_x = 4
        ball.speed_y = -5
        ball.update()
        assert ball.rect.centerx == int(ball.x)
        assert ball.rect.centery == int(ball.y)


# ── Paddle ────────────────────────────────────────────────────────────────────

class TestPaddle:
    def test_initial_width(self):
        paddle = Paddle()
        assert paddle.width == paddle.normal_width

    def test_initial_y_position(self):
        paddle = Paddle()
        assert paddle.y == SCREEN_HEIGHT - paddle.height - 30

    def test_move_left_changes_x(self):
        paddle = Paddle()
        x_before = paddle.rect.x
        paddle.move("left")
        assert paddle.rect.x == x_before - paddle.speed

    def test_move_right_changes_x(self):
        paddle = Paddle()
        x_before = paddle.rect.x
        paddle.move("right")
        assert paddle.rect.x == x_before + paddle.speed

    def test_left_boundary(self):
        paddle = Paddle()
        paddle.rect.x = 0
        paddle.move("left")
        assert paddle.rect.left >= 0

    def test_right_boundary(self):
        paddle = Paddle()
        paddle.rect.right = SCREEN_WIDTH
        paddle.move("right")
        assert paddle.rect.right <= SCREEN_WIDTH

    def test_make_big_increases_width(self):
        paddle = Paddle()
        paddle.make_big()
        assert paddle.width == paddle.big_width
        assert paddle.rect.width == paddle.big_width

    def test_make_big_sets_timer(self):
        paddle = Paddle()
        paddle.make_big(120)
        assert paddle.big_paddle_timer == 120

    def test_timer_decreases_on_update(self):
        paddle = Paddle()
        paddle.make_big(100)
        paddle.update()
        assert paddle.big_paddle_timer == 99

    def test_reverts_to_normal_when_timer_expires(self):
        paddle = Paddle()
        paddle.make_big(1)
        paddle.update()
        assert paddle.width == paddle.normal_width
        assert paddle.big_paddle_timer == 0

    def test_make_big_not_double_applied(self):
        paddle = Paddle()
        paddle.make_big(100)
        paddle.make_big(200)
        assert paddle.big_paddle_timer == 100


# ── Brick ─────────────────────────────────────────────────────────────────────

class TestBrick:
    def test_initial_strength(self):
        brick = Brick(100, 100, (255, 0, 0), strength=3)
        assert brick.strength == 3

    def test_hit_reduces_strength(self):
        brick = Brick(100, 100, (255, 0, 0), strength=2)
        result = brick.hit()
        assert brick.strength == 1
        assert result is False

    def test_hit_destroys_brick(self):
        brick = Brick(100, 100, (255, 0, 0), strength=1)
        result = brick.hit()
        assert result is True

    def test_color_changes_at_strength_2(self):
        brick = Brick(100, 100, (255, 0, 0), strength=3)
        brick.hit()
        assert brick.color == ORANGE

    def test_color_changes_at_strength_1(self):
        brick = Brick(100, 100, (255, 0, 0), strength=3)
        brick.hit()
        brick.hit()
        assert brick.color == YELLOW

    def test_brick_rect_dimensions(self):
        brick = Brick(100, 100, (255, 0, 0))
        assert brick.rect.width == 70
        assert brick.rect.height == 22


# ── Bonus ─────────────────────────────────────────────────────────────────────

class TestBonus:
    def test_falls_downward(self):
        bonus = Bonus(100, 100, BONUS_EXTRA_LIFE)
        y_before = bonus.rect.y
        bonus.update()
        assert bonus.rect.y == y_before + bonus.speed_y

    def test_active_by_default(self):
        bonus = Bonus(100, 100, BONUS_MULTI_BALL)
        assert bonus.active is True

    def test_extra_life_type(self):
        bonus = Bonus(0, 0, BONUS_EXTRA_LIFE)
        assert bonus.type == BONUS_EXTRA_LIFE

    def test_multi_ball_type(self):
        bonus = Bonus(0, 0, BONUS_MULTI_BALL)
        assert bonus.type == BONUS_MULTI_BALL

    def test_big_paddle_type(self):
        bonus = Bonus(0, 0, BONUS_BIG_PADDLE)
        assert bonus.type == BONUS_BIG_PADDLE

    def test_bonus_size(self):
        bonus = Bonus(100, 100, BONUS_EXTRA_LIFE)
        assert bonus.rect.width == 20
        assert bonus.rect.height == 20


# ── Level loading ─────────────────────────────────────────────────────────────

class TestLevelLoading:
    def test_loads_10_levels(self, tmp_path):
        levels_data = {
            "levels": [
                {"id": i, "name": f"Level {i}", "layout": [[1, 1], [1, 1]]}
                for i in range(1, 11)
            ]
        }
        (tmp_path / "levels.json").write_text(json.dumps(levels_data))

        with _config_dir(tmp_path):
            from classes.game import Arkanoid
            game = Arkanoid.__new__(Arkanoid)
            game.load_levels()
            assert len(game.levels) == 10

    def test_level_has_layout(self, tmp_path):
        levels_data = {
            "levels": [
                {"id": 1, "name": "Test", "layout": [[1, 2, 3], [3, 2, 1]]}
            ]
        }
        (tmp_path / "levels.json").write_text(json.dumps(levels_data))

        with _config_dir(tmp_path):
            from classes.game import Arkanoid
            game = Arkanoid.__new__(Arkanoid)
            game.load_levels()
            assert game.levels[0]["layout"] == [[1, 2, 3], [3, 2, 1]]

    def test_fallback_levels_generated_when_no_file(self, tmp_path):
        with _config_dir(tmp_path):
            from classes.game import Arkanoid
            game = Arkanoid.__new__(Arkanoid)
            game.load_levels()
            assert len(game.levels) == 10


# ── Progress persistence ──────────────────────────────────────────────────────

class TestProgressPersistence:
    def test_save_and_load_progress(self, tmp_path):
        data = {
            "unlocked_levels": [1, 2],
            "high_scores": {"1": 500},
            "selected_topic": None,
            "quiz_used_indices": {},
        }
        (tmp_path / "progress.json").write_text(json.dumps(data))

        with _config_dir(tmp_path):
            from classes.game import Arkanoid
            game = Arkanoid.__new__(Arkanoid)
            game.load_progress()
            assert 1 in game.unlocked_levels
            assert 2 in game.unlocked_levels
            assert game.high_scores.get("1") == 500

    def test_defaults_when_no_file(self, tmp_path):
        with _config_dir(tmp_path):
            from classes.game import Arkanoid
            game = Arkanoid.__new__(Arkanoid)
            game.load_progress()
            assert game.unlocked_levels == [1]
            assert game.high_scores == {}
            assert game.selected_topic is None
            assert game.quiz_used_indices == {}

    def test_loads_selected_topic_and_used_indices(self, tmp_path):
        data = {
            "unlocked_levels": [1],
            "high_scores": {},
            "selected_topic": "cars",
            "quiz_used_indices": {"cars": [0]},
        }
        (tmp_path / "progress.json").write_text(json.dumps(data))

        with _config_dir(tmp_path):
            from classes.game import Arkanoid
            game = Arkanoid.__new__(Arkanoid)
            game.load_progress()
            assert game.selected_topic == "cars"
            assert game.quiz_used_indices == {"cars": [0]}


# ── Quiz ──────────────────────────────────────────────────────────────────────

class TestQuiz:
    # ── helpers ───────────────────────────────────────────────────────────────

    def _write_questions(self, tmp_path, questions, topics=None):
        data = {"questions": questions}
        if topics:
            data["topics"] = topics
        (tmp_path / "questions.json").write_text(json.dumps(data), encoding="utf-8")

    def _write_progress(self, tmp_path, selected_topic=None, used=None):
        data = {
            "unlocked_levels": [1],
            "high_scores": {},
            "selected_topic": selected_topic,
            "quiz_used_indices": used or {},
        }
        (tmp_path / "progress.json").write_text(json.dumps(data))

    def _stub_game(self, selected_topic=None, used=None):
        from classes.game import Arkanoid
        game = Arkanoid.__new__(Arkanoid)
        game._quiz = None
        game.game_over = False
        game.lives = 0
        game.balls = []
        game.selected_topic = selected_topic
        game.quiz_used_indices = used if used is not None else {}
        return game

    # ── _get_topic_questions ──────────────────────────────────────────────────

    def test_get_questions_no_topic_returns_general(self, tmp_path):
        self._write_questions(tmp_path, [
            {"id": 1, "question": "Q?", "options": ["A", "B", "C", "D"], "answer": 0}
        ])
        with _config_dir(tmp_path):
            game = self._stub_game()
            result = game._get_topic_questions()
            assert len(result) == 1
            assert result[0]["question"] == "Q?"

    def test_get_questions_with_topic(self, tmp_path):
        self._write_questions(tmp_path, [], topics={
            "cars": {
                "name": "Авто",
                "questions": [
                    {"id": 1, "question": "Car Q?", "options": ["A", "B", "C", "D"], "answer": 1}
                ],
            }
        })
        with _config_dir(tmp_path):
            game = self._stub_game(selected_topic="cars")
            result = game._get_topic_questions()
            assert len(result) == 1
            assert result[0]["question"] == "Car Q?"

    def test_get_questions_unknown_topic_falls_back_to_general(self, tmp_path):
        self._write_questions(tmp_path, [
            {"id": 1, "question": "General?", "options": ["A", "B", "C", "D"], "answer": 0}
        ])
        with _config_dir(tmp_path):
            game = self._stub_game(selected_topic="nonexistent")
            result = game._get_topic_questions()
            assert result[0]["question"] == "General?"

    # ── _start_quiz ───────────────────────────────────────────────────────────

    def test_start_quiz_activates_quiz(self, tmp_path):
        self._write_questions(tmp_path, [
            {"id": 1, "question": "Q?", "options": ["A", "B", "C", "D"], "answer": 2}
        ])
        self._write_progress(tmp_path)
        with _config_dir(tmp_path):
            game = self._stub_game()
            game._start_quiz()
            assert game._quiz is not None
            assert game._quiz['phase'] == 'asking'
            assert game._quiz['selected'] == 0
            assert game._quiz['correct'] is False
            assert 'question' in game._quiz

    def test_start_quiz_empty_questions_sets_game_over(self, tmp_path):
        self._write_questions(tmp_path, [])
        self._write_progress(tmp_path)
        with _config_dir(tmp_path):
            game = self._stub_game()
            game._start_quiz()
            assert game._quiz is None
            assert game.game_over is True

    # ── _finish_quiz ──────────────────────────────────────────────────────────

    def test_finish_quiz_correct_restores_life(self):
        game = self._stub_game()
        game._quiz = {'question': {}, 'selected': 0, 'phase': 'result',
                      'correct': True, 'timer': 0}
        game._finish_quiz()
        assert game._quiz is None
        assert game.lives == 1
        assert len(game.balls) == 1
        assert game.game_over is False

    def test_finish_quiz_wrong_sets_game_over(self):
        game = self._stub_game()
        game._quiz = {'question': {}, 'selected': 0, 'phase': 'result',
                      'correct': False, 'timer': 0}
        game._finish_quiz()
        assert game._quiz is None
        assert game.game_over is True

    # ── Question cycling ──────────────────────────────────────────────────────

    def test_each_question_used_once_before_cycling(self, tmp_path):
        self._write_questions(tmp_path, [
            {"id": i, "question": f"Q{i}?", "options": ["A", "B", "C", "D"], "answer": 0}
            for i in range(3)
        ])
        self._write_progress(tmp_path)
        with _config_dir(tmp_path):
            game = self._stub_game()
            seen = set()
            for _ in range(3):
                game._start_quiz()
                seen.add(game._quiz['question']['id'])
                game._quiz = None
            assert len(seen) == 3

    def test_questions_reset_after_all_used(self, tmp_path):
        self._write_questions(tmp_path, [
            {"id": i, "question": f"Q{i}?", "options": ["A", "B", "C", "D"], "answer": 0}
            for i in range(2)
        ])
        self._write_progress(tmp_path)
        with _config_dir(tmp_path):
            game = self._stub_game()
            game._start_quiz(); game._quiz = None
            game._start_quiz(); game._quiz = None
            assert set(game.quiz_used_indices.get('general', [])) == {0, 1}
            game._start_quiz()
            assert game._quiz is not None  # cycle restarted, a question was picked

    def test_topic_questions_cycle_independently(self, tmp_path):
        self._write_questions(tmp_path, [], topics={
            "animals": {
                "name": "Животные",
                "questions": [
                    {"id": i, "question": f"A{i}?", "options": ["A", "B", "C", "D"], "answer": 0}
                    for i in range(2)
                ],
            }
        })
        self._write_progress(tmp_path, selected_topic="animals")
        with _config_dir(tmp_path):
            game = self._stub_game(selected_topic="animals")
            seen = set()
            for _ in range(2):
                game._start_quiz()
                seen.add(game._quiz['question']['id'])
                game._quiz = None
            assert len(seen) == 2
            assert set(game.quiz_used_indices.get('animals', [])) == {0, 1}

    # ── wrap_text ─────────────────────────────────────────────────────────────

    def test_wrap_text_splits_long_line(self):
        from classes.utils import wrap_text
        font = pygame.font.Font(None, 36)
        text = "Это очень длинное предложение которое должно быть разбито на несколько строк"
        lines = wrap_text(text, font, 300)
        assert len(lines) > 1
        for line in lines:
            assert font.size(line)[0] <= 300

    def test_wrap_text_short_line_unchanged(self):
        from classes.utils import wrap_text
        font = pygame.font.Font(None, 36)
        lines = wrap_text("Короткий текст", font, 600)
        assert len(lines) == 1

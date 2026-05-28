import os

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

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

BONUS_EXTRA_LIFE = 1
BONUS_MULTI_BALL = 2
BONUS_BIG_PADDLE = 3
BONUS_BOTTOM_SHIELD = 4

STORED_BONUS_NAMES = {
    BONUS_BIG_PADDLE:    "Длинная платф.",
    BONUS_MULTI_BALL:    "Много шаров",
    BONUS_BOTTOM_SHIELD: "Защита дна",
}
STORED_BONUS_COLORS = {
    BONUS_BIG_PADDLE:    BLUE,
    BONUS_MULTI_BALL:    GREEN,
    BONUS_BOTTOM_SHIELD: PURPLE,
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, 'configs')

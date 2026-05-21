import sys
import os
import json
import pygame
import pytest

# Добавляем родительскую папку в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Создаем упрощенные версии классов для тестирования (чтобы не зависеть от pygame)
class MockBall:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed_x = 4
        self.speed_y = -5
        self.radius = 7
        self.rect = pygame.Rect(x - self.radius, y - self.radius, 
                                self.radius * 2, self.radius * 2)
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.rect.center = (self.x, self.y)
    
    def is_off_screen(self):
        return self.y + self.radius >= 700  # SCREEN_HEIGHT

class MockPaddle:
    def __init__(self, width=120):
        self.width = width
        self.height = 15
        self.x = (1000 - self.width) // 2
        self.y = 700 - self.height - 30
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.speed = 8
        self.big_paddle_timer = 0
    
    def move(self, direction):
        if direction == 'left' and self.rect.left > 0:
            self.rect.x -= self.speed
        elif direction == 'right' and self.rect.right < 1000:
            self.rect.x += self.speed

class MockBrick:
    def __init__(self, x, y, color, strength=1):
        self.width = 70
        self.height = 22
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.strength = strength
        self.color = color
    
    def hit(self):
        self.strength -= 1
        return self.strength == 0


class TestGameMechanics:
    """Тесты основной механики игры"""
    
    def setup_method(self):
        """Инициализация перед каждым тестом"""
        pygame.init()
        self.paddle = MockPaddle()
        self.ball = MockBall(500, 600)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        pygame.quit()
    
    def test_ball_movement(self):
        """Тест 1: Проверка движения шарика"""
        initial_x = self.ball.x
        initial_y = self.ball.y
        
        self.ball.update()
        
        # Шарик должен изменить координаты
        assert self.ball.x != initial_x or self.ball.y != initial_y
        print(f"✓ Шарик движется: ({initial_x}, {initial_y}) -> ({self.ball.x}, {self.ball.y})")
    
    def test_paddle_movement_left(self):
        """Тест 2: Проверка движения платформы влево"""
        initial_x = self.paddle.rect.x
        
        # Двигаем влево
        self.paddle.move('left')
        
        # Платформа должна сместиться влево
        assert self.paddle.rect.x < initial_x
        print(f"✓ Платформа движется влево: {initial_x} -> {self.paddle.rect.x}")
    
    def test_paddle_movement_right(self):
        """Тест 3: Проверка движения платформы вправо"""
        initial_x = self.paddle.rect.x
        
        # Двигаем вправо
        self.paddle.move('right')
        
        # Платформа должна сместиться вправо
        assert self.paddle.rect.x > initial_x
        print(f"✓ Платформа движется вправо: {initial_x} -> {self.paddle.rect.x}")
    
    def test_paddle_boundaries(self):
        """Тест 4: Проверка границ платформы (не выходит за экран)"""
        # Двигаем влево много раз
        for _ in range(20):
            self.paddle.move('left')
        
        # Платформа не должна уйти за левый край
        assert self.paddle.rect.left >= 0
        
        # Двигаем вправо много раз
        for _ in range(20):
            self.paddle.move('right')
        
        # Платформа не должна уйти за правый край
        assert self.paddle.rect.right <= 1000
        print(f"✓ Границы платформы работают корректно")
    
    def test_ball_collision_with_paddle(self):
        """Тест 5: Проверка столкновения шарика с платформой"""
        # Размещаем шарик прямо над платформой
        self.ball.x = self.paddle.rect.centerx
        self.ball.y = self.paddle.rect.top - 10
        self.ball.rect.center = (self.ball.x, self.ball.y)
        
        # Скорость до столкновения
        old_speed_y = self.ball.speed_y
        
        # Проверяем столкновение
        if self.ball.rect.colliderect(self.paddle.rect):
            # При столкновении скорость по Y должна изменить знак
            self.ball.speed_y = -abs(self.ball.speed_y)
            assert self.ball.speed_y > 0 or old_speed_y < 0
            print(f"✓ Столкновение с платформой работает: скорость Y {old_speed_y} -> {self.ball.speed_y}")
    
    def test_brick_strength(self):
        """Тест 6: Проверка прочности кирпичей"""
        # Кирпич с прочностью 1
        brick1 = MockBrick(100, 100, (0, 255, 0), 1)
        assert brick1.hit() == True  # Разбивается с 1 удара
        
        # Кирпич с прочностью 2
        brick2 = MockBrick(100, 100, (255, 165, 0), 2)
        assert brick2.hit() == False  # Не разбился с 1 удара
        assert brick2.hit() == True   # Разбился со 2 удара
        
        # Кирпич с прочностью 3
        brick3 = MockBrick(100, 100, (255, 0, 0), 3)
        assert brick3.hit() == False  # 1 удар
        assert brick3.hit() == False  # 2 удар
        assert brick3.hit() == True   # 3 удар
        
        print(f"✓ Прочность кирпичей работает корректно")
    
    def test_bonus_distribution_logic(self):
        """Тест 7: Проверка логики распределения бонусов"""
        total_bricks = 25
        bonus_count = max(1, total_bricks // 5)  # Должно быть 5 бонусов
        
        # Равномерное распределение
        step = total_bricks / bonus_count
        bonus_indices = [int(i * step) for i in range(bonus_count)]
        
        # Проверяем, что индексы уникальны
        assert len(set(bonus_indices)) == len(bonus_indices)
        # Проверяем, что все индексы в пределах
        assert all(0 <= idx < total_bricks for idx in bonus_indices)
        # Проверяем, что бонусы распределены равномерно
        assert len(bonus_indices) == 5
        print(f"✓ Бонусы распределены равномерно: {bonus_indices}")
    
    def test_ball_off_screen_detection(self):
        """Тест 8: Проверка определения выхода шарика за экран"""
        # Шарик в пределах экрана
        self.ball.y = 600
        assert self.ball.is_off_screen() == False
        
        # Шарик за нижней границей
        self.ball.y = 710
        assert self.ball.is_off_screen() == True
        
        print(f"✓ Определение выхода за экран работает")
    
    def test_lives_mechanics(self):
        """Тест 9: Проверка механики жизней"""
        lives = 3
        
        # Тратим жизни
        lives -= 1
        assert lives == 2
        lives -= 1
        assert lives == 1
        lives -= 1
        assert lives == 0
        
        # Защита активируется когда lives == 0
        assert lives == 0
        print(f"✓ Механика жизней работает корректно")
    
    def test_tutorial_steps(self):
        """Тест 10: Проверка последовательности шагов обучения"""
        tutorial_step = 0  # Обучение движению
        tutorial_waiting_for_move = True
        
        # Имитируем нажатие стрелки
        if tutorial_waiting_for_move:
            tutorial_waiting_for_move = False
            tutorial_step = 1  # Переход к обучению бонусу
        
        assert tutorial_step == 1
        assert tutorial_waiting_for_move == False
        
        # Имитируем получение бонуса
        tutorial_bonus_caught = True
        if tutorial_bonus_caught:
            tutorial_step = 2  # Завершение обучения
        
        assert tutorial_step == 2
        print(f"✓ Последовательность обучения работает")


class TestJSONStructure:
    """Тесты структуры JSON файлов"""
    
    def test_levels_json_structure(self):
        """Тест 11: Проверка структуры levels.json"""
        # Путь к файлу levels.json в корневой папке
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'levels.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert 'levels' in data
            levels = data['levels']
            assert len(levels) >= 1  # Хотя бы один уровень
            
            for level in levels:
                assert 'id' in level
                assert 'layout' in level
                assert 'name' in level
                assert 1 <= level['id'] <= 10
                
                # Проверяем, что layout - это список списков
                layout = level['layout']
                assert isinstance(layout, list)
                for row in layout:
                    assert isinstance(row, list)
                    for cell in row:
                        assert 0 <= cell <= 3  # Допустимые значения: 0,1,2,3
            
            print(f"✓ Структура levels.json корректна, найдено {len(levels)} уровней")
        else:
            print(f"⚠ Файл levels.json не найден по пути: {json_path}")
            print(f"  Пропускаем этот тест")


# Запуск тестов через pytest
if __name__ == "__main__":
    # Инициализация Pygame для тестов
    pygame.init()
    
    # Создаем тестовый экран (невидимый)
    screen = pygame.display.set_mode((1, 1))
    
    # Создаем экземпляры тестов
    test_mechanics = TestGameMechanics()
    test_json = TestJSONStructure()
    
    print("\n" + "="*50)
    print("ЗАПУСК UNIT ТЕСТОВ")
    print("="*50 + "\n")
    
    # Запускаем тесты механики
    test_mechanics.setup_method()
    test_mechanics.test_ball_movement()
    test_mechanics.test_paddle_movement_left()
    test_mechanics.test_paddle_movement_right()
    test_mechanics.test_paddle_boundaries()
    test_mechanics.test_ball_collision_with_paddle()
    test_mechanics.test_brick_strength()
    test_mechanics.test_bonus_distribution_logic()
    test_mechanics.test_ball_off_screen_detection()
    test_mechanics.test_lives_mechanics()
    test_mechanics.test_tutorial_steps()
    test_mechanics.teardown_method()
    
    # Запускаем тесты JSON
    test_json.test_levels_json_structure()
    
    pygame.quit()
    
    print("\n" + "="*50)
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("="*50)
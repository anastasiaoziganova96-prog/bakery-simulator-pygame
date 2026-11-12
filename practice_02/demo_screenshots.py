"""Автоматическая демонстрация без окна (для Google Colab).
Прогоняет настоящие функции из main.py по сценарию и сохраняет скриншоты."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"     # окно не нужно
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import main as bakery

pygame.init()
screen = pygame.display.set_mode((bakery.WIDTH, bakery.HEIGHT))
fonts = bakery.create_fonts()
state = bakery.create_state()
os.makedirs("screenshots", exist_ok=True)
DT = 1 / 60


class FakeKeys:
    """Имитация pygame.key.get_pressed()."""
    def __init__(self, pressed):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


def press(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def step(pressed=(), events=(), frames=1):
    for _ in range(frames):
        bakery.handle_events(state, list(events))
        events = ()
        if not state["menu_open"]:
            bakery.handle_movement(state["player"], FakeKeys(pressed), DT)
        bakery.update_order(state, DT)


def shot(name):
    bakery.draw_scene(screen, state, fonts)
    bakery.draw_ui(screen, state, fonts, 60)
    pygame.image.save(screen, f"screenshots/{name}")
    print("сохранено:", name)


def walk_to(tx, ty, tol=4):
    for _ in range(2000):
        p = state["player"]
        keys = set()
        if tx - p["x"] > tol: keys.add(pygame.K_d)
        if p["x"] - tx > tol: keys.add(pygame.K_a)
        if ty - p["y"] > tol: keys.add(pygame.K_s)
        if p["y"] - ty > tol: keys.add(pygame.K_w)
        if not keys:
            return
        step(keys)


def order(number_key):
    walk_to(430, 210)
    step(events=[press(pygame.K_e)])
    step(events=[press(number_key)])


def pickup():
    walk_to(870, 430)
    while state["order_state"] == bakery.WAITING:
        step()
    step(events=[press(pygame.K_e)])


# 1. Общий вид
walk_to(430, 420)
shot("bakery.png")

# 2. Смена цвета
step(events=[press(pygame.K_SPACE)])
shot("03_color.png")

# 3. E вне зоны — меню не открывается
step(events=[press(pygame.K_e)])
shot("04_E_outside_zone.png")

# 4. Столкновение с прилавком + подсказка
step({pygame.K_w}, frames=120)
shot("05_counter_hint.png")

# 5. Меню заказа
step(events=[press(pygame.K_e)])
shot("ordering.png")

# 6. Заказ сэндвича, клиент идёт к выдаче во время готовки
step(events=[press(pygame.K_3)])
step({pygame.K_d, pygame.K_s}, frames=90)
shot("07_waiting.png")

# 7. Заказ готов, зона выдачи подсвечена
walk_to(870, 430)
while state["order_state"] == bakery.WAITING:
    step()
shot("08_ready.png")

# 8. Заказ получен
step(events=[press(pygame.K_e)])
shot("09_done.png")

# 9. Второй сэндвич (остаток станет 0)
order(pygame.K_3)
pickup()

# 10. Недостаточно денег (осталось 60 ₽)
walk_to(430, 210)
step(events=[press(pygame.K_e)])
step(events=[press(pygame.K_4)])
shot("10_no_money.png")

# 11. Товар закончился
step(events=[press(pygame.K_3)])
shot("11_out_of_stock.png")

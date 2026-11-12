"""Симулятор пекарни. Этап 1 — клиент и заказ (PyGame).

Управление:
    W A S D  — движение клиента (включите английскую раскладку)
    SPACE    — сменить цвет клиента
    E        — действие (заказ у прилавка / получение заказа в зоне выдачи)
    1–4      — выбор товара в меню, 0 или Backspace — закрыть меню
    Esc      — выход
"""
import math
import pygame

# ---------------------------------------------------------------------------
# Задание 1. Параметры окна и основного цикла
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1000, 650
FPS = 60
TITLE = "Симулятор пекарни. Этап 1 — клиент и заказ"

# ---------------------------------------------------------------------------
# Задание 8. Состояния заказа
# ---------------------------------------------------------------------------
NO_ORDER = "NO_ORDER"   # активного заказа нет
WAITING = "WAITING"     # заказ готовится
READY = "READY"         # заказ готов
DONE = "DONE"           # заказ получен

# ---------------------------------------------------------------------------
# Задание 2. План пекарни (зоны)
# ---------------------------------------------------------------------------
ENTRANCE = pygame.Rect(20, 500, 170, 130)         # вход
COUNTER = pygame.Rect(250, 120, 360, 50)          # прилавок (препятствие)
CASH_DESK = pygame.Rect(650, 120, 100, 50)        # касса (препятствие)
COUNTER_ZONE = pygame.Rect(250, 170, 360, 80)     # Задание 5: зона взаимодействия
PICKUP_ZONE = pygame.Rect(790, 330, 190, 200)     # зона выдачи
OBSTACLES = [COUNTER, CASH_DESK]

# ---------------------------------------------------------------------------
# Задание 3 и 4. Клиент и цвета
# ---------------------------------------------------------------------------
PLAYER_COLORS = [
    (220, 60, 60),    # красный
    (60, 120, 220),   # синий
    (60, 170, 90),    # зелёный
    (230, 190, 40),   # жёлтый
    (150, 80, 190),   # фиолетовый
]
START_MONEY = 420      # Задание 7

# Задание 6: общая структура данных о товарах (список словарей)
def create_products():
    return [
        {"name": "Хлеб",    "price": 70,  "stock": 3, "cook_time": 0},
        {"name": "Булочка", "price": 90,  "stock": 4, "cook_time": 0},
        {"name": "Сэндвич", "price": 180, "stock": 2, "cook_time": 5},
        {"name": "Кофе",    "price": 140, "stock": 5, "cook_time": 3},
    ]


MENU_KEYS = {
    pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3,
    pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2, pygame.K_KP4: 3,
}


def create_state():
    """Всё состояние игры в одном словаре."""
    return {
        # Задание 3: координаты, радиус, цвет, скорость (px/s)
        "player": {
            "x": ENTRANCE.centerx, "y": ENTRANCE.centery,
            "radius": 16, "color_index": 0, "color": PLAYER_COLORS[0],
            "speed": 220.0,
        },
        "money": START_MONEY,
        "products": create_products(),
        "order_state": NO_ORDER,
        "order_name": None,
        "cook_left": 0.0,
        "cook_total": 0.0,
        "menu_open": False,
        "message": "",
        "message_timer": 0.0,
    }


# ---------------------------------------------------------------------------
# Вспомогательные функции (геометрия, сообщения)
# ---------------------------------------------------------------------------
def create_fonts():
    """Шрифты с поддержкой кириллицы (для Colab нужен fonts-dejavu-core)."""
    path = None
    for name in ("dejavusans", "arial", "liberationsans", "notosans", "freesans"):
        path = pygame.font.match_font(name)
        if path:
            break
    return {
        "small": pygame.font.Font(path, 18),
        "normal": pygame.font.Font(path, 22),
        "big": pygame.font.Font(path, 30),
    }


def circle_hits_rect(x, y, radius, rect):
    """Пересекается ли круг с прямоугольником."""
    nearest_x = max(rect.left, min(x, rect.right))
    nearest_y = max(rect.top, min(y, rect.bottom))
    return (x - nearest_x) ** 2 + (y - nearest_y) ** 2 < radius ** 2


def hits_obstacles(x, y, radius):
    return any(circle_hits_rect(x, y, radius, rect) for rect in OBSTACLES)


def player_in_zone(player, zone):
    return zone.collidepoint(player["x"], player["y"])


def set_message(state, text, seconds=3.0):
    state["message"] = text
    state["message_timer"] = seconds


def has_active_order(state):
    return state["order_state"] in (WAITING, READY)


def get_action_hint(state):
    """Доступное действие в зависимости от положения клиента (Задания 5, 11, 12)."""
    player = state["player"]
    if state["menu_open"]:
        return "1–4 — выбрать, 0 — закрыть"
    if state["order_state"] == READY and player_in_zone(player, PICKUP_ZONE):
        return "E — получить заказ"
    if player_in_zone(player, COUNTER_ZONE) and not has_active_order(state):
        return "E — сделать заказ"
    return "—"


# ---------------------------------------------------------------------------
# Задание 6, 7, 8. Логика заказа
# ---------------------------------------------------------------------------
def try_order(state, index):
    """Проверка наличия и денег, оформление заказа."""
    product = state["products"][index]
    if product["stock"] <= 0:
        set_message(state, "Товар закончился")
        return
    if state["money"] < product["price"]:
        set_message(state, "Недостаточно денег")
        return

    state["money"] -= product["price"]
    product["stock"] -= 1
    state["order_name"] = product["name"]
    state["menu_open"] = False
    set_message(state, "Заказ принят")

    if product["cook_time"] > 0:
        state["order_state"] = WAITING
        state["cook_total"] = float(product["cook_time"])
        state["cook_left"] = float(product["cook_time"])
    else:
        state["order_state"] = READY
        state["cook_total"] = 0.0
        state["cook_left"] = 0.0


def interact(state):
    """Нажатие E: меню у прилавка или получение заказа (Задания 5, 11)."""
    player = state["player"]
    if state["menu_open"]:
        state["menu_open"] = False
        return
    if state["order_state"] == READY and player_in_zone(player, PICKUP_ZONE):
        state["order_state"] = DONE
        set_message(state, "Заказ получен")
    elif player_in_zone(player, COUNTER_ZONE):
        if has_active_order(state):
            set_message(state, "Сначала получите текущий заказ")
        else:
            state["menu_open"] = True
            state["message"] = ""
    # вне зон нажатие E ничего не делает


# ---------------------------------------------------------------------------
# Задание 1, 4, 5, 6, 11. Обработка событий
# ---------------------------------------------------------------------------
def handle_events(state, events):
    """Возвращает False, если нужно завершить программу."""
    for event in events:
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_ESCAPE:
            return False
        if event.key == pygame.K_SPACE:
            # Задание 4: KEYDOWN срабатывает один раз на нажатие
            player = state["player"]
            player["color_index"] = (player["color_index"] + 1) % len(PLAYER_COLORS)
            player["color"] = PLAYER_COLORS[player["color_index"]]
        elif event.key == pygame.K_e:
            interact(state)
        elif state["menu_open"]:
            if event.key in MENU_KEYS:
                try_order(state, MENU_KEYS[event.key])
            elif event.key in (pygame.K_0, pygame.K_KP0, pygame.K_BACKSPACE):
                state["menu_open"] = False
    return True


# ---------------------------------------------------------------------------
# Задание 3. Движение клиента
# ---------------------------------------------------------------------------
def handle_movement(player, keys, dt):
    """WASD, delta time, нормализация диагонали, границы и препятствия."""
    dx = int(bool(keys[pygame.K_d])) - int(bool(keys[pygame.K_a]))
    dy = int(bool(keys[pygame.K_s])) - int(bool(keys[pygame.K_w]))
    if dx == 0 and dy == 0:
        return

    length = math.hypot(dx, dy)          # для диагонали = 1.414...
    dx, dy = dx / length, dy / length    # единичный вектор направления
    step = player["speed"] * dt          # пиксели/сек * сек = пиксели
    radius = player["radius"]

    # Оси проверяются отдельно: клиент «скользит» вдоль препятствия
    new_x = min(max(player["x"] + dx * step, radius), WIDTH - radius)
    if not hits_obstacles(new_x, player["y"], radius):
        player["x"] = new_x

    new_y = min(max(player["y"] + dy * step, radius), HEIGHT - radius)
    if not hits_obstacles(player["x"], new_y, radius):
        player["y"] = new_y


# ---------------------------------------------------------------------------
# Задание 9. Приготовление заказа без time.sleep
# ---------------------------------------------------------------------------
def update_order(state, dt):
    if state["message_timer"] > 0:
        state["message_timer"] -= dt
        if state["message_timer"] <= 0:
            state["message"] = ""

    if state["order_state"] == WAITING:
        state["cook_left"] -= dt
        if state["cook_left"] <= 0:
            state["cook_left"] = 0.0
            state["order_state"] = READY
            set_message(state, "Заказ готов — заберите его в зоне выдачи", 4.0)


# ---------------------------------------------------------------------------
# Отрисовка (Задания 2, 10, 12). Здесь нет изменения денег/остатков/состояния
# ---------------------------------------------------------------------------
def draw_text(screen, font, text, pos, color=(30, 30, 30), center=False):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    screen.blit(surface, rect)


def draw_zone(screen, rect, color, label, font, alpha=255, text_color=(30, 30, 30)):
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    layer.fill((*color, alpha))
    screen.blit(layer, rect.topleft)
    pygame.draw.rect(screen, (60, 60, 60), rect, 2)
    draw_text(screen, font, label, rect.center, text_color, center=True)


def draw_scene(screen, state, fonts):
    """Задания 2, 3, 5, 11: план пекарни, зоны и клиент."""
    screen.fill((238, 226, 205))
    pygame.draw.rect(screen, (205, 190, 165), (0, 0, WIDTH, HEIGHT), 6)

    draw_zone(screen, ENTRANCE, (120, 190, 120), "Вход", fonts["normal"])
    draw_zone(screen, COUNTER_ZONE, (255, 225, 110), "Зона заказа", fonts["small"], alpha=120)
    draw_zone(screen, COUNTER, (150, 100, 60), "Прилавок", fonts["normal"],
              text_color=(255, 255, 255))
    draw_zone(screen, CASH_DESK, (90, 90, 120), "Касса", fonts["normal"],
              text_color=(255, 255, 255))

    # Зона выдачи визуально меняется, когда заказ готов (Задание 11)
    if state["order_state"] == READY:
        draw_zone(screen, PICKUP_ZONE, (80, 210, 110), "Зона выдачи", fonts["normal"])
        draw_text(screen, fonts["small"], "ЗАКАЗ ГОТОВ!",
                  (PICKUP_ZONE.centerx, PICKUP_ZONE.centery + 30),
                  (20, 90, 40), center=True)
        pygame.draw.rect(screen, (20, 140, 60), PICKUP_ZONE, 5)
    else:
        draw_zone(screen, PICKUP_ZONE, (190, 190, 195), "Зона выдачи", fonts["normal"])

    player = state["player"]
    center = (int(player["x"]), int(player["y"]))
    pygame.draw.circle(screen, player["color"], center, player["radius"])
    pygame.draw.circle(screen, (20, 20, 20), center, player["radius"], 2)


def draw_cooking_indicator(screen, state, fonts):
    """Задание 10: название, оставшееся время и полоса прогресса."""
    box = pygame.Rect(270, 12, 440, 96)
    if state["order_state"] not in (WAITING, READY):
        return
    pygame.draw.rect(screen, (252, 252, 252), box, border_radius=8)
    pygame.draw.rect(screen, (60, 60, 60), box, 2, border_radius=8)

    bar = pygame.Rect(box.x + 15, box.y + 62, box.width - 30, 22)
    if state["order_state"] == WAITING:
        progress = 1.0 - state["cook_left"] / state["cook_total"]
        draw_text(screen, fonts["normal"], f"Готовится: {state['order_name']}",
                  (box.x + 15, box.y + 8))
        draw_text(screen, fonts["normal"], f"Осталось: {state['cook_left']:.1f} с",
                  (box.x + 15, box.y + 34))
        fill_color = (240, 160, 40)
    else:
        progress = 1.0
        draw_text(screen, fonts["normal"], f"Заказ готов: {state['order_name']}",
                  (box.x + 15, box.y + 8), (20, 120, 50))
        draw_text(screen, fonts["normal"], "Заберите его в зоне выдачи",
                  (box.x + 15, box.y + 34))
        fill_color = (60, 190, 90)

    pygame.draw.rect(screen, (215, 215, 215), bar)
    pygame.draw.rect(screen, fill_color, (bar.x, bar.y, int(bar.width * progress), bar.height))
    pygame.draw.rect(screen, (60, 60, 60), bar, 2)


def draw_info_panel(screen, state, fonts, fps):
    """Задание 12: информационная панель."""
    panel = pygame.Rect(10, 10, 235, 190)
    pygame.draw.rect(screen, (252, 252, 252), panel, border_radius=8)
    pygame.draw.rect(screen, (60, 60, 60), panel, 2, border_radius=8)

    cooking = f"{state['cook_left']:.1f} s" if state["order_state"] == WAITING else "—"
    lines = [
        f"Money: {state['money']} ₽",
        f"Order: {state['order_name'] or '—'}",
        f"State: {state['order_state']}",
        f"Cooking: {cooking}",
        f"FPS: {fps:.0f}",
        "Action:",
        get_action_hint(state),
    ]
    for i, line in enumerate(lines):
        draw_text(screen, fonts["small"], line, (panel.x + 12, panel.y + 8 + i * 24))


def draw_menu(screen, state, fonts):
    """Задание 6: графическое меню заказа."""
    box = pygame.Rect(0, 0, 620, 330)
    box.center = (WIDTH // 2, HEIGHT // 2 + 40)
    pygame.draw.rect(screen, (255, 250, 240), box, border_radius=10)
    pygame.draw.rect(screen, (60, 60, 60), box, 3, border_radius=10)
    draw_text(screen, fonts["big"], "Меню заказа", (box.centerx, box.y + 28), center=True)

    for i, item in enumerate(state["products"]):
        y = box.y + 62 + i * 46
        color = (30, 30, 30) if item["stock"] > 0 else (160, 160, 160)
        text = (f"{i + 1}. {item['name']} — {item['price']} ₽   "
                f"(остаток: {item['stock']}, готовка: {item['cook_time']} с)")
        draw_text(screen, fonts["normal"], text, (box.x + 25, y), color)

    draw_text(screen, fonts["small"], "1–4 — выбрать товар,  0 / Backspace / E — закрыть без покупки",
              (box.centerx, box.bottom - 55), center=True)
    if state["message"]:
        draw_text(screen, fonts["normal"], state["message"],
                  (box.centerx, box.bottom - 22), (180, 40, 40), center=True)


def draw_ui(screen, state, fonts, fps):
    """Задания 6, 10, 12: интерфейс поверх сцены."""
    draw_info_panel(screen, state, fonts, fps)
    draw_cooking_indicator(screen, state, fonts)

    if state["menu_open"]:
        draw_menu(screen, state, fonts)
    elif state["message"]:
        draw_text(screen, fonts["big"], state["message"],
                  (WIDTH // 2, HEIGHT - 40), (30, 90, 160), center=True)

    # Подсказка рядом с зоной (Задание 5)
    hint = get_action_hint(state)
    if hint.startswith("E —") and not state["menu_open"]:
        draw_text(screen, fonts["normal"], hint,
                  (int(state["player"]["x"]), int(state["player"]["y"]) - 32),
                  (20, 20, 20), center=True)


# ---------------------------------------------------------------------------
# Задание 13. Главная функция
# ---------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))      # Задание 1
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    fonts = create_fonts()
    state = create_state()

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)           # delta time в секундах

        running = handle_events(state, pygame.event.get())
        if not state["menu_open"]:
            handle_movement(state["player"], pygame.key.get_pressed(), dt)
        update_order(state, dt)

        draw_scene(screen, state, fonts)
        draw_ui(screen, state, fonts, clock.get_fps())
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

import pygame
import random
import sys
import math

pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

GREEN = (34, 139, 34)
GRAY = (100, 100, 100)
DARK_GRAY = (60, 60, 60)
WHITE = (255, 255, 255)
YELLOW = (250, 210, 20)
RED = (220, 20, 60)
BLUE = (20, 80, 220)
DARK_BLUE = (10, 40, 130)
BROWN = (120, 70, 30)
DARK_GREEN = (15, 80, 15)
GOLD = (255, 215, 0)
BLACK = (20, 20, 20)
HILL_COLOR = (28, 115, 28)
ROOF_COLOR = (180, 60, 40)
WINDOW_COLOR = (240, 240, 150)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Car")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24, True)
small_font = pygame.font.SysFont("Arial", 20, True)

high_score = 0


BOOST_DURATION = 300
BOOST_MULTIPLIER = 1.10

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.size = 24
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.animation_timer = random.uniform(0, 10)
        self.update_sprite()

    def update_sprite(self):
        self.image.fill((0, 0, 0, 0))
        pulse = math.sin(self.animation_timer) * 2
        radius = int(10 + pulse)
        pygame.draw.circle(self.image, (180, 140, 10), (self.size // 2, self.size // 2), radius)
        pygame.draw.circle(self.image, GOLD, (self.size // 2, self.size // 2), radius - 2)
        pygame.draw.circle(self.image, WHITE, (self.size // 2 - 2, self.size // 2 - 2), radius // 3)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, camera):
        self.animation_timer += 0.1
        self.update_sprite()
        self.rect.center = camera.apply(self.pos)


class Camera:
    def __init__(self):
        self.pos = pygame.math.Vector2(0, 0)

    def update(self, target_pos):
        self.pos.x += (target_pos.x - SCREEN_WIDTH // 2 - self.pos.x) * 0.08
        self.pos.y += (target_pos.y - SCREEN_HEIGHT // 2 - self.pos.y) * 0.08

    def apply(self, entity_pos):
        return entity_pos - self.pos


class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(3, 14)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = random.randint(4, 11)
        self.color = random.choice([(255, 60, 0), (255, 150, 0), (255, 220, 30), (100, 100, 100)])
        self.life = random.randint(40, 75)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.radius > 0.3:
            self.radius -= 0.12

    def draw(self, surface, camera):
        if self.life > 0 and self.radius > 0:
            sp = camera.apply(pygame.math.Vector2(self.x, self.y))
            pygame.draw.circle(surface, self.color, (int(sp.x), int(sp.y)), int(self.radius))


class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.particles = [Particle(x, y) for _ in range(180)]
        self.shockwave = 5
        self.active = True

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]
        self.shockwave += 5
        if not self.particles and self.shockwave > 150:
            self.active = False

    def draw(self, surface, camera):
        for p in self.particles:
            p.draw(surface, camera)
        if self.shockwave < 130:
            alpha = max(0, 255 - self.shockwave * 2)
            wave_surf = pygame.Surface((self.shockwave * 2, self.shockwave * 2), pygame.SRCALPHA)
            pygame.draw.circle(wave_surf, (255, 80, 10, alpha), (self.shockwave, self.shockwave), self.shockwave,
                               min(6, int(self.shockwave)))
            sp = camera.apply(pygame.math.Vector2(self.x, self.y))
            surface.blit(wave_surf, (sp.x - self.shockwave, sp.y - self.shockwave))


class StaticObstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.width = width
        self.height = height
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.mask = None

    def update_rect(self, camera):
        self.rect.topleft = camera.apply(self.pos)


class DetailedTree(StaticObstacle):
    def __init__(self, x, y):
        super().__init__(x, y, 90, 90)
        pygame.draw.circle(self.image, (0, 0, 0, 60), (45, 50), 38)
        pygame.draw.circle(self.image, DARK_GREEN, (45, 45), 35)
        pygame.draw.circle(self.image, GREEN, (40, 40), 28)
        pygame.draw.circle(self.image, (50, 180, 50), (35, 35), 18)
        pygame.draw.circle(self.image, BROWN, (45, 45), 6)

        self.coll_surf = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(self.coll_surf, (255, 255, 255), (45, 45), 26)
        self.mask = pygame.mask.from_surface(self.coll_surf)


class DetailedHouse(StaticObstacle):
    def __init__(self, x, y):
        w = random.randint(150, 250)
        h = random.randint(150, 250)
        super().__init__(x, y, w, h)

        pygame.draw.rect(self.image, (0, 0, 0, 50), (5, 5, w, h), border_radius=4)
        wall_color = random.choice([(210, 180, 140), (230, 220, 200), (170, 190, 200)])
        pygame.draw.rect(self.image, wall_color, (0, 0, w, h), border_radius=4)

        pygame.draw.rect(self.image, ROOF_COLOR, (10, 10, w - 20, h - 20), border_radius=2)
        for i in range(15, w - 20, 12):
            pygame.draw.line(self.image, (140, 40, 30), (i, 10), (i, h - 10), 2)

        for ox in range(25, w - 20, 40):
            pygame.draw.rect(self.image, WINDOW_COLOR, (ox, 2, 14, 6))
            pygame.draw.rect(self.image, WINDOW_COLOR, (ox, h - 8, 14, 6))

        self.mask = pygame.mask.from_surface(self.image)


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, body_color):
        super().__init__()
        self.width = width
        self.height = height
        self.body_color = body_color

        self.base_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.build_sprite()

        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.angle = 0
        self.speed = 0
        self.max_speed = 6
        self.acceleration = 0.15
        self.friction = 0.04
        self.steer_speed = 3.6
        self.mask = pygame.mask.from_surface(self.image)

    def build_sprite(self):
        pass

    def rotate_and_sync(self, camera):
        self.angle %= 360
        self.image = pygame.transform.rotate(self.base_image, -self.angle)
        self.rect = self.image.get_rect(center=camera.apply(self.pos))
        self.mask = pygame.mask.from_surface(self.image)


class Player(Vehicle):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 72, RED)
        self.max_speed = 8.5
        self.base_max_speed = 8.5

    def build_sprite(self):
        w, h = self.width, self.height
        pygame.draw.rect(self.base_image, BLACK, (-1, 10, 4, 14), border_radius=2)
        pygame.draw.rect(self.base_image, BLACK, (w - 3, 10, 4, 14), border_radius=2)
        pygame.draw.rect(self.base_image, BLACK, (-1, 50, 4, 14), border_radius=2)
        pygame.draw.rect(self.base_image, BLACK, (w - 3, 50, 4, 14), border_radius=2)
        pygame.draw.rect(self.base_image, self.body_color, (2, 0, w - 4, h), border_radius=8)
        pygame.draw.rect(self.base_image, BLACK, (w // 2 - 4, 2, 8, 20))
        pygame.draw.rect(self.base_image, (100, 200, 255), (6, 24, w - 12, 14), border_radius=2)
        pygame.draw.rect(self.base_image, (70, 160, 220), (7, 48, w - 14, 10), border_radius=1)
        pygame.draw.rect(self.base_image, WHITE, (5, 0, 6, 3), border_radius=1)
        pygame.draw.rect(self.base_image, WHITE, (w - 11, 0, 6, 3), border_radius=1)
        pygame.draw.rect(self.base_image, BLACK, (0, h - 4, w, 4), border_radius=1)

    def update(self, camera):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed = min(self.max_speed, self.speed + self.acceleration)
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed = max(-self.max_speed / 2, self.speed - self.acceleration)
        else:
            if self.speed > 0:
                self.speed = max(0, self.speed - self.friction)
            elif self.speed < 0:
                self.speed = min(0, self.speed + self.friction)

        if self.speed != 0:
            dir_mod = 1 if self.speed > 0 else -1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.angle -= self.steer_speed * dir_mod
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.angle += self.steer_speed * dir_mod

        rad = math.radians(self.angle)
        self.velocity.x = math.sin(rad) * self.speed
        self.velocity.y = -math.cos(rad) * self.speed
        self.pos += self.velocity
        self.rotate_and_sync(camera)


class PoliceCar(Vehicle):
    def __init__(self, x, y):
        super().__init__(x, y, 40, 72, DARK_BLUE)
        self.max_speed = 7.5
        self.flash = 0

    def build_sprite(self):
        w, h = self.width, self.height
        pygame.draw.rect(self.base_image, BLACK, (-1, 10, 4, 14))
        pygame.draw.rect(self.base_image, BLACK, (w - 3, 10, 4, 14))
        pygame.draw.rect(self.base_image, BLACK, (2, 0, w - 4, h), border_radius=6)
        pygame.draw.rect(self.base_image, WHITE, (2, 22, w - 4, 25))
        pygame.draw.rect(self.base_image, (80, 80, 90), (6, 22, w - 12, 12))
        pygame.draw.rect(self.base_image, RED, (6, 36, w // 2 - 6, 5))
        pygame.draw.rect(self.base_image, BLUE, (w // 2, 36, w // 2 - 6, 5))

    def update(self, target_pos, camera):
        to_target = target_pos - self.pos
        t_angle = math.degrees(math.atan2(to_target.x, -to_target.y)) % 360
        diff = (t_angle - self.angle + 180) % 360 - 180
        if diff > 3:
            self.angle += self.steer_speed * 0.8
        elif diff < -3:
            self.angle -= self.steer_speed * 0.8

        self.speed = min(self.max_speed, self.speed + self.acceleration)
        rad = math.radians(self.angle)
        self.velocity.x = math.sin(rad) * self.speed
        self.velocity.y = -math.cos(rad) * self.speed
        self.pos += self.velocity

        self.flash += 1
        if self.flash % 8 == 0:
            color1 = BLUE if (self.flash % 16 == 0) else RED
            color2 = RED if (self.flash % 16 == 0) else BLUE
            pygame.draw.rect(self.base_image, color1, (6, 36, self.width // 2 - 6, 5))
            pygame.draw.rect(self.base_image, color2, (self.width // 2, 36, self.width // 2 - 6, 5))

        self.rotate_and_sync(camera)


class PoliceVan(Vehicle):
    def __init__(self, x, y):
        super().__init__(x, y, 48, 85, BLACK)
        self.max_speed = 6.2
        self.flash = 0

    def build_sprite(self):
        w, h = self.width, self.height
        pygame.draw.rect(self.base_image, DARK_GRAY, (-2, 12, 6, 18))
        pygame.draw.rect(self.base_image, DARK_GRAY, (w - 4, 12, 6, 18))
        pygame.draw.rect(self.base_image, DARK_GRAY, (-2, 58, 6, 18))
        pygame.draw.rect(self.base_image, DARK_GRAY, (w - 4, 58, 6, 18))
        pygame.draw.rect(self.base_image, (30, 35, 45), (2, 0, w - 4, h), border_radius=4)
        pygame.draw.rect(self.base_image, DARK_GRAY, (6, 0, w - 12, 4))
        pygame.draw.rect(self.base_image, (5, 25, 45), (6, 20, w - 12, 10))
        pygame.draw.circle(self.base_image, DARK_GRAY, (w // 2, 48), 10, 2)
        pygame.draw.rect(self.base_image, BLUE, (8, 2, 8, 4))
        pygame.draw.rect(self.base_image, RED, (w - 16, 2, 8, 4))

    def update(self, target_pos, camera):
        to_target = target_pos - self.pos
        t_angle = math.degrees(math.atan2(to_target.x, -to_target.y)) % 360
        diff = (t_angle - self.angle + 180) % 360 - 180
        if diff > 2:
            self.angle += self.steer_speed * 0.65
        elif diff < -2:
            self.angle -= self.steer_speed * 0.65

        self.speed = min(self.max_speed, self.speed + self.acceleration)
        rad = math.radians(self.angle)
        self.velocity.x = math.sin(rad) * self.speed
        self.velocity.y = -math.cos(rad) * self.speed
        self.pos += self.velocity

        self.flash += 1
        if self.flash % 6 == 0:
            c1 = RED if (self.flash % 12 == 0) else BLUE
            c2 = BLUE if (self.flash % 12 == 0) else RED
            pygame.draw.rect(self.base_image, c1, (8, 2, 8, 4))
            pygame.draw.rect(self.base_image, c2, (self.width - 16, 2, 8, 4))

        self.rotate_and_sync(camera)


class CityGrid:
    def __init__(self):
        self.cell_size = 1400
        self.road_width = 240
        self.loaded_cells = {}
        self.obstacles = pygame.sprite.Group()
        self.parking_slots = []

    def get_cell_coords(self, pos):
        cx = int(pos.x // self.cell_size)
        cy = int(pos.y // self.cell_size)
        return cx, cy

    def is_on_road(self, local_x, local_y):
        half_r = self.road_width / 2
        mid = self.cell_size / 2
        in_v_road = (mid - half_r <= local_x <= mid + half_r)
        in_h_road = (mid - half_r <= local_y <= mid + half_r)
        return in_v_road or in_h_road

    def is_in_parking(self, local_x, local_y):
        mid = self.cell_size / 2
        rw = self.road_width / 2
        if (mid + rw + 20 <= local_x <= mid + rw + 180) and (mid - rw - 220 <= local_y <= mid - rw - 20):
            return True
        return False

    def generate_cell(self, cx, cy):
        if (cx, cy) in self.loaded_cells:
            return

        cell_start_x = cx * self.cell_size
        cell_start_y = cy * self.cell_size

        mid = self.cell_size / 2
        rw = self.road_width / 2
        self.parking_slots.append(pygame.math.Vector2(cell_start_x + mid + rw + 20, cell_start_y + mid - rw - 220))

        for _ in range(5):
            for attempt in range(10):
                lx = random.randint(100, self.cell_size - 300)
                ly = random.randint(100, self.cell_size - 300)
                if not self.is_on_road(lx, ly) and not self.is_on_road(lx + 220, ly + 180) and not self.is_in_parking(
                        lx, ly):
                    house = DetailedHouse(cell_start_x + lx, cell_start_y + ly)
                    self.obstacles.add(house)
                    break

        for _ in range(12):
            for attempt in range(10):
                lx = random.randint(50, self.cell_size - 100)
                ly = random.randint(50, self.cell_size - 100)
                if not self.is_on_road(lx - 40, ly - 40) and not self.is_on_road(lx + 40,
                                                                                 ly + 40) and not self.is_in_parking(
                        lx, ly):
                    tree = DetailedTree(cell_start_x + lx, cell_start_y + ly)
                    self.obstacles.add(tree)
                    break

        self.loaded_cells[(cx, cy)] = True
        self.spawn_coins_in_cell(cx, cy)

    def spawn_coins_in_cell(self, cx, cy):
        cell_start_x = cx * self.cell_size
        cell_start_y = cy * self.cell_size

        num_coins = random.randint(2, 5)

        for _ in range(num_coins):
            for attempt in range(15):
                lx = random.uniform(80, self.cell_size - 80)
                ly = random.uniform(80, self.cell_size - 80)

                if not self.is_on_road(lx, ly):
                    continue

                if self.is_in_parking(lx, ly):
                    continue

                coin = Coin(cell_start_x + lx, cell_start_y + ly)
                coins.add(coin)
                break

    def update(self, player_pos, camera):
        cx, cy = self.get_cell_coords(player_pos)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                self.generate_cell(cx + dx, cy + dy)

        for obj in self.obstacles:
            obj.update_rect(camera)

    def draw_roads(self, surface, camera, player_pos):
        cx, cy = self.get_cell_coords(player_pos)
        half_r = self.road_width / 2
        mid = self.cell_size / 2

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                ccx = cx + dx
                ccy = cy + dy
                csx = ccx * self.cell_size
                csy = ccy * self.cell_size

                v_road_topleft = camera.apply(pygame.math.Vector2(csx + mid - half_r, csy))
                h_road_topleft = camera.apply(pygame.math.Vector2(csx, csy + mid - half_r))

                pygame.draw.rect(surface, GRAY, (v_road_topleft.x, v_road_topleft.y, self.road_width, self.cell_size))
                pygame.draw.rect(surface, GRAY, (h_road_topleft.x, h_road_topleft.y, self.cell_size, self.road_width))

                p_pos = camera.apply(pygame.math.Vector2(csx + mid + half_r, csy + mid - half_r - 200))
                pygame.draw.rect(surface, DARK_GRAY, (p_pos.x, p_pos.y, 160, 200), border_radius=3)
                for py in range(int(p_pos.y) + 20, int(p_pos.y) + 200, 40):
                    pygame.draw.line(surface, WHITE, (p_pos.x, py), (p_pos.x + 40, py), 2)

                for step in range(0, self.cell_size, 60):
                    v_line = camera.apply(pygame.math.Vector2(csx + mid, csy + step))
                    h_line = camera.apply(pygame.math.Vector2(csx + step, csy + mid))
                    pygame.draw.rect(surface, YELLOW, (v_line.x - 2, v_line.y, 4, 30))
                    pygame.draw.rect(surface, YELLOW, (h_line.x, h_line.y - 2, 30, 4))


camera = Camera()
city = CityGrid()
player = Player(city.cell_size // 2, city.cell_size // 2)
police_squad = pygame.sprite.Group()
coins = pygame.sprite.Group()

score = 0
coins_collected = 0
score_timer = 0
police_spawn_timer = 0
explosion_effect = None
game_over = False

# ================== ПЕРЕМЕННЫЕ БУСТА ==================
boost_available = False   # набрано 10 монет — можно ускориться
boost_active = False      # буст активен прямо сейчас
boost_timer = 0           # сколько кадров ещё действует буст
boost_cost = 10           # цена ускорения в монетах
# ======================================================

running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # ---- Активация буста клавишей T ----
        if event.type == pygame.KEYDOWN and event.key == pygame.K_t and not game_over:
            if boost_available and not boost_active:
                boost_active = True
                boost_timer = BOOST_DURATION
                boost_available = False
                # Снимаем 10 монет с общего счётчика — используем их как топливо
                coins_collected -= boost_cost
                player.max_speed = player.base_max_speed * BOOST_MULTIPLIER

        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_r:
                player = Player(city.cell_size // 2, city.cell_size // 2)
                police_squad.empty()
                coins.empty()
                score = 0
                coins_collected = 0
                score_timer = 0
                police_spawn_timer = 0
                explosion_effect = None
                game_over = False
                city.loaded_cells = {}
                boost_available = False
                boost_active = False
                boost_timer = 0

    if not game_over:
        # ---- Таймер буста: снимаем эффект по истечении ----
        if boost_active:
            boost_timer -= 1
            if boost_timer <= 0:
                boost_active = False
                player.max_speed = player.base_max_speed

        player.update(camera)
        camera.update(player.pos)
        city.update(player.pos, camera)

        for cop in police_squad:
            cop.update(player.pos, camera)

        for coin in coins:
            coin.update(camera)

        collected = pygame.sprite.spritecollide(player, coins, True, pygame.sprite.collide_mask)
        if collected:
            count = len(collected)
            score += 10 * count
            coins_collected += count
            # Каждые 10 собранных монет даём право на ускорение
            if coins_collected >= boost_cost:
                boost_available = True

        score_timer += 1
        if score_timer >= 60:
            score += 1
            score_timer = 0

        police_spawn_timer += 1
        if police_spawn_timer >= 180 and len(police_squad) < 8:
            police_spawn_timer = 0
            spawn_angle = random.uniform(0, math.pi * 2)
            spawn_dist = 700
            spawn_x = player.pos.x + math.cos(spawn_angle) * spawn_dist
            spawn_y = player.pos.y + math.sin(spawn_angle) * spawn_dist

            if random.choice([True, False]):
                police_squad.add(PoliceCar(spawn_x, spawn_y))
            else:
                police_squad.add(PoliceVan(spawn_x, spawn_y))

        for cop in police_squad:
            if pygame.sprite.collide_mask(player, cop):
                game_over = True
                explosion_effect = Explosion(player.pos.x, player.pos.y)
                break

        if not game_over:
            for obs in city.obstacles:
                if player.rect.colliderect(obs.rect):
                    if pygame.sprite.collide_mask(player, obs):
                        game_over = True
                        explosion_effect = Explosion(player.pos.x, player.pos.y)
                        break

        if game_over:
            if score > high_score:
                high_score = score

        for coin in list(coins):
            if math.sqrt((coin.pos.x - player.pos.x) ** 2 + (coin.pos.y - player.pos.y) ** 2) > 3000:
                coin.kill()

        for cop in list(police_squad):
            if math.sqrt((cop.pos.x - player.pos.x) ** 2 + (cop.pos.y - player.pos.y) ** 2) > 1600:
                cop.kill()
    else:
        if explosion_effect and explosion_effect.active:
            explosion_effect.update()

    screen.fill(GREEN)
    city.draw_roads(screen, camera, player.pos)

    sorted_obstacles = sorted(city.obstacles.sprites(), key=lambda o: o.pos.y)
    for obs in sorted_obstacles:
        screen.blit(obs.image, obs.rect.topleft)

    for coin in coins:
        screen.blit(coin.image, coin.rect.topleft)

    for cop in police_squad:
        screen.blit(cop.image, cop.rect.topleft)
    if not game_over:
        screen.blit(player.image, player.rect.topleft)

    if explosion_effect and explosion_effect.active:
        explosion_effect.draw(screen, camera)

    score_lbl = font.render("Score: " + str(score), True, WHITE)
    best_lbl = font.render("Record: " + str(high_score), True, GOLD)
    coins_lbl = font.render("Coins: " + str(coins_collected), True, YELLOW)

    pygame.draw.rect(screen, BLACK, (10, 10, 150, 40), border_radius=6)
    pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - 200, 10, 190, 40), border_radius=6)
    pygame.draw.rect(screen, BLACK, (10, 60, 150, 40), border_radius=6)
    pygame.draw.rect(screen, BLACK, (10, 110, 220, 40), border_radius=6)
    screen.blit(score_lbl, (25, 17))
    screen.blit(best_lbl, (SCREEN_WIDTH - 185, 17))
    screen.blit(coins_lbl, (25, 67))

    # ---- Табличка подсказки про ускорение ----
    if game_over:
        go_surf = font.render("CRASHED Score: " + str(score), True, WHITE)
        restart_surf = font.render("Press 'R' to Restart", True, GOLD)
        go_rect = go_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        rest_rect = restart_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))

        pygame.draw.rect(screen, BLACK, go_rect.inflate(40, 60), border_radius=10)
        screen.blit(go_surf, go_rect)
        screen.blit(restart_surf, rest_rect)
    elif boost_active:
        # Во время буста показываем обратный отсчёт
        seconds_left = max(0, boost_timer // FPS)
        boost_lbl = small_font.render("BOOST! (" + str(seconds_left) + " sec)", True, (0, 255, 100))
        pygame.draw.rect(screen, (0, 60, 20), (10, 110, 220, 40), border_radius=6)
        screen.blit(boost_lbl, (25, 117))
    elif boost_available:
        # Готово к использованию — большая заметная подсказка
        hint_lbl = small_font.render("Press 'T' to boost for " + str(boost_cost) + " coins!", True, GOLD)
        pygame.draw.rect(screen, (60, 45, 0), (10, 110, 300, 40), border_radius=6)
        screen.blit(hint_lbl, (22, 117))
    else:
        # Пока монет мало — мягкая подсказка, что буст накопится
        hint_lbl = small_font.render("Collect 10 coins to enable boost (T)", True, WHITE)
        pygame.draw.rect(screen, (30, 30, 30), (10, 110, 320, 40), border_radius=6)
        screen.blit(hint_lbl, (22, 117))

    pygame.display.flip()

pygame.quit()
sys.exit()

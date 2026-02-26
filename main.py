import pygame
import random
import os

# --- INITIALIZATION ---
pygame.init()
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wall Street Climber")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.SysFont("Arial", 26, bold=True)
title_font = pygame.font.SysFont("Arial", 42, bold=True)
small_font = pygame.font.SysFont("Arial", 18, bold=True)

# File Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
bg_names = ["background.png", "nightbackground.png", "snowbackground.png"]
theme_labels = ["Day", "Night", "Snow"]

# Persistent files
high_score_file = os.path.join(script_dir, "highscore.txt")
bank_file = os.path.join(script_dir, "bank.txt")

# --- SETTINGS & STATE ---
volume = 0.5  # Default 50%
state = 0     # 0: Menu, 1: Game, 2: Game Over, 3: Settings
diff_list = ["Easy", "Medium", "Difficult"]
diff_idx = 1
theme_idx = 0
# Colors
WHITE, GOLD, BLACK = (255, 255, 255), (255, 215, 0), (0, 0, 0)
BTN_BG, CYAN, PLAYER_RED = (45, 45, 45), (0, 255, 255), (255, 100, 100)
DANGER_RED, PENNY_FILL, PENNY_HIGHLIGHT = (255, 60, 60), (184, 115, 51), (230, 170, 120)

# --- SHOP DATA ---
wardrobe_file = os.path.join(script_dir, "wardrobe.txt")
# Format: Name, Color, Price
SUITS = [("Navy", (40, 44, 52), 0), ("Charcoal", (60, 60, 60), 1000), ("Gold", (212, 175, 55), 5000), ("Emerald", (0, 100, 50), 10000),("Platinum", (229, 228, 226), 999900)]
TIES = [("Red", DANGER_RED, 0), ("Blue", (50, 50, 200), 500), ("Green", (50, 150, 50), 750), ("Pink", (255, 105, 180), 1200),("Diamond", (185, 242, 255), 999900)]

owned_suits = ["Navy"]
owned_ties = ["Red"]
eq_suit_idx = 0
eq_tie_idx = 0

# Load unlocked items
if os.path.exists(wardrobe_file):
    try:
        with open(wardrobe_file, "r") as f:
            lines = f.read().splitlines()
            owned_suits = lines[0].split(",")
            owned_ties = lines[1].split(",")
            eq_suit_idx = int(lines[2])
            eq_tie_idx = int(lines[3])
    except: pass

def save_wardrobe():
    with open(wardrobe_file, "w") as f:
        f.write(f"{','.join(owned_suits)}\n{','.join(owned_ties)}\n{eq_suit_idx}\n{eq_tie_idx}")

# --- HIGH SCORE & BANK SETUP ---
high_score = 0
if os.path.exists(high_score_file):
    try:
        with open(high_score_file, "r") as f:
            high_score = int(f.read())
    except: pass

bank_cents = 0
if os.path.exists(bank_file):
    try:
        with open(bank_file, "r") as f:
            bank_cents = int(f.read())
    except: bank_cents = 0

def save_high_score(score):
    try:
        with open(high_score_file, "w") as f:
            f.write(str(score))
    except: pass

def save_bank(cents):
    try:
        with open(bank_file, "w") as f:
            f.write(str(int(cents)))
    except: pass

def fmt_money(cents: int) -> str:
    dollars = cents // 100
    rem = cents % 100
    return f"${dollars:,}.{rem:02d}"

# --- ASSET LOADING ---
BG_IMAGES = []
for name in bg_names:
    path = os.path.join(script_dir, name)
    try:
        img = pygame.image.load(path).convert()
        BG_IMAGES.append(pygame.transform.scale(img, (WIDTH, HEIGHT)))
    except:
        fallbacks = [(135, 206, 235), (20, 24, 82), (200, 230, 255)]
        idx = len(BG_IMAGES)
        fallback = pygame.Surface((WIDTH, HEIGHT))
        fallback.fill(fallbacks[idx] if idx < len(fallbacks) else (40, 40, 60))
        BG_IMAGES.append(fallback)
try:
    MONEY_BAG_IMG = pygame.image.load(os.path.join(script_dir, "moneybag.png")).convert_alpha()
    MONEY_BAG_IMG = pygame.transform.scale(MONEY_BAG_IMG, (35, 35)) # Match your current size
except: 
    MONEY_BAG_IMG = None
try:
    PLAYER_IMG = pygame.image.load(os.path.join(script_dir, "character.png")).convert_alpha()
    PLAYER_IMG = pygame.transform.scale(PLAYER_IMG, (25, 50))
except: PLAYER_IMG = None

try:
    HELI_IMG = pygame.image.load(os.path.join(script_dir, "helicopter.png")).convert_alpha()
    HELI_IMG = pygame.transform.scale(HELI_IMG, (60, 30))
except: HELI_IMG = None

try:
    SHIELD_IMG = pygame.image.load(os.path.join(script_dir, "shield.png")).convert_alpha()
    SHIELD_IMG = pygame.transform.scale(SHIELD_IMG, (30, 30))
except: SHIELD_IMG = None

# --- SOUNDS ---
def load_sound(name):
    try: return pygame.mixer.Sound(os.path.join(script_dir, name))
    except: return None

SND_JUMP = load_sound("jump.mp3")
SND_LAND = load_sound("land.ogg")
SND_MENU = load_sound("menuclick.ogg")
SND_DEATH = load_sound("death.ogg")
SND_MONEY = load_sound("moneyearned.mp3")
SND_PENNIES_LAND = load_sound("penniesland.mp3")

def play(sound):
    if sound:
        sound.set_volume(volume)
        sound.play()

def load_plat(name):
    try:
        path = os.path.join(script_dir, name)
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (100, 18))
    except: return None

PLAT_ASSETS = {
    "standard": load_plat("platform.png"),
    "horiz": load_plat("horizontalplatform.png"),
    "vert": load_plat("verticalplatform.png"),
    "snow_std": load_plat("snowplatform.png"),
    "snow_horiz": load_plat("snowyhorizontal.png"),
    "snow_vert": load_plat("snowyvertical.png"),
}



# --- CLASSES ---

class Environment:
    def __init__(self, bg_index):
        self.bg_y = 0
        self.bg_index = bg_index
        self.snow_particles = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(1, 3), random.randint(2, 4)] for _ in range(80)]
        self.clouds = []
        for _ in range(6):
            scale = random.uniform(0.6, 1.2)
            offsets = [(random.randint(-20, 20) * scale, random.randint(-10, 10) * scale, random.randint(15, 25) * scale) for _ in range(4)]
            self.clouds.append([random.randint(0, WIDTH), random.randint(0, 400), random.uniform(0.2, 0.5), scale, offsets])

    def draw(self, surface, scroll_speed):
        self.bg_y += scroll_speed * 0.5
        if self.bg_y >= 0: self.bg_y = 0
        surface.blit(BG_IMAGES[self.bg_index], (0, int(self.bg_y)))

        if self.bg_index == 2:
            for flake in self.snow_particles:
                flake[1] += flake[2] + (scroll_speed if scroll_speed > 0 else 0)
                if flake[1] > HEIGHT: flake[1], flake[0] = -10, random.randint(0, WIDTH)
                pygame.draw.circle(surface, (255, 255, 255, 180), (int(flake[0]), int(flake[1])), flake[3])

        for c in self.clouds:
            c[0] = (c[0] + c[2]) % (WIDTH + 100)
            for ox, oy, rad in c[4]:
                cloud_surf = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
                alpha = 100 if self.bg_index != 1 else 60
                pygame.draw.circle(cloud_surf, (255, 255, 255, alpha), (rad, rad), rad)
                surface.blit(cloud_surf, (int(c[0] + ox - rad), int(c[1] + oy - rad)))

class Player:
    def __init__(self):
        self.rect = pygame.Rect(200, 500, 25, 50)
        self.vel_y = 0
        self.height_ft = 0
        self.pixels_climbed = 0
        self.on_ground = False
        self.current_platform = None
        self.has_shield = False
        self.invincible = False
        self.invincible_timer = 0
        self.run_cents = 0
        self.last_bonus_bucket = 0

    def draw(self, surface):
        if self.invincible and (pygame.time.get_ticks() // 100) % 2 == 0:
            return

        x, y = self.rect.x, self.rect.y
        w, h = self.rect.width, self.rect.height
        
        # Use currently equipped colors
        current_suit_color = SUITS[eq_suit_idx][1]
        current_tie_color = TIES[eq_tie_idx][1]

        # 1. DRAW BODY (The Suit)
        pygame.draw.rect(surface, current_suit_color, (x, y + 15, w, h - 15), border_radius=3)

        # 2. DRAW HEAD
        pygame.draw.rect(surface, (255, 219, 172), (x + 5, y, w - 10, 15), border_radius=4)

        # 3. DRAW THE SHIRT & TIE
        pygame.draw.polygon(surface, WHITE, [(x + 5, y + 15), (x + 20, y + 15), (x + 12, y + 25)])
        pygame.draw.line(surface, current_tie_color, (x + 12, y + 15), (x + 12, y + 28), 3)

        # 4. EYES & SHIELD
        pygame.draw.circle(surface, BLACK, (x + 8, y + 6), 2)
        pygame.draw.circle(surface, BLACK, (x + 17, y + 6), 2)
        if self.has_shield:
            pygame.draw.circle(surface, CYAN, self.rect.center, 38, 3)

    def jump(self):
        if self.on_ground:
            self.vel_y = -18
            self.on_ground = False
            self.current_platform = None
            play(SND_JUMP)

    def apply_gravity(self):
        self.vel_y += 0.8
        self.rect.y += self.vel_y

    def update_invincibility(self):
        if self.invincible and (pygame.time.get_ticks() - self.invincible_timer > 3000):
            self.invincible = False

    def update_height_and_money(self):
        new_height = int(self.pixels_climbed // 10)
        if new_height > self.height_ft:
            delta = new_height - self.height_ft
            self.height_ft = new_height
            self.run_cents += delta 
        bucket = self.height_ft // 250
        if bucket > self.last_bonus_bucket:
            self.run_cents += (bucket - self.last_bonus_bucket) * 500
            self.last_bonus_bucket = bucket
            play(SND_MONEY)

class Platform:
    def __init__(self, x, y, score, difficulty, prev_x=None):
        if prev_x is not None:
            x = random.randint(max(0, prev_x - 150), min(WIDTH - 100, prev_x + 150))
        self.rect = pygame.Rect(x, y, 100, 18)
        speed_mult = 1.8 if difficulty == "Difficult" else 1.2 if difficulty == "Medium" else 1.0
        self.move_type = random.choice([0, 1, 2]) if score > 50 else random.choice([0, 1])
        self.direction, self.speed = 1, random.randint(2, 3) * speed_mult
        self.start_y, self.v_range = y, 60

    def draw(self, surface, bg_index):
        key = "standard"
        if bg_index == 2:
            if self.move_type == 1: key = "snow_horiz"
            elif self.move_type == 2: key = "snow_vert"
            else: key = "snow_std"
        else:
            if self.move_type == 1: key = "horiz"
            elif self.move_type == 2: key = "vert"
            else: key = "standard"
        sprite = PLAT_ASSETS.get(key) or PLAT_ASSETS["standard"]
        if sprite: surface.blit(sprite, (self.rect.x, self.rect.y))
        else: pygame.draw.rect(surface, (100, 100, 105), self.rect)

    def update(self, scroll_speed):
        self.rect.y += scroll_speed
        self.start_y += scroll_speed
        if self.move_type == 1:
            self.rect.x += self.direction * self.speed
            if self.rect.right >= WIDTH or self.rect.left <= 0: self.direction *= -1
        elif self.move_type == 2:
            self.rect.y += self.direction * (self.speed // 2)
            if abs(self.rect.y - self.start_y) > self.v_range: self.direction *= -1

class HeliEnemy:
    def __init__(self, score, difficulty):
        self.rect = pygame.Rect(random.randint(0, WIDTH - 60), -100, 60, 30)
        self.direction = random.choice([-1, 1])
        base_speed = 2 if difficulty == "Easy" else 4 if difficulty == "Medium" else 6
        self.speed = min(9, base_speed + (score / 200))

    def update(self, scroll_vel):
        self.rect.x += self.direction * self.speed
        self.rect.y += scroll_vel
        if self.rect.right >= WIDTH: self.direction = -1
        elif self.rect.left <= 0: self.direction = 1

    def draw(self, surface):
        if HELI_IMG:
            img = pygame.transform.flip(HELI_IMG, True, False) if self.direction == -1 else HELI_IMG
            surface.blit(img, self.rect)
        else: pygame.draw.rect(surface, (30, 50, 100), self.rect, border_radius=5)

class ShieldItem:
    def __init__(self, y):
        self.rect = pygame.Rect(random.randint(50, WIDTH - 50), y, 30, 30)
        self.collected = False
    def update(self, scroll_vel): self.rect.y += scroll_vel
    def draw(self, surface):
        if not self.collected:
            if SHIELD_IMG: surface.blit(SHIELD_IMG, self.rect)
            else: 
                pygame.draw.circle(surface, CYAN, self.rect.center, 15)
                pygame.draw.circle(surface, WHITE, self.rect.center, 15, 2)

class PennyWarning:
    def __init__(self, x, w, delay_ms=900):
        self.x, self.w, self.y, self.h = int(max(0, min(WIDTH - w, x))), int(w), 70, 26
        self.spawn_time, self.delay_ms = pygame.time.get_ticks(), delay_ms
    def ready_to_drop(self): return (pygame.time.get_ticks() - self.spawn_time) >= self.delay_ms
    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        blink_rate = 140 if elapsed < self.delay_ms * 0.6 else 70
        if (pygame.time.get_ticks() // blink_rate) % 2 == 0:
            warn_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            warn_surf.fill((DANGER_RED[0], DANGER_RED[1], DANGER_RED[2], 85))
            surface.blit(warn_surf, (self.x, self.y))
            pygame.draw.rect(surface, DANGER_RED, (self.x, self.y, self.w, self.h), 3, border_radius=7)
            for cx in range(self.x + 10, self.x + self.w - 10, 18):
                pygame.draw.polygon(surface, DANGER_RED, [(cx, self.y + 6), (cx + 10, self.y + 6), (cx + 5, self.y + 18)])

class Penny:
    def __init__(self, x, y, speed):
        self.x, self.y, self.speed, self.r = float(x), float(y), float(speed), 6
        self.rect = pygame.Rect(0, 0, self.r * 2, self.r * 2)
    def update(self):
        self.y += self.speed
        self.rect.center = (int(self.x), int(self.y))
    def draw(self, surface):
        pygame.draw.circle(surface, PENNY_FILL, (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surface, (120, 75, 35), (int(self.x), int(self.y)), self.r, 2)
        pygame.draw.circle(surface, PENNY_HIGHLIGHT, (int(self.x) - 2, int(self.y) - 2), 2)

class MoneyBag:
    def __init__(self, y):
        # We'll keep it 35x35 to match your current layout
        self.rect = pygame.Rect(random.randint(50, WIDTH - 50), y, 35, 35)
        self.collected = False
        self.value = 500  # $5.00

    def update(self, scroll_vel):
        self.rect.y += scroll_vel

    def draw(self, surface):
        if not self.collected:
            if MONEY_BAG_IMG:
                # Draw the cool pixel art image
                surface.blit(MONEY_BAG_IMG, self.rect)
            else:
                # Fallback in case the image file is missing
                pygame.draw.ellipse(surface, (34, 139, 34), (self.rect.x, self.rect.y + 10, 35, 25))
                draw_text("$", small_font, GOLD, self.rect.centerx, self.rect.centery)
# --- GAME FUNCTIONS ---

def reset_game(difficulty, theme_idx):
    p, env = Player(), Environment(theme_idx)
    plats, last_x, curr_y = [], 150, 550
    gap = 100 if difficulty == "Easy" else 130 if difficulty == "Medium" else 155
    for i in range(7):
        new_plat = Platform(last_x, curr_y, 0, difficulty, prev_x=None if i == 0 else last_x)
        plats.append(new_plat)
        last_x, curr_y = new_plat.rect.x, curr_y - gap
    
    # NEW: Return empty lists for everything that could kill you
    return p, plats, [], env, [], 0, [], [], []

def draw_text(text, font_obj, color, x, y, shadow=False):
    if shadow:
        s_img = font_obj.render(text, True, BLACK)
        screen.blit(s_img, s_img.get_rect(center=(x + 2, y + 2)))
    img = font_obj.render(text, True, color)
    rect = img.get_rect(center=(x, y))
    screen.blit(img, rect)
    return rect

def draw_styled_button(surface, text, rect):
    pygame.draw.rect(surface, BTN_BG, rect, border_radius=12)
    pygame.draw.rect(surface, WHITE, rect, width=3, border_radius=12)
    draw_text(text, font, WHITE, rect.centerx, rect.centery)

def get_drop_width(difficulty: str, height_ft: int) -> int:
    if difficulty == "Easy": base, growth, cap = 75, 0.85, 170
    elif difficulty == "Medium": base, growth, cap = 120, .5, 180
    else: base, growth, cap = 150, 1.6, 320
    return max(70, min(cap, int(base + height_ft * growth * 0.06)))



# --- MAIN LOOP ---
# This line sets the ID numbers for the timers
enemy_timer, penny_timer = pygame.USEREVENT + 1, pygame.USEREVENT + 2

# This line sets up the initial game state
player, platforms, helis, env, shields, last_shield_spawn, pennies, penny_warnings, money_bags = reset_game(diff_list[diff_idx], theme_idx)

last_run_cents, deposited_this_gameover, last_landed_platform_id = 0, False, None

running = True
while running:
    # --- STATE 0: MAIN MENU ---
    if state == 0:
        deposited_this_gameover = False
        env.bg_index = theme_idx
        env.draw(screen, 0)
        draw_text("WALL STREET", title_font, GOLD, WIDTH // 2, 80, True)
        draw_text("CLIMBER", title_font, GOLD, WIDTH // 2, 130, True)
        draw_text(f"BANK: {fmt_money(bank_cents)}", small_font, GOLD, WIDTH // 2, 175, True)

        start_btn = pygame.Rect(WIDTH // 2 - 110, 220, 220, 50)
        shop_btn = pygame.Rect(WIDTH // 2 - 110, 290, 220, 50)
        settings_btn = pygame.Rect(WIDTH // 2 - 110, 360, 220, 50)
        
        draw_styled_button(screen, "START CAREER", start_btn)
        draw_styled_button(screen, "THE TAILOR", shop_btn)
        draw_styled_button(screen, "SETTINGS", settings_btn)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.collidepoint(event.pos):
                    # FIX: Added money_bags to the reset line
                    player, platforms, helis, env, shields, last_shield_spawn, pennies, penny_warnings, money_bags = reset_game(diff_list[diff_idx], theme_idx)
                    pygame.time.set_timer(enemy_timer, 3000) 
                    pygame.time.set_timer(penny_timer, 6000) 
                    play(SND_MENU)
                    state = 1
                elif shop_btn.collidepoint(event.pos):
                    play(SND_MENU); state = 4
                elif settings_btn.collidepoint(event.pos):
                    play(SND_MENU); state = 3

    # --- STATE 3: SETTINGS ---
    elif state == 3:
        env.draw(screen, 0)
        draw_text("SETTINGS", title_font, GOLD, WIDTH // 2, 100, True)
        vol_btn = pygame.Rect(WIDTH // 2 - 110, 200, 220, 55); diff_btn = pygame.Rect(WIDTH // 2 - 110, 280, 220, 55)
        theme_btn = pygame.Rect(WIDTH // 2 - 110, 360, 220, 55); back_btn = pygame.Rect(WIDTH // 2 - 110, 460, 220, 55)
        draw_styled_button(screen, f"VOL: {int(volume*100)}%", vol_btn); draw_styled_button(screen, f"MODE: {diff_list[diff_idx]}", diff_btn)
        draw_styled_button(screen, f"THEME: {theme_labels[theme_idx]}", theme_btn); draw_styled_button(screen, "BACK", back_btn)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if vol_btn.collidepoint(event.pos): volume = (volume + 0.1) if volume < 0.9 else 0.0; play(SND_MENU)
                elif diff_btn.collidepoint(event.pos): diff_idx = (diff_idx + 1) % len(diff_list); play(SND_MENU)
                elif theme_btn.collidepoint(event.pos): theme_idx = (theme_idx + 1) % len(theme_labels); env.bg_index = theme_idx; play(SND_MENU)
                elif back_btn.collidepoint(event.pos): state = 0; play(SND_MENU)

    # --- STATE 1: GAMEPLAY ---
    elif state == 1:
        scroll_vel = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == enemy_timer and len(helis) < 2:
                helis.append(HeliEnemy(player.height_ft, diff_list[diff_idx]))
            if event.type == penny_timer and len(penny_warnings) < 1:
                w = get_drop_width(diff_list[diff_idx], player.height_ft)
                penny_warnings.append(PennyWarning(random.randint(0, WIDTH - w), w, delay_ms=1500))
                new_interval = max(3000, 6000 - int(player.height_ft * 1.0))
                pygame.time.set_timer(penny_timer, new_interval)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: player.rect.x -= 8
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: player.rect.x += 8
        if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]: player.jump()

        player.apply_gravity(); player.update_invincibility()
        if player.on_ground and player.current_platform:
            if player.current_platform.move_type == 1: player.rect.x += player.current_platform.direction * player.current_platform.speed
            if player.current_platform.move_type == 2: player.rect.bottom = player.current_platform.rect.top
        player.rect.left = max(0, player.rect.left); player.rect.right = min(WIDTH, player.rect.right)

        if player.rect.y <= 250 and player.vel_y < 0:
            scroll_vel = abs(player.vel_y)
            player.rect.y += scroll_vel; player.pixels_climbed += scroll_vel
            player.update_height_and_money()
            if player.height_ft > high_score: high_score = player.height_ft

        # Shield Spawning
        if player.height_ft > 0 and player.height_ft % 300 == 0 and player.height_ft > last_shield_spawn:
            shields.append(ShieldItem(-50)); last_shield_spawn = player.height_ft

        # MONEY BAG SPAWNING (Every 500ft)
        if player.height_ft > 0 and player.height_ft % 500 == 0:
            if not any(mb.rect.y < 0 for mb in money_bags): 
                money_bags.append(MoneyBag(-50))

        env.draw(screen, scroll_vel)

        # Draw Penny Warnings
        for warn in penny_warnings[:]:
            warn.draw(screen)
            if warn.ready_to_drop():
                left, right = warn.x + 10, warn.x + warn.w - 10
                span = max(1, right - left)
                for i in range(5):
                    px = max(left, min(right, left + int((i + 0.5) * span / 5) + random.randint(-6, 6)))
                    pennies.append(Penny(px, warn.y - random.randint(40, 140), random.uniform(8.0, 12.0)))
                play(SND_PENNIES_LAND); penny_warnings.remove(warn)

        # Update Pennies
        for pny in pennies[:]:
            pny.update(); pny.draw(screen)
            if pny.rect.colliderect(player.rect):
                if player.invincible: pennies.remove(pny)
                elif player.has_shield:
                    player.has_shield, player.invincible, player.invincible_timer = False, True, pygame.time.get_ticks()
                    pennies.remove(pny)
                else: state = 2; play(SND_DEATH); save_high_score(high_score); break
            if pny.y - pny.r > HEIGHT: pennies.remove(pny)

        # Update Shields
        for s in shields[:]:
            s.update(scroll_vel); s.draw(screen)
            if player.rect.colliderect(s.rect) and not s.collected:
                player.has_shield, s.collected = True, True
            if s.rect.top > HEIGHT: shields.remove(s)

        # Update Money Bags
        for mb in money_bags[:]:
            mb.update(scroll_vel); mb.draw(screen)
            if player.rect.colliderect(mb.rect) and not mb.collected:
                mb.collected = True
                player.run_cents += mb.value
                play(SND_MONEY)
                money_bags.remove(mb)
            elif mb.rect.top > HEIGHT: money_bags.remove(mb)

        # Platforms
        player.on_ground = False; landed_this_frame = False
        for plat in platforms:
            plat.update(scroll_vel); plat.draw(screen, env.bg_index)
            if player.vel_y >= 0 and player.rect.colliderect(plat.rect) and player.rect.bottom <= plat.rect.top + 20:
                player.rect.bottom, player.vel_y, player.on_ground, player.current_platform = plat.rect.top, 0, True, plat
                if id(plat) != last_landed_platform_id: landed_this_frame, last_landed_platform_id = True, id(plat)
            if plat.rect.top > HEIGHT:
                hy = min(p.rect.y for p in platforms)
                hx = [p.rect.x for p in platforms if p.rect.y == hy][0]
                plat.__init__(0, hy - (130 if diff_list[diff_idx] == "Easy" else 145 if diff_list[diff_idx] == "Medium" else 155), player.height_ft, diff_list[diff_idx], prev_x=hx)
        if landed_this_frame: play(SND_LAND)

        # Helicopters
        for h in helis[:]:
            h.update(scroll_vel); h.draw(screen)
            if player.rect.colliderect(h.rect):
                if not player.invincible:
                    if player.has_shield: player.has_shield, player.invincible, player.invincible_timer = False, True, pygame.time.get_ticks()
                    else: state = 2; play(SND_DEATH); save_high_score(high_score)
            elif h.rect.top > HEIGHT: helis.remove(h)

        player.draw(screen)
        draw_text(f"Height: {player.height_ft}ft", font, WHITE, 90, 30, True)
        draw_text(f"Earned: {fmt_money(player.run_cents)}", small_font, GOLD, 95, 60, True)
        draw_text(f"Bank: {fmt_money(bank_cents)}", small_font, WHITE, WIDTH - 95, 30, True)
        if player.has_shield: draw_text("SHIELD", small_font, CYAN, WIDTH - 95, 55, True)
        if player.rect.top > HEIGHT: state = 2; play(SND_DEATH); save_high_score(high_score)

    # --- STATE 2: GAME OVER ---
    elif state == 2:
        if not deposited_this_gameover:
            last_run_cents = player.run_cents
            bank_cents += last_run_cents
            save_bank(bank_cents)
            deposited_this_gameover = True
            # CLEANUP
            pygame.time.set_timer(penny_timer, 0)
            pygame.time.set_timer(enemy_timer, 0)
            pennies.clear(); penny_warnings.clear(); helis.clear(); money_bags.clear()

        draw_text("BANKRUPT!", title_font, PLAYER_RED, WIDTH // 2, 150, True)
        draw_text(f"Final Height: {player.height_ft}ft", font, WHITE, WIDTH // 2, 220, True)
        draw_text(f"Earned: {fmt_money(last_run_cents)}", small_font, GOLD, WIDTH // 2, 255, True)
        draw_text(f"Total: {fmt_money(bank_cents)}", small_font, GOLD, WIDTH // 2, 285, True)
        
        retry_btn = pygame.Rect(WIDTH // 2 - 110, 360, 220, 55)
        draw_styled_button(screen, "MAIN MENU", retry_btn)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN and retry_btn.collidepoint(event.pos):
                play(SND_MENU); state = 0

    # --- STATE 4: THE TAILOR ---
    elif state == 4:
        env.draw(screen, 0)
        draw_text("THE TAILOR", title_font, GOLD, WIDTH // 2, 50, True)
        draw_text(f"BANK: {fmt_money(bank_cents)}", small_font, WHITE, WIDTH // 2, 85, True)

        col_width, start_y, item_h, gap = 160, 130, 45, 8
        
        # Draw Suit Column
        draw_text("SUITS", small_font, GOLD, 100, 115)
        suit_rects = []
        for i, (name, color, price) in enumerate(SUITS):
            rect = pygame.Rect(30, start_y + (i * (item_h + gap)), col_width, item_h)
            suit_rects.append((rect, i))
            bg_color = (60, 60, 80) if i == eq_suit_idx else BTN_BG
            pygame.draw.rect(screen, bg_color, rect, border_radius=8)
            pygame.draw.rect(screen, GOLD if i == eq_suit_idx else WHITE, rect, width=2, border_radius=8)
            pygame.draw.circle(screen, color, (rect.x + 20, rect.centery), 10)
            status_txt = "OWNED" if name in owned_suits else f"${price//100}"
            draw_text(name, small_font, WHITE, rect.x + 85, rect.y + 12)
            draw_text(status_txt, pygame.font.SysFont("Arial", 11, bold=True), GOLD if "$" in status_txt else (150,150,150), rect.x + 85, rect.y + 30)

        # Draw Tie Column
        draw_text("TIES", small_font, GOLD, 300, 115)
        tie_rects = []
        for i, (name, color, price) in enumerate(TIES):
            rect = pygame.Rect(210, start_y + (i * (item_h + gap)), col_width, item_h)
            tie_rects.append((rect, i))
            bg_color = (60, 60, 80) if i == eq_tie_idx else BTN_BG
            pygame.draw.rect(screen, bg_color, rect, border_radius=8)
            pygame.draw.rect(screen, GOLD if i == eq_tie_idx else WHITE, rect, width=2, border_radius=8)
            pygame.draw.circle(screen, color, (rect.x + 20, rect.centery), 8)
            status_txt = "OWNED" if name in owned_ties else f"${price//100}"
            draw_text(name, small_font, WHITE, rect.x + 85, rect.y + 12)
            draw_text(status_txt, pygame.font.SysFont("Arial", 11, bold=True), GOLD if "$" in status_txt else (150,150,150), rect.x + 85, rect.y + 30)

        # Preview & Back
        preview_player = Player(); preview_player.rect.center = (WIDTH // 2, 475); preview_player.draw(screen)
        back_btn = pygame.Rect(WIDTH // 2 - 70, 540, 140, 40); draw_styled_button(screen, "BACK", back_btn)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                for r, index in suit_rects:
                    if r.collidepoint(event.pos):
                        target = SUITS[index]
                        if target[0] in owned_suits: eq_suit_idx = index
                        elif bank_cents >= target[2]: bank_cents -= target[2]; owned_suits.append(target[0]); eq_suit_idx = index; save_bank(bank_cents)
                        save_wardrobe(); play(SND_MENU)
                for r, index in tie_rects:
                    if r.collidepoint(event.pos):
                        target = TIES[index]
                        if target[0] in owned_ties: eq_tie_idx = index
                        elif bank_cents >= target[2]: bank_cents -= target[2]; owned_ties.append(target[0]); eq_tie_idx = index; save_bank(bank_cents)
                        save_wardrobe(); play(SND_MENU)
                if back_btn.collidepoint(event.pos): state = 0; play(SND_MENU)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
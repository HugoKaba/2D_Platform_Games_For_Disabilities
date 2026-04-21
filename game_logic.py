import json
import random
import time
import math
import sys
import pygame
from constants import (
    WIDTH, HEIGHT, FPS, GRAVITY, 
    GESTURE_PROFILES
)
from utils import make_gradient, generate_levels, create_platform_textures
from controllers import GestureController, VoiceController
from entities import Enemy, Fireball
from pathlib import Path

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Mini Mario AR + World Map")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 30, bold=True)
        self.text_font = pygame.font.SysFont("arial", 22)

        self.levels = generate_levels(10)
        self.level_index = 0
        self.unlocked_level = 0
        self.menu_selection = 0
        self.state = "menu"
        self.gesture_profile_index = 0

        self.player = pygame.Rect(0, 0, 34, 46)
        self.facing = 1
        self.vx = 0.0
        self.vy = 0.0
        self.base_speed = 4.2
        self.jump_speed = -14.2
        self.on_ground = False
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.is_big = False
        self.has_fire = False
        self.coins = 0
        self.coins_for_life = 0
        self.lives = 3
        self.hp_max = 3
        self.hp = self.hp_max
        self.attack_timer = 0
        self.last_fire_at = 0.0
        self.level_timer = 300.0

        self.camera_x = 0
        self.camera_y = 0
        self.assets = {}
        self.load_assets()
        self.enemies = []
        self.power_blocks = []
        self.coins_rects = []
        self.fireballs = []
        self.checkpoint = None
        self.checkpoint_reached = False
        self.checkpoint_anim_pct = 0.0
        self.spawn_point = (80, 500)

        self.gesture = GestureController()
        self.gesture_enabled = self.gesture.start()
        self.gesture.set_profile(GESTURE_PROFILES[self.gesture_profile_index])
        self.voice = VoiceController()
        self.voice_enabled = self.voice.start()

        self.clouds = [(random.randint(0, 6000), random.randint(60, 220), random.randint(60, 110)) for _ in range(28)]
        self.last_voice = ""
        self.voice_feedback_timer = 0.0
        self.running = True
        
        self.map_nodes = [
            (200, 480), (350, 420), (500, 480), (650, 420), (850, 480),
            (850, 280), (650, 220), (500, 280), (350, 220), (200, 280)
        ]
        
        self.settings = {
            "Controle": ["Mixte", "Clavier", "AR"],
            "Profil AR": [p["name"] for p in GESTURE_PROFILES],
            "Micro": ["Activé", "Désactivé"]
        }
        self.settings_indices = [0, 0, 0]
        self.settings_selection = 0
        
        self.load_progress()
        self.load_level(0)

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS) / relative_path
        return Path(__file__).parent / relative_path

    def load_assets(self):
        asset_path = self.resource_path("assets")
        self.background_sky = pygame.Surface((WIDTH, HEIGHT))
        make_gradient(self.background_sky, (100, 160, 255), (200, 230, 255))
        try:
            def load_sprite(name, scale=None):
                path = asset_path / name
                if not path.exists():
                    return None
                img = pygame.image.load(str(path)).convert_alpha()
                w, h = img.get_size()
                for x in range(w):
                    for y in range(h):
                        color = img.get_at((x, y))
                        if color.g > 100 and color.g > color.r + 20 and color.g > color.b + 20:
                            img.set_at((x, y), (0, 0, 0, 0))
                if scale:
                    img = pygame.transform.scale(img, scale)
                return img

            self.assets["player"] = load_sprite("player.png")
            self.assets["enemy"] = load_sprite("enemy.png")
            self.assets["coin"] = load_sprite("coin.png")
            self.assets["block"] = load_sprite("block.png")
            self.assets["fire"] = load_sprite("coin.png", (24, 24))
            
            menu_bg_path = asset_path / "mario_menu_bg.png"
            if menu_bg_path.exists():
                self.assets["menu_bg"] = pygame.image.load(str(menu_bg_path)).convert()
                self.assets["menu_bg"] = pygame.transform.scale(self.assets["menu_bg"], (WIDTH, HEIGHT))
            
            bg_plains_path = asset_path / "bg_sky.png"
            if bg_plains_path.exists():
                self.assets["bg_plains"] = pygame.image.load(str(bg_plains_path)).convert()
                self.assets["bg_plains"] = pygame.transform.scale(self.assets["bg_plains"], (WIDTH, HEIGHT))
            
            bg_sky_path = asset_path / "bg_mountains.png"
            if bg_sky_path.exists():
                self.assets["bg_sky_alt"] = pygame.image.load(str(bg_sky_path)).convert()
                self.assets["bg_sky_alt"] = pygame.transform.scale(self.assets["bg_sky_alt"], (WIDTH, HEIGHT))
            
            self.assets["bg_cave"] = pygame.Surface((WIDTH, HEIGHT))
            make_gradient(self.assets["bg_cave"], (15, 10, 30), (35, 30, 55))
            for _ in range(40):
                rx, ry = random.randint(0, WIDTH), random.randint(0, HEIGHT)
                rs = random.randint(2, 5)
                pygame.draw.circle(self.assets["bg_cave"], (55, 50, 75), (rx, ry), rs)
                
            self.assets["brick"], self.assets["grass_top"] = create_platform_textures()
        except Exception as e:
            print(f"Erreur assets: {e}")

    def load_progress(self):
        prog_file = self.resource_path("save_progress.json")
        if prog_file.exists():
            try:
                data = json.loads(prog_file.read_text(encoding="utf-8"))
                self.unlocked_level = data.get("unlocked_level", 0)
            except Exception:
                pass

    def save_progress(self):
        prog_file = self.resource_path("save_progress.json")
        try:
            prog_file.write_text(json.dumps({"unlocked_level": self.unlocked_level}), encoding="utf-8")
        except Exception:
            pass

    def load_level(self, idx):
        self.level_index = max(0, min(idx, len(self.levels) - 1))
        level = self.levels[self.level_index]
        self.spawn_point = level["start"]
        self.player.x, self.player.y = self.spawn_point
        self.vx = self.vy = 0
        self.camera_x = 0
        self.camera_y = max(0, level.get('world_h', 640) - HEIGHT)
        self.checkpoint = level["checkpoint"]
        self.checkpoint_reached = False
        self.checkpoint_anim_pct = 0.0
        self.enemies = [Enemy(e["x"], e["y"], e["range"], e["speed"], self.assets.get("enemy"), e.get("type", "ground")) for e in level["enemies"]]
        self.power_blocks = [{"rect": r.copy(), "used": False} for r in level["power_blocks"]]
        self.coins_rects = [r.copy() for r in level["coins"]]
        self.fireballs = []
        self.attack_timer = 0
        self.level_timer = 300.0

    def reset_current_level(self):
        self.player.x, self.player.y = self.spawn_point
        self.vx = self.vy = 0
        self.fireballs = []

    def move_next_level(self):
        if self.level_index < len(self.levels) - 1:
            self.unlocked_level = max(self.unlocked_level, self.level_index + 1)
            self.save_progress()
            self.load_level(self.level_index + 1)
            self.state = "running"
        else:
            self.state = "victory"

    def handle_voice_command(self, text):
        self.last_voice = text.upper()
        self.voice_feedback_timer = 2.5
        text = text.lower()
        
        if "paramètre" in text or "settings" in text:
            self.state = "settings"
            return
        if "menu" in text:
            self.state = "menu"
            return
        if "jouer" in text:
            if self.state == "menu":
                self.load_level(self.menu_selection)
                self.state = "running"
            return
        if "pause" in text:
            self.state = "paused"
            return
        if "rejoindre" in text or "reprendre" in text:
            self.state = "running"
            return
        if "quitter" in text:
            self.running = False
            return
        if "rejouer" in text or "restart" in text:
            self.reset_current_level()
            self.state = "running"
            return

        if "mode" in text:
            if "mixte" in text:
                self.settings_indices[0] = 0
            elif "clavier" in text:
                self.settings_indices[0] = 1
            elif "ar" in text or "caméra" in text or "camera" in text:
                self.settings_indices[0] = 2

        if "profil" in text:
            old_idx = self.settings_indices[1]
            if "facile" in text:
                self.settings_indices[1] = 0
            elif "normal" in text:
                self.settings_indices[1] = 1
            elif "dur" in text or "difficile" in text or "hard" in text:
                self.settings_indices[1] = 2
            elif "spécial" in text or "special" in text or "directionnel" in text:
                self.settings_indices[1] = 3
            
            if self.settings_indices[1] != old_idx:
                self.gesture.set_profile(GESTURE_PROFILES[self.settings_indices[1]])

        if "niveau" in text:
            for i in range(1, 11):
                if str(i) in text:
                    target_idx = i - 1
                    if target_idx <= self.unlocked_level:
                        self.menu_selection = target_idx
                        if self.state == "menu":
                            self.load_level(target_idx)
                            self.state = "running"
                    break

    def process_voice(self):
        if self.voice_enabled:
            for cmd in self.voice.pop_commands():
                self.handle_voice_command(cmd)

    def spawn_fireball(self):
        if not self.has_fire:
            return
        now = time.time()
        if now - self.last_fire_at < 0.22:
            return
        fb = Fireball(self.player.centerx + 18 * self.facing, self.player.centery - 6, self.facing, self.assets.get("coin"))
        self.fireballs.append(fb)
        self.last_fire_at = now

    def handle_controls(self):
        keys = pygame.key.get_pressed()
        mode_idx = self.settings_indices[0]
        
        left = right = jump = attack = False
        
        if mode_idx in (0, 1):
            left = keys[pygame.K_LEFT] or keys[pygame.K_q]
            right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
            jump = keys[pygame.K_z] or keys[pygame.K_UP] or keys[pygame.K_SPACE]
            attack = keys[pygame.K_s]

        if mode_idx in (0, 2) and self.gesture_enabled and self.gesture.active:
            left = left or self.gesture.left
            right = right or self.gesture.right
            if self.gesture.consume_jump():
                jump = True
            if self.gesture.consume_attack():
                attack = True

        self.vx = 0
        if left:
            self.vx -= self.base_speed
        if right:
            self.vx += self.base_speed
        if self.vx < 0:
            self.facing = -1
        elif self.vx > 0:
            self.facing = 1

        if jump:
            self.jump_buffer_timer = 0.16
        if self.jump_buffer_timer > 0 and (self.on_ground or self.coyote_timer > 0):
            self.vy = self.jump_speed
            self.on_ground = False
            self.coyote_timer = self.jump_buffer_timer = 0

        if attack:
            self.attack_timer = 10
            self.spawn_fireball()

    def update_game(self):
        dt = 1.0 / FPS
        self.handle_controls()
        self.vy += GRAVITY
        self.player.x += int(self.vx)
        self.player.y += int(self.vy)
        self.player.x = max(0, self.player.x)
        
        self.on_ground = False
        level = self.levels[self.level_index]
        for p in level["platforms"]:
            if self.player.colliderect(p) and self.vy >= 0 and self.player.bottom <= p.top + 26:
                self.player.bottom = p.top
                self.vy = 0
                self.on_ground = True
                self.coyote_timer = 0.12

        if self.player.top > level.get("world_h", 640) + 150:
            self.reset_current_level()

        self.enemies = [e for e in self.enemies if e.alive]
        for e in self.enemies:
            e.update()
        
        active_f = []
        for f in self.fireballs:
            f.update()
            hit = False
            for p in level["platforms"]:
                if f.rect.colliderect(p) and f.vy > 0:
                    f.rect.bottom = p.top
                    f.vy = -5.3
            for e in self.enemies:
                if e.alive and f.rect.colliderect(e.rect):
                    e.alive = False
                    hit = True
                    break
            if not hit and 0 <= f.rect.x <= level["world_w"]:
                active_f.append(f)
        self.fireballs = active_f

        if self.attack_timer > 0:
            atk_r = pygame.Rect(self.player.centerx + (24*self.facing) - 23, self.player.centery - 17, 46, 34)
            for e in self.enemies:
                if e.alive and atk_r.colliderect(e.rect):
                    e.alive = False
            self.attack_timer -= 1

        prev_bot = self.player.bottom - self.vy
        for e in self.enemies:
            if e.alive and self.player.colliderect(e.rect):
                if prev_bot <= e.rect.top + 10 and self.vy > 0:
                    e.alive = False
                    self.vy = -9.0
                else:
                    self.hp -= 1
                    self.vy = -5.0
                    if self.hp <= 0:
                        self.lives -= 1
                        self.hp = self.hp_max
                        if self.lives <= 0:
                            self.lives = 3
                            self.state = "menu"
                        else:
                            self.reset_current_level()

        for b in self.power_blocks:
            if not b["used"] and self.player.colliderect(b["rect"]):
                if self.vy < 0 and self.player.top >= b["rect"].bottom - 28:
                    b["used"] = self.is_big = self.has_fire = True

        kept_c = []
        for c in self.coins_rects:
            if self.player.colliderect(c):
                self.coins += 1
                if self.coins >= 10:
                    self.coins -= 10
                    self.lives += 1
            else:
                kept_c.append(c)
        self.coins_rects = kept_c

        if not self.checkpoint_reached and self.checkpoint and self.player.centerx >= self.checkpoint.centerx:
            self.checkpoint_reached = True
            self.spawn_point = (self.checkpoint.x, self.checkpoint.y)
        if self.checkpoint_reached:
            self.checkpoint_anim_pct = min(1.0, self.checkpoint_anim_pct + 0.04)

        if self.player.colliderect(level["goal"]):
            self.move_next_level()

        target_x = self.player.centerx - WIDTH * 0.4
        self.camera_x = max(0, min(int(target_x), level["world_w"] - WIDTH))
        target_y = self.player.centery - HEIGHT * 0.5
        self.camera_y = max(0, min(int(target_y), level["world_h"] - HEIGHT))
        
        self.coyote_timer = max(0.0, self.coyote_timer - dt)
        self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        
        self.level_timer -= dt
        if self.level_timer <= 0:
            self.lives -= 1
            if self.lives <= 0:
                self.lives = 3
                self.state = "menu"
            else:
                self.reset_current_level()
                self.level_timer = 300.0
        
        if self.voice_feedback_timer > 0:
            self.voice_feedback_timer -= dt

    def draw_world(self):
        level = self.levels[self.level_index]
        theme = level.get("theme", "plains")
        bg = self.assets.get(f"bg_{theme}")
        if theme == "sky":
            bg = self.assets.get("bg_sky_alt")
        if bg:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill((100, 160, 255))

        for p in level["platforms"]:
            r = p.move(-self.camera_x, -self.camera_y)
            if theme == "plains":
                mc, tc, bc = (139, 69, 19), (34, 139, 34), (100, 50, 10)
            elif theme == "cave":
                mc, tc, bc = (40, 40, 80), (100, 60, 160), (20, 20, 40)
            else:
                mc, tc, bc = (200, 200, 255), (255, 230, 100), (150, 150, 255)
            pygame.draw.rect(self.screen, mc, r, border_radius=4)
            pygame.draw.rect(self.screen, tc, (r.x, r.y, r.w, 12), border_radius=4)
            pygame.draw.rect(self.screen, bc, r, width=2, border_radius=4)
            if self.assets.get("brick"):
                self.assets["brick"].set_alpha(140)
                for tx in range(0, r.w, 32):
                    self.screen.blit(self.assets["brick"], (r.x + tx, r.y), (0, 0, min(32, r.w - tx), 32))

        if self.checkpoint:
            cp = self.checkpoint.move(-self.camera_x, -self.camera_y)
            pygame.draw.rect(self.screen, (160, 160, 160), (cp.x + 8, cp.y, 4, cp.h))
            pygame.draw.circle(self.screen, (220, 220, 220), (cp.x + 10, cp.y), 6)
            fh = 24
            fy = cp.bottom - fh - (self.checkpoint_anim_pct * (cp.h - fh - 10))
            pts = [(cp.x + 12, fy), (cp.x + 12, fy + fh), (cp.x + 40, fy + fh // 2)]
            pygame.draw.polygon(self.screen, (200, 40, 40), pts)

        for pb in self.power_blocks:
            r = pb["rect"].move(-self.camera_x, -self.camera_y)
            if not pb["used"] and self.assets.get("block"):
                self.screen.blit(pygame.transform.scale(self.assets["block"], (r.w, r.h)), r)
            else:
                pygame.draw.rect(self.screen, (100, 100, 100), r, border_radius=5)

        for c in self.coins_rects:
            r = c.move(-self.camera_x, -self.camera_y)
            if self.assets.get("coin"):
                self.screen.blit(pygame.transform.scale(self.assets["coin"], (r.w, r.h)), r)

        for e in self.enemies:
            e.draw(self.screen, self.camera_x, self.camera_y)
        for f in self.fireballs:
            f.draw(self.screen, self.camera_x, self.camera_y)
        self.draw_portal(level["goal"])

        ph, pw = (64, 48) if self.is_big else (48, 36)
        p_rect = pygame.Rect(self.player.x - self.camera_x, self.player.y - (ph - self.player.h) - self.camera_y, pw, ph)
        if self.assets.get("player"):
            img = pygame.transform.scale(self.assets["player"], (pw, ph))
            if self.facing < 0:
                img = pygame.transform.flip(img, True, False)
            self.screen.blit(img, p_rect)
        if self.attack_timer > 0:
            atk_x = self.player.centerx + (24 * self.facing) - 23 - self.camera_x
            pygame.draw.rect(self.screen, (255, 255, 255), (atk_x, self.player.centery - 17 - self.camera_y, 46, 34), 2, border_radius=6)

    def draw_portal(self, goal_rect):
        r = goal_rect.move(-self.camera_x, -self.camera_y)
        t = time.time() * 5
        for i in range(4, 0, -1):
            radius = (r.w // 2) * (i / 4.0) + math.sin(t + i * 0.8) * 5
            col = (max(50, int(150 + 100 * math.sin(t))), max(100, int(200 + 55 * math.cos(t))), 255)
            s = pygame.Surface((radius * 2.2, radius * 2.2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, 100 + i * 30), (radius * 1.1, radius * 1.1), radius)
            self.screen.blit(s, (r.centerx - radius * 1.1, r.centery - radius * 1.1))
        pygame.draw.ellipse(self.screen, (255, 255, 255), r, 3)

    def draw_hud(self):
        pygame.draw.rect(self.screen, (0, 0, 0, 80), (0, 0, WIDTH, 80))

        if self.assets.get("player"):
            head = pygame.transform.scale(self.assets["player"], (32, 44))
            self.screen.blit(head, (25, 12))
            txt_v = self.font.render(f" x {self.lives}", True, (255, 255, 255))
            self.screen.blit(txt_v, (65, 18))

        if self.assets.get("coin"):
            coin_img = pygame.transform.scale(self.assets["coin"], (28, 28))
            self.screen.blit(coin_img, (WIDTH // 2 - 110, 15))
            txt_c = self.font.render(f"x{self.coins:02d}", True, (255, 220, 0))
            self.screen.blit(txt_c, (WIDTH // 2 - 75, 15))
        
        pygame.draw.circle(self.screen, (255, 255, 255), (WIDTH // 2 + 30, 30), 12, 2)
        pygame.draw.line(self.screen, (255, 255, 255), (WIDTH // 2 + 30, 30), (WIDTH // 2 + 30, 22), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (WIDTH // 2 + 30, 30), (WIDTH // 2 + 38, 30), 2)
        txt_t = self.font.render(f"{int(self.level_timer):03d}", True, (255, 255, 255))
        self.screen.blit(txt_t, (WIDTH // 2 + 50, 15))

        ratio = max(0.0, min(1.0, self.player.centerx / self.levels[self.level_index]["world_w"]))
        pb_w, pb_h = 400, 10
        pb_x, pb_y = WIDTH // 2 - pb_w // 2, 55
        pygame.draw.rect(self.screen, (40, 40, 60), (pb_x, pb_y, pb_w, pb_h), border_radius=5)
        if ratio > 0:
            pygame.draw.rect(self.screen, (255, 215, 0), (pb_x, pb_y, int(pb_w * ratio), pb_h), border_radius=5)
        pygame.draw.rect(self.screen, (255, 255, 255), (pb_x, pb_y, pb_w, pb_h), 2, border_radius=5)

        if self.voice_feedback_timer > 0:
            v_msg = f"DIT: {self.last_voice}"
            v_txt = self.text_font.render(v_msg, True, (255, 255, 0))
            bg_r = pygame.Rect(WIDTH - v_txt.get_width() - 40, 10, v_txt.get_width() + 20, 34)
            pygame.draw.rect(self.screen, (0, 0, 0, 150), bg_r, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 0), bg_r, 1, border_radius=8)
            self.screen.blit(v_txt, (bg_r.x + 10, bg_r.y + 6))

        mode = self.settings["Controle"][self.settings_indices[0]].upper()
        mode_txt = self.text_font.render(f"MODE: {mode}", True, (180, 255, 180))
        self.screen.blit(mode_txt, (WIDTH - mode_txt.get_width() - 20, 50))

    def draw_camera_monitor(self):
        mw, mh = 160, 120
        mx, my = WIDTH - mw - 20, HEIGHT - mh - 20
        
        s = pygame.Surface((mw, mh), pygame.SRCALPHA)
        s.fill((0, 0, 0, 140))
        self.screen.blit(s, (mx, my))
        pygame.draw.rect(self.screen, (255, 255, 255), (mx, my, mw, mh), 2, border_radius=4)
        
        prof = self.gesture.profile
        if prof.get("is_spatial"):
            pygame.draw.line(self.screen, (255, 255, 255, 60), (mx, my + mh * prof["jump_y"]), (mx + mw, my + mh * prof["jump_y"]), 1)
            pygame.draw.line(self.screen, (255, 255, 255, 60), (mx, my + mh * prof["attack_y"]), (mx + mw, my + mh * prof["attack_y"]), 1)
            
            z_font = pygame.font.SysFont("Arial", 12)
            self.screen.blit(z_font.render("SAUT", True, (255, 255, 255, 100)), (mx + mw//2 - 15, my + 5))
            self.screen.blit(z_font.render("ATK", True, (255, 255, 255, 100)), (mx + mw//2 - 10, my + mh - 18))
        
        pygame.draw.line(self.screen, (255, 255, 255, 60), (mx + mw * prof["move_left"], my), (mx + mw * prof["move_left"], my + mh), 1)
        pygame.draw.line(self.screen, (255, 255, 255, 60), (mx + mw * prof["move_right"], my), (mx + mw * prof["move_right"], my + mh), 1)

        sx, sy = self.gesture.stump_x, self.gesture.stump_y
        stump_pos = (mx + int(sx * mw), my + int(sy * mh))
        
        glow_size = int(6 + 3 * math.sin(time.time() * 10))
        pygame.draw.circle(self.screen, (255, 215, 0, 100), stump_pos, glow_size)
        pygame.draw.circle(self.screen, (255, 255, 255), stump_pos, 5)

    def draw_pause_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font.render("PAUSE", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 80))
        
        instr = [
            "Dites 'REPRENDRE' ou 'REJOINDRE' pour continuer",
            "Dites 'S' ou 'PARAMÈTRES' pour les réglages",
            "Dites 'MENU' pour quitter le niveau"
        ]
        for i, line in enumerate(instr):
            t = self.text_font.render(line, True, (200, 200, 200))
            self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 + 20 + i * 35))

    def draw_menu(self):
        if self.assets.get("menu_bg"):
            self.screen.blit(self.assets["menu_bg"], (0, 0))
        else:
            self.screen.fill((10, 15, 30))
            make_gradient(self.screen, (10, 15, 30), (30, 40, 70))
        
        title = self.font.render("LE MONDE DE MARIO AR", True, (255, 230, 0))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40 + int(6 * math.sin(time.time() * 3))))

        for i in range(len(self.map_nodes) - 1):
            col = (255, 255, 255) if i + 1 <= self.unlocked_level else (80, 80, 80)
            pygame.draw.line(self.screen, col, self.map_nodes[i], self.map_nodes[i+1], 4)

        for i, pos in enumerate(self.map_nodes):
            unlocked = i <= self.unlocked_level
            selected = i == self.menu_selection
            radius = 22 if selected else 16
            col = (255, 215, 0) if unlocked else (60, 60, 60)
            if selected:
                pygame.draw.circle(self.screen, (255, 255, 255), pos, radius + 4)
            pygame.draw.circle(self.screen, col, pos, radius)
            num = self.text_font.render(str(i+1), True, (0, 0, 0) if unlocked else (150, 150, 150))
            self.screen.blit(num, (pos[0] - num.get_width() // 2, pos[1] - num.get_height() // 2))

        cur_pos = self.map_nodes[self.menu_selection]
        if self.assets.get("player"):
            img = pygame.transform.scale(self.assets["player"], (32, 44))
            self.screen.blit(img, (cur_pos[0] - 16, cur_pos[1] - 55 + int(4 * math.sin(time.time()*10))))

        instr = "FLÈCHES: NAVIGUER | ENTRÉE: JOUER | S: PARAMÈTRES"
        txt_i = self.text_font.render(instr, True, (200, 200, 200))
        self.screen.blit(txt_i, (WIDTH // 2 - txt_i.get_width() // 2, HEIGHT - 50))

    def draw_settings(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.screen.blit(s, (0, 0))
        card = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 180, 500, 360)
        pygame.draw.rect(self.screen, (30, 40, 60), card, border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), card, width=3, border_radius=15)
        title = self.font.render("PARAMÈTRES", True, (255, 215, 0))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, card.y + 20))
        for i, key in enumerate(self.settings.keys()):
            sel = i == self.settings_selection
            y = card.y + 100 + i * 60
            txt = self.text_font.render(key, True, (255, 255, 255) if sel else (180, 180, 180))
            self.screen.blit(txt, (card.x + 40, y))
            val = self.settings[key][self.settings_indices[i]]
            val_txt = self.text_font.render(f"< {val} >", True, (255, 230, 100) if sel else (140, 140, 140))
            self.screen.blit(val_txt, (card.x + card.w - val_txt.get_width() - 40, y))

    def handle_keydown(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
            return
        if key == pygame.K_s:
            if self.state in ("menu", "paused"):
                self.state = "settings"
            elif self.state == "settings":
                self.state = "menu"
            return
        if self.state == "settings":
            keys = list(self.settings.keys())
            if key in (pygame.K_UP, pygame.K_z):
                self.settings_selection = (self.settings_selection - 1) % len(keys)
            if key in (pygame.K_DOWN, pygame.K_s):
                self.settings_selection = (self.settings_selection + 1) % len(keys)
            if key in (pygame.K_LEFT, pygame.K_q):
                self.settings_indices[self.settings_selection] = (self.settings_indices[self.settings_selection] - 1) % len(self.settings[keys[self.settings_selection]])
                if keys[self.settings_selection] == "Profil AR":
                    self.gesture.set_profile(GESTURE_PROFILES[self.settings_indices[self.settings_selection]])
            if key in (pygame.K_RIGHT, pygame.K_d):
                self.settings_indices[self.settings_selection] = (self.settings_indices[self.settings_selection] + 1) % len(self.settings[keys[self.settings_selection]])
                if keys[self.settings_selection] == "Profil AR":
                    self.gesture.set_profile(GESTURE_PROFILES[self.settings_indices[self.settings_selection]])
            return
        if self.state == "menu":
            if key in (pygame.K_LEFT, pygame.K_q):
                self.menu_selection = max(0, self.menu_selection - 1)
            if key in (pygame.K_RIGHT, pygame.K_d):
                self.menu_selection = min(len(self.levels) - 1, self.menu_selection + 1)
            if key in (pygame.K_UP, pygame.K_z):
                self.menu_selection = max(0, self.menu_selection - 5)
            if key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selection = min(len(self.levels) - 1, self.menu_selection + 5)
            if key == pygame.K_RETURN:
                if self.menu_selection <= self.unlocked_level:
                    self.load_level(self.menu_selection)
                    self.state = "running"
            return
        if key == pygame.K_p:
            self.state = "paused" if self.state == "running" else "running"
        if key == pygame.K_m:
            self.state = "menu"
        if key == pygame.K_r:
            self.reset_current_level()
            self.state = "running"

    def run(self):
        try:
            while self.running:
                self.clock.tick(FPS)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        self.handle_keydown(event.key)
                self.process_voice()
                if self.state == "running":
                    self.update_game()
                self.screen.fill((0, 0, 0))
                if self.state in ("running", "paused"):
                    self.draw_world()
                    self.draw_hud()
                    ctrl_mode = self.settings_indices[0]
                    if ctrl_mode in (0, 2) and self.gesture_enabled and self.gesture.camera_ready:
                        self.draw_camera_monitor()
                    
                    if self.state == "paused":
                        self.draw_pause_menu()
                elif self.state == "victory":
                    self.screen.fill((20, 30, 50))
                elif self.state == "settings":
                    self.draw_settings()
                else:
                    self.draw_menu()
                pygame.display.flip()
        finally:
            self.gesture.stop()
            self.voice.stop()
            pygame.quit()

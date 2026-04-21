import pygame
import math
from constants import COLORS

class Enemy:
    def __init__(self, x, y, move_range, speed, image=None, type="ground"):
        self.rect = pygame.Rect(x, y, 48, 48)
        self.min_x, self.max_x = move_range
        self.speed = speed
        self.dir = 1
        self.alive = True
        self.image = image
        self.type = type
        self.start_y = y
        self.float_offset = 0.0
        if self.image:
            self.image = pygame.transform.scale(self.image, (48, 48))

    def update(self):
        if not self.alive:
            return
        
        if self.type == "flyer":
            self.float_offset += 0.05
            self.rect.y = self.start_y + int(math.sin(self.float_offset) * 50)
            self.rect.x += int(self.speed * self.dir)
        else:
            self.rect.x += int(self.speed * self.dir)
            
        if self.rect.x <= self.min_x or self.rect.x >= self.max_x:
            self.dir *= -1

    def draw(self, screen, camera_x, camera_y=0):
        r = self.rect.move(-camera_x, -camera_y)
        if self.image:
            img = self.image
            if self.dir > 0:
                img = pygame.transform.flip(self.image, True, False)
            screen.blit(img, r)
        else:
            pygame.draw.rect(screen, COLORS["enemy"], r, border_radius=8)

class Fireball:
    def __init__(self, x, y, direction, image=None):
        self.rect = pygame.Rect(x, y, 24, 24)
        self.vx = 8 * direction
        self.vy = -1.5
        self.alive = True
        self.image = image
        if self.image:
            self.image = pygame.transform.scale(self.image, (24, 24))

    def update(self):
        self.vy += 0.35
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        if self.rect.y > 4000 or self.rect.y < -1000:
            self.alive = False

    def draw(self, screen, camera_x, camera_y=0):
        r = self.rect.move(-camera_x, -camera_y)
        if self.image:
            screen.blit(self.image, r)
        else:
            pygame.draw.circle(screen, COLORS["fire"], r.center, 7)

class Particle:
    def __init__(self, x, y, vx, vy, color, life):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, screen, camera_x):
        alpha = int((self.life / self.max_life) * 255)
        s = pygame.Surface((4, 4))
        s.set_alpha(alpha)
        s.fill(self.color)
        screen.blit(s, (self.x - camera_x, self.y))

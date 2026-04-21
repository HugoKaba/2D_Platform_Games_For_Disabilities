import pygame
import random

def make_gradient(surface, color_top, color_bottom):
    h = surface.get_height()
    for y in range(h):
        r = color_top[0] + (color_bottom[0] - color_top[0]) * y // h
        g = color_top[1] + (color_bottom[1] - color_top[1]) * y // h
        b = color_top[2] + (color_bottom[2] - color_top[2]) * y // h
        pygame.draw.line(surface, (r, g, b), (0, y), (surface.get_width(), y))

def generate_levels(count=10):
    levels = []
    for i in range(count):
        if i < 3:
            theme = "plains"
            world_w = 2300 + i * 400
            world_h = 640
            bg_col = (100, 160, 255)
        elif i < 7:
            theme = "cave"
            world_w = 3000 + i * 200
            world_h = 1152
            bg_col = (20, 20, 40)
        else:
            theme = "sky"
            world_w = 4200
            world_h = 1408
            bg_col = (80, 100, 200)

        platforms = []
        start_y = world_h - 100
        platforms.append(pygame.Rect(0, start_y, 400, 120))
        
        curr_x = 450
        curr_y = start_y
        
        while curr_x < world_w - 400:
            rtype = random.choice(["flat", "stairs", "blocks", "pillar"])
            gap = random.randint(110, 135)
            
            target_y = curr_y + random.randint(-110, 160)
            target_y = max(200, min(world_h - 100, target_y))
            
            if rtype == "flat":
                w = random.randint(150, 400)
                platforms.append(pygame.Rect(curr_x, target_y, w, 40))
                if random.random() > 0.7:
                    platforms.append(pygame.Rect(curr_x + 50, target_y - 120, 96, 22))
                curr_x += w + gap
                curr_y = target_y
                
            elif rtype == "stairs":
                steps = random.randint(3, 5)
                direction = -1 if target_y < curr_y else 1
                step_h = abs(target_y - curr_y) // steps
                step_h = max(20, min(32, step_h))
                
                for s in range(steps):
                    sy = curr_y + (s * step_h * direction)
                    platforms.append(pygame.Rect(curr_x + s*32, sy, 32, world_h - sy))
                curr_x += steps * 32 + gap
                curr_y = curr_y + (steps-1) * step_h * direction
                
            elif rtype == "blocks":
                count_b = random.randint(3, 5)
                for b in range(count_b):
                    by = target_y + random.randint(-30, 30)
                    platforms.append(pygame.Rect(curr_x + b*80, by, 48, 22))
                curr_x += count_b * 80 + gap
                curr_y = target_y
                
            elif rtype == "pillar":
                platforms.append(pygame.Rect(curr_x, target_y, 64, world_h - target_y))
                curr_x += 64 + gap
                curr_y = target_y
            
        platforms.append(pygame.Rect(world_w - 400, curr_y, 400, world_h - curr_y + 100))
        
        goal = pygame.Rect(world_w - 100, curr_y - 120, 48, 120)
        mid_idx = len(platforms) // 2
        cp_p = platforms[mid_idx]
        checkpoint = pygame.Rect(cp_p.centerx, cp_p.y - 140, 40, 140)
        
        enemies = []
        for p in platforms[2:-2]:
            if p.w >= 64 and random.random() < 0.35:
                etype = "ground"
                if theme == "sky" or (theme == "cave" and random.random() > 0.6):
                    etype = "flyer"
                enemies.append({
                    "x": p.x + 10, 
                    "y": p.y - 48 if etype == "ground" else p.y - 120,
                    "range": (p.x, p.x + p.w - 48),
                    "speed": 1.1 + (i * 0.12),
                    "type": etype
                })
        levels.append({
            "name": f"Niveau {i+1} ({theme.capitalize()})",
            "world_w": world_w,
            "world_h": world_h,
            "theme": theme,
            "start": (80, start_y - 60),
            "goal": goal,
            "platforms": platforms,
            "enemies": enemies,
            "power_blocks": [pygame.Rect(p.x + 20, p.y - 150, 44, 44) for p in platforms[3:8] if p.w > 80],
            "coins": [pygame.Rect(p.centerx, p.y - 40, 16, 16) for p in platforms if random.random() > 0.5],
            "checkpoint": checkpoint,
            "bg_col": bg_col
        })
    return levels

def create_platform_textures():
    brick = pygame.Surface((32, 32))
    brick.fill((139, 69, 19))
    pygame.draw.line(brick, (200, 100, 40), (0, 0), (31, 0), 2)
    pygame.draw.line(brick, (200, 100, 40), (0, 0), (0, 31), 2)
    pygame.draw.line(brick, (80, 40, 10), (31, 1), (31, 31), 2)
    pygame.draw.line(brick, (80, 40, 10), (1, 31), (31, 31), 2)
    for px, py in [(6, 6), (24, 6), (6, 24), (24, 24)]:
        pygame.draw.circle(brick, (60, 30, 5), (px, py), 2)

    grass = pygame.Surface((32, 32), pygame.SRCALPHA)
    grass.fill((34, 139, 34))
    for _ in range(8):
        x = random.randint(0, 30)
        h = random.randint(5, 12)
        pygame.draw.line(grass, (50, 180, 50), (x, 32), (x + random.randint(-2, 2), 32 - h), 2)
    return brick, grass

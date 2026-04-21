from pathlib import Path

WIDTH, HEIGHT = 1100, 640
FPS = 60
GRAVITY = 0.72

COLORS = {
    "sky_top": (96, 160, 255),
    "sky_bottom": (193, 225, 255),
    "ground": (87, 179, 97),
    "platform": (150, 109, 64),
    "player_small": (227, 83, 63),
    "player_big": (242, 176, 52),
    "enemy": (175, 66, 66),
    "goal": (255, 224, 109),
    "panel": (22, 29, 46),
    "panel_line": (74, 96, 146),
    "text": (242, 246, 255),
    "hint": (205, 218, 244),
    "question": (245, 179, 59),
    "coin": (255, 223, 84),
    "menu_bg": (18, 27, 44),
    "menu_card": (34, 47, 74),
    "menu_accent": (255, 219, 120),
    "fire": (255, 120, 64),
    "checkpoint": (72, 210, 240),
}

VOICE_HINT = "Voix: Menu, Jouer, Pause, Niveau 1..10, Mode Caméra, Profil Spécial, Quitter"
PROGRESS_FILE = Path(__file__).parent / "save_progress.json"

GESTURE_PROFILES = [
    {"name": "Facile", "move_left": 0.42, "move_right": 0.58, "pinch": 0.12, "jump_cd": 0.15, "swipe": -0.15, "attack_cd": 0.55},
    {"name": "Normal", "move_left": 0.40, "move_right": 0.60, "pinch": 0.10, "jump_cd": 0.20, "swipe": -0.12, "attack_cd": 0.45},
    {"name": "Hard", "move_left": 0.38, "move_right": 0.62, "pinch": 0.08, "jump_cd": 0.25, "swipe": -0.10, "attack_cd": 0.35},
    {"name": "Directionnel", "is_spatial": True, "deadzone": 0.16, "jump_y": 0.38, "attack_y": 0.62, "move_left": 0.38, "move_right": 0.62, "jump_cd": 0.35, "attack_cd": 0.5},
]

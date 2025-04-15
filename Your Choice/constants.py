import pygame

# Game screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
TITLE = "Chase/Hide AI Game"

# Colors (Type hinting can be helpful)
WHITE: tuple[int, int, int] = (255, 255, 255)
BLACK: tuple[int, int, int] = (0, 0, 0)
RED: tuple[int, int, int] = (255, 0, 0) # Typically Attacker/Chaser
BLUE: tuple[int, int, int] = (0, 0, 255) # Typically Defender/Hider
DARK_GRAY: tuple[int, int, int] = (50, 50, 50)
LIGHT_GRAY: tuple[int, int, int] = (180, 180, 180) # For menu text
YELLOW: tuple[int, int, int] = (255, 255, 0)
GREEN: tuple[int, int, int] = (0, 255, 0)
PURPLE: tuple[int, int, int] = (150, 50, 255)

# Laser Colors
LASER_RED: tuple[int, int, int] = (255, 0, 0)
LASER_CORE: tuple[int, int, int] = (255, 255, 0)

# Debug/UI Colors
PATH_COLOR: tuple[int, int, int] = (50, 200, 50)
PREDICTION_COLOR: tuple[int, int, int] = (200, 50, 50)
ATTACKER_PATH_COLOR: tuple[int, int, int] = (255, 100, 100)
DEFENDER_PATH_COLOR: tuple[int, int, int] = (100, 100, 255)
HIDE_TARGET_COLOR: tuple[int, int, int] = PURPLE

# Game settings
FPS = 60
GRID_SIZE = 20
CAR_WIDTH = 30
CAR_HEIGHT = 40
OBSTACLE_SIZE = 40
NUM_OBSTACLES = 15
OBSTACLE_MIN_START_DIST = 100 # Min distance obstacles should be from cars at start

# AI settings (General)
PATHFINDING_UPDATE_RATE = 10 # Frames between path recalculations
PREDICTION_STEPS = 60 # How many steps (frames) into the future to predict
PREDICTION_INTERVAL = 5 # Granularity of prediction path points

# AI Attacker Settings (Chasing Logic)
# Attacker uses A* to chase, simple avoidance
LOS_TIMER_DURATION = 1500 # ms - Time LOS must be held to win (Defender mode)
LASER_MAX_LENGTH_FACTOR = 1.0 # Factor of screen diagonal for max laser length

# AI Defender Settings (Hiding/Evading Logic using FSM)
SAFE_DISTANCE = 100 # Base distance for EVADE state fallback
MIN_DISTANCE = 80 # Unused? Maybe remove or repurpose
HIDE_TRIGGER_DISTANCE = 400 # How close attacker needs to be to trigger HIDE state
VERY_CLOSE_DISTANCE = 80 # If attacker gets this close, force basic EVADE
BUFFER_BEHIND_OBSTACLE = CAR_HEIGHT * 1.5 # How far behind obstacle center to target for HIDE
MAX_HIDE_SEARCH_OBSTACLES = 5 # Limit obstacle checks for HIDE spots (performance)
OBSTACLE_SORT_WEIGHT_DIST = 0.6 # Weight for obstacle distance in HIDE scoring
OBSTACLE_SORT_WEIGHT_ANGLE = 0.4 # Weight for angle difference in HIDE scoring

# State indicator colors (can be defined here or in rendering)
STATE_IDLE_COLOR: tuple[int, int, int] = (200, 200, 200)
STATE_EVADE_COLOR: tuple[int, int, int] = (255, 100, 100)
STATE_PATROL_COLOR: tuple[int, int, int] = (100, 255, 100)
STATE_HIDE_COLOR: tuple[int, int, int] = PURPLE
STATE_RETURN_COLOR: tuple[int, int, int] = YELLOW
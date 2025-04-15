# Game screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
TITLE = "Advanced Car Avoidance Game"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
DARK_GRAY = (50, 50, 50)
LASER_RED = (255, 0, 0)
LASER_CORE = (255, 255, 0)
HIDE_TARGET_COLOR = (150, 50, 255) # Color for visualizing hide target

# Game settings
FPS = 60
GRID_SIZE = 20
CAR_WIDTH = 30
CAR_HEIGHT = 40
OBSTACLE_SIZE = 40

# AI settings
PREDICTION_STEPS = 60
SAFE_DISTANCE = 100 # Keep for basic EVADE fallback trigger
MIN_DISTANCE = 80
PATHFINDING_UPDATE_RATE = 10

# Hiding Behavior Settings
HIDE_TRIGGER_DISTANCE = 600 # How close player needs to be to trigger HIDE state
BUFFER_BEHIND_OBSTACLE = CAR_HEIGHT * 1.5 # How far behind obstacle to target
MAX_HIDE_SEARCH_OBSTACLES = 5 # Limit how many obstacles to check for hiding spots (performance)
OBSTACLE_SORT_WEIGHT_DIST = 0.6 # Weight for obstacle distance in sorting
OBSTACLE_SORT_WEIGHT_ANGLE = 0.4 # Weight for angle difference in sorting
VERY_CLOSE_DISTANCE = 60 # If player gets this close, force EVADE even if hidden
import math
import pygame
from constants import GRID_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def normalize_vector(x: float, y: float) -> tuple[float, float]:
    """Normalize a vector to have magnitude 1."""
    mag = distance(0, 0, x, y)
    # Avoid division by zero or very small numbers
    if mag < 0.0001:
        return 0.0, 0.0
    return x / mag, y / mag

def world_to_grid(x: float, y: float) -> tuple[int, int]:
    """Convert world coordinates to grid coordinates."""
    return int(x // GRID_SIZE), int(y // GRID_SIZE)

def grid_to_world(grid_x: int, grid_y: int) -> tuple[float, float]:
    """Convert grid coordinates to center world coordinates of the grid cell."""
    return grid_x * GRID_SIZE + GRID_SIZE / 2.0, grid_y * GRID_SIZE + GRID_SIZE / 2.0

def is_in_screen(x: float, y: float, obj_width: int = 0, obj_height: int = 0) -> bool:
    """Check if a point or an object's top-left corner is within screen boundaries."""
    return 0 <= x <= SCREEN_WIDTH - obj_width and 0 <= y <= SCREEN_HEIGHT - obj_height

def check_line_of_sight(start_pos: tuple[float, float], end_pos: tuple[float, float], obstacles: list) -> bool:
    """
    Checks if the line segment between start_pos and end_pos is blocked by any obstacles.
    Uses simple ray stepping.

    Args:
        start_pos: (x, y) tuple for the start of the line.
        end_pos: (x, y) tuple for the end of the line.
        obstacles: A list of obstacle objects, each having a `rect` attribute.

    Returns:
        bool: True if LOS is blocked by an obstacle, False if clear.
    """
    start_x, start_y = start_pos
    end_x, end_y = end_pos

    dx = end_x - start_x
    dy = end_y - start_y
    line_dist = distance(start_x, start_y, end_x, end_y)

    if line_dist < 1.0: # Points are practically the same
        return False # No obstacle can be between them

    # Normalize direction vector
    norm_dx, norm_dy = normalize_vector(dx, dy)

    # Ray casting check
    step_size = 5.0  # Check every 5 pixels along the ray
    current_dist = step_size # Start checking slightly away from the start point

    while current_dist < line_dist:
        # Calculate current point along the ray
        current_x = start_x + norm_dx * current_dist
        current_y = start_y + norm_dy * current_dist

        # Check if this point falls within any obstacle's rectangle
        for obstacle in obstacles:
            # obstacle.rect should be a pygame.Rect object
            if obstacle.rect.collidepoint(current_x, current_y):
                return True # Blocked by an obstacle

        current_dist += step_size

    return False # No collision found, LOS is clear
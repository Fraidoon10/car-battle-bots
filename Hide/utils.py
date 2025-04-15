import math
import pygame
from constants import GRID_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

def distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def normalize_vector(x, y):
    """Normalize a vector to have magnitude 1."""
    mag = max(0.01, distance(0, 0, x, y))
    return x / mag, y / mag

def world_to_grid(x, y):
    """Convert world coordinates to grid coordinates."""
    return int(x / GRID_SIZE), int(y / GRID_SIZE)

def grid_to_world(grid_x, grid_y):
    """Convert grid coordinates to world coordinates."""
    return grid_x * GRID_SIZE + GRID_SIZE // 2, grid_y * GRID_SIZE + GRID_SIZE // 2

def is_in_screen(x, y, width, height):
    """Check if an object is within screen boundaries."""
    # Corrected check to include boundaries properly
    return (0 <= x <= SCREEN_WIDTH - width and 0 <= y <= SCREEN_HEIGHT - height)

def check_line_of_sight(start_pos, end_pos, obstacles):
    """
    Checks if the line segment between start_pos and end_pos is blocked by any obstacles.
    Returns:
        bool: True if LOS is blocked, False if clear.
    """
    start_x, start_y = start_pos
    end_x, end_y = end_pos

    # Calculate direction vector and distance
    dx = end_x - start_x
    dy = end_y - start_y
    distance_to_end = math.sqrt(dx*dx + dy*dy)

    if distance_to_end < 1.0: # Points are too close, consider LOS clear
        return False

    # Normalize direction vector
    dx /= distance_to_end
    dy /= distance_to_end

    # Ray casting check
    step_size = 5  # Check every 5 pixels along the ray
    current_dist = step_size # Start checking slightly away from the start point

    while current_dist < distance_to_end:
        # Calculate current point along the ray
        current_x = start_x + dx * current_dist
        current_y = start_y + dy * current_dist

        # Check if this point falls within any obstacle's rectangle
        for obstacle in obstacles:
            # Use inflate to give a slight margin to the collision check? Or just collidepoint
            # if obstacle.rect.inflate(2, 2).collidepoint(current_x, current_y): # Example with inflate
            if obstacle.rect.collidepoint(current_x, current_y):
                return True # Blocked by an obstacle

        current_dist += step_size

    return False # No collision found, LOS is clear
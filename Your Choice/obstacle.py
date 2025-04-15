import pygame
import random
from constants import (SCREEN_WIDTH, SCREEN_HEIGHT, OBSTACLE_SIZE, DARK_GRAY,
                     NUM_OBSTACLES, OBSTACLE_MIN_START_DIST)
from utils import distance

class Obstacle:
    """Represents a static obstacle in the game world."""
    def __init__(self, x: int, y: int, size: int = OBSTACLE_SIZE):
        self.x = x
        self.y = y
        self.size = size
        self.color = DARK_GRAY
        # Pygame Rect for collision detection and drawing
        # Use int for Rect coordinates
        self.rect = pygame.Rect(int(self.x), int(self.y), self.size, self.size)
        # Store center position for convenience
        self.center = self.rect.center

    def draw(self, screen: pygame.Surface):
        """Draws the obstacle on the screen."""
        pygame.draw.rect(screen, self.color, self.rect)

def generate_obstacles(cars_to_avoid: list, num_obstacles: int = NUM_OBSTACLES,
                       min_dist_from_cars: float = OBSTACLE_MIN_START_DIST,
                       min_dist_between_obs: float = OBSTACLE_SIZE * 1.5) -> list[Obstacle]:
    """
    Generates a list of obstacles, ensuring they don't spawn too close
    to initial car positions or each other.

    Args:
        cars_to_avoid: A list of car objects (must have x, y attributes) to avoid placing obstacles near.
        num_obstacles: The number of obstacles to generate.
        min_dist_from_cars: Minimum distance an obstacle center can be from any car center at start.
        min_dist_between_obs: Minimum distance between the centers of any two obstacles.

    Returns:
        A list of generated Obstacle objects.
    """
    obstacles = []
    attempts = 0
    max_attempts = num_obstacles * 20 # Prevent infinite loops if space is too crowded

    while len(obstacles) < num_obstacles and attempts < max_attempts:
        attempts += 1
        # Generate random top-left position
        x = random.randint(0, SCREEN_WIDTH - OBSTACLE_SIZE)
        y = random.randint(0, SCREEN_HEIGHT - OBSTACLE_SIZE)
        new_obs_center_x = x + OBSTACLE_SIZE / 2
        new_obs_center_y = y + OBSTACLE_SIZE / 2

        valid_placement = True

        # 1. Check distance from initial car positions
        for car in cars_to_avoid:
            # car should have get_position() or x, y attributes
            try:
                car_x, car_y = car.get_position() # Prefer get_position for center
            except AttributeError:
                car_x, car_y = car.x + car.width/2, car.y + car.height/2 # Fallback

            if distance(car_x, car_y, new_obs_center_x, new_obs_center_y) < min_dist_from_cars:
                valid_placement = False
                break
        if not valid_placement:
            continue # Try new random position

        # 2. Check distance from already placed obstacles
        for existing_obs in obstacles:
            if distance(existing_obs.center[0], existing_obs.center[1], new_obs_center_x, new_obs_center_y) < min_dist_between_obs:
                valid_placement = False
                break
        if not valid_placement:
            continue # Try new random position

        # If all checks pass, add the obstacle
        obstacles.append(Obstacle(x, y))

    if len(obstacles) < num_obstacles:
        print(f"Warning: Could only generate {len(obstacles)} out of {num_obstacles} requested obstacles due to spacing constraints.")

    return obstacles
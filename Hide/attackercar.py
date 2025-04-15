import pygame
import random
import math
from constants import *
from utils import is_in_screen, distance, normalize_vector

class AttackerCar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = CAR_WIDTH
        self.height = CAR_HEIGHT
        self.max_speed = 3
        self.vx = 0
        self.vy = 0
        self.color = RED
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.current_target_waypoint = None # For A* path following

    def move_to_target(self, target_pos, obstacles):
        """Sets velocity towards a target, with basic obstacle avoidance."""
        if not target_pos:
            self.vx = 0
            self.vy = 0
            return

        car_center_x = self.x + self.width / 2
        car_center_y = self.y + self.height / 2
        dx = target_pos[0] - car_center_x
        dy = target_pos[1] - car_center_y
        dist_to_target = max(0.1, distance(0, 0, dx, dy))
        target_dx, target_dy = normalize_vector(dx, dy) # Target direction

        # Basic speed control (optional, could just use max_speed)
        target_speed = self.max_speed # min(self.max_speed, dist_to_target / 5)

        # --- Basic Local Obstacle Avoidance ---
        avoidance_dx = 0
        avoidance_dy = 0
        avoidance_active = False
        avoidance_radius = self.width * 2.0 # How close to obstacle triggers avoidance

        for obstacle in obstacles:
            obstacle_center_x = obstacle.x + obstacle.size / 2
            obstacle_center_y = obstacle.y + obstacle.size / 2
            obstacle_dist = distance(car_center_x, car_center_y,
                                     obstacle_center_x, obstacle_center_y)

            if obstacle_dist < avoidance_radius:
                away_dx = car_center_x - obstacle_center_x
                away_dy = car_center_y - obstacle_center_y
                away_dx, away_dy = normalize_vector(away_dx, away_dy)
                strength = (1.0 - (obstacle_dist / avoidance_radius)) * 1.5 # Avoidance strength factor

                avoidance_dx += away_dx * strength
                avoidance_dy += away_dy * strength
                avoidance_active = True

        # --- Combine Target Direction with Avoidance ---
        if avoidance_active:
            avoid_mag = math.sqrt(avoidance_dx**2 + avoidance_dy**2)
            if avoid_mag > 0.01:
                norm_av_dx = avoidance_dx / avoid_mag
                norm_av_dy = avoidance_dy / avoid_mag
                # Blend target and avoidance vectors (adjust weight as needed)
                avoid_weight = min(0.8, avoid_mag) # Stronger avoidance when closer/more obstacles
                final_dx = target_dx * (1.0 - avoid_weight) + norm_av_dx * avoid_weight
                final_dy = target_dy * (1.0 - avoid_weight) + norm_av_dy * avoid_weight
                final_dx, final_dy = normalize_vector(final_dx, final_dy)
            else:
                final_dx, final_dy = target_dx, target_dy
        else:
            final_dx, final_dy = target_dx, target_dy

        self.vx = final_dx * target_speed
        self.vy = final_dy * target_speed

    def update_physics(self, obstacles):
        """Applies velocity and handles collisions (like original DefenseCar.update)."""
        old_x, old_y = self.x, self.y

        # Update X position
        self.x += self.vx
        self.rect.x = int(self.x)
        collided_x = False
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                self.x = old_x
                self.rect.x = int(old_x)
                self.vx *= -0.5 # Bounce
                collided_x = True
                break

        # Update Y position
        self.y += self.vy
        self.rect.y = int(self.y)
        collided_y = False
        for obstacle in obstacles:
             if self.rect.colliderect(obstacle.rect):
                self.y = old_y
                self.rect.y = int(old_y)
                self.vy *= -0.5 # Bounce
                collided_y = True
                break

        # Keep within screen boundaries
        bounce_factor = -0.5
        if self.x < 0:
            self.x = 0
            self.vx *= bounce_factor
        elif self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
            self.vx *= bounce_factor
        if self.y < 0:
            self.y = 0
            self.vy *= bounce_factor
        elif self.y > SCREEN_HEIGHT - self.height:
            self.y = SCREEN_HEIGHT - self.height
            self.vy *= bounce_factor

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)


    def get_position(self):
        return (self.x + self.width/2, self.y + self.height/2)

# --- Obstacle and generation functions remain the same ---
class Obstacle:
    def __init__(self, x, y, size=OBSTACLE_SIZE):
        self.x = x
        self.y = y
        self.size = size
        self.color = DARK_GRAY
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

def generate_obstacles(num_obstacles, car1, car2, min_dist=100):
    """Generate obstacles that aren't too close to cars."""
    obstacles = []
    # Ensure car1 and car2 are valid objects with x, y attributes
    cars = [c for c in [car1, car2] if c is not None]

    for _ in range(num_obstacles):
        valid = False
        while not valid:
            x = random.randint(0, SCREEN_WIDTH - OBSTACLE_SIZE)
            y = random.randint(0, SCREEN_HEIGHT - OBSTACLE_SIZE)
            valid_placement = True

            # Check distance from cars
            for car in cars:
                 if distance(car.x, car.y, x + OBSTACLE_SIZE/2, y + OBSTACLE_SIZE/2) < min_dist:
                      valid_placement = False
                      break
            if not valid_placement: continue

            # Check overlapping with other obstacles
            for obs in obstacles:
                if distance(obs.x + obs.size/2, obs.y + obs.size/2, x + OBSTACLE_SIZE/2, y + OBSTACLE_SIZE/2) < OBSTACLE_SIZE * 1.5:
                    valid_placement = False
                    break

            if valid_placement:
                valid = True
                obstacles.append(Obstacle(x, y))
    return obstacles
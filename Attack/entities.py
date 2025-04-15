import pygame
import random
from constants import *
from utils import is_in_screen, distance

class PlayerCar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = CAR_WIDTH
        self.height = CAR_HEIGHT
        self.speed = 5
        self.vx = 0  # Velocity x component
        self.vy = 0  # Velocity y component
        self.color = RED
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, keys, obstacles):
        # Save old position for collision resolution
        old_x, old_y = self.x, self.y

        # Reset velocity
        self.vx = 0
        self.vy = 0

        # Update velocity based on keys
        if keys[pygame.K_LEFT]:
            self.vx = -self.speed
        if keys[pygame.K_RIGHT]:
            self.vx = self.speed
        if keys[pygame.K_UP]:
            self.vy = -self.speed
        if keys[pygame.K_DOWN]:
            self.vy = self.speed

        # Move in X direction
        self.x += self.vx
        self.rect.x = self.x

        # Check for collisions in X direction
        collision_detected = False
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                collision_detected = True
                # Revert X position
                self.x = old_x
                self.rect.x = old_x
                break

        # Move in Y direction
        self.y += self.vy
        self.rect.y = self.y

        # Check for collisions in Y direction
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                # Revert Y position
                self.y = old_y
                self.rect.y = old_y
                collision_detected = True
                break

        # Keep within screen boundaries
        if not is_in_screen(self.x, self.y, self.width, self.height):
            self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
            self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))
            self.rect.x = self.x
            self.rect.y = self.y

    def get_position(self):
        return (self.x + self.width/2, self.y + self.height/2)

    def get_velocity(self):
        return (self.vx, self.vy)

    # Removed get_rect()

class Obstacle:
    def __init__(self, x, y, size=OBSTACLE_SIZE):
        self.x = x
        self.y = y
        self.size = size
        self.color = DARK_GRAY
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    # Removed get_rect()

def generate_obstacles(num_obstacles, player_car, def_car=None, min_dist=100):
    """Generate obstacles that aren't too close to cars."""
    obstacles = []

    for _ in range(num_obstacles):
        valid = False
        while not valid:
            x = random.randint(0, SCREEN_WIDTH - OBSTACLE_SIZE)
            y = random.randint(0, SCREEN_HEIGHT - OBSTACLE_SIZE)

            # Check distance from player car
            if distance(player_car.x, player_car.y, x, y) < min_dist:
                continue

            # Check distance from defense car if provided
            if def_car and distance(def_car.x, def_car.y, x, y) < min_dist:
                continue

            # Check overlapping with other obstacles
            overlapping = False
            for obs in obstacles:
                if distance(obs.x, obs.y, x, y) < OBSTACLE_SIZE * 1.5:
                    overlapping = True
                    break

            if not overlapping:
                valid = True
                obstacles.append(Obstacle(x, y))

    return obstacles
import pygame
import math
from constants import *
from utils import distance, normalize_vector, is_in_screen

class HidingCar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = CAR_WIDTH
        self.height = CAR_HEIGHT
        self.speed = 5
        self.vx = 0
        self.vy = 0
        self.color = BLUE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update_player(self, keys, obstacles):
        """Update based on keyboard input and handle collisions."""
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

        # Normalize diagonal movement (optional but good practice)
        if self.vx != 0 and self.vy != 0:
             self.vx /= math.sqrt(2)
             self.vy /= math.sqrt(2)

        # Move in X direction
        self.x += self.vx
        self.rect.x = int(self.x)

        # Check for collisions in X direction
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                self.x = old_x
                self.rect.x = int(old_x)
                self.vx = 0 # Stop x-movement on collision
                break

        # Move in Y direction
        self.y += self.vy
        self.rect.y = int(self.y)

        # Check for collisions in Y direction
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                self.y = old_y
                self.rect.y = int(old_y)
                self.vy = 0 # Stop y-movement on collision
                break

        # Keep within screen boundaries (simple stop)
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def get_position(self):
        """Get the center position of the car."""
        return (self.x + self.width/2, self.y + self.height/2)
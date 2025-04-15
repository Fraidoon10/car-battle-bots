import pygame
import math
from constants import (CAR_WIDTH, CAR_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
                     RED, BLUE, WHITE)
from obstacle import Obstacle # Use the unified Obstacle class
from utils import normalize_vector

class PlayerCar:
    """Represents a car controlled by the player via keyboard input."""

    def __init__(self, x: float, y: float, role: str = "hider"):
        """
        Initializes the player car.

        Args:
            x: Initial x-coordinate (top-left).
            y: Initial y-coordinate (top-left).
            role: "hider" (blue, evading) or "chaser" (red, attacking).
                  Determines color and potentially behavior/speed later.
        """
        self.x = x
        self.y = y
        self.width = CAR_WIDTH
        self.height = CAR_HEIGHT
        self.role = role

        # Assign properties based on role
        if self.role == "hider":
            self.color = BLUE
            self.speed = 5.0 # Hider speed
        elif self.role == "chaser":
            self.color = RED
            self.speed = 5.0 # Chaser speed
        else:
            self.color = (128, 128, 128) # Default gray if role is unknown
            self.speed = 4.0
            print(f"Warning: Unknown player role '{self.role}'. Using default settings.")

        self.vx = 0.0 # Velocity x
        self.vy = 0.0 # Velocity y
        # Use floating point for position, integer for Rect
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, keys: pygame.key.ScancodeWrapper, obstacles: list[Obstacle]):
        """
        Updates the player car's position based on keyboard input and
        handles collisions with obstacles and screen boundaries.

        Args:
            keys: The state of all keyboard keys (from pygame.key.get_pressed()).
            obstacles: A list of Obstacle objects to check collisions against.
        """
        old_x, old_y = self.x, self.y

        # --- Calculate desired velocity based on input ---
        move_x = 0.0
        move_y = 0.0
        if keys[pygame.K_LEFT]:
            move_x -= 1.0
        if keys[pygame.K_RIGHT]:
            move_x += 1.0
        if keys[pygame.K_UP]:
            move_y -= 1.0
        if keys[pygame.K_DOWN]:
            move_y += 1.0

        # --- Normalize diagonal movement ---
        mag = math.hypot(move_x, move_y)
        if mag > 0.001: # Avoid division by zero/normalize zero vector
            norm_move_x = move_x / mag
            norm_move_y = move_y / mag
        else:
            norm_move_x = 0.0
            norm_move_y = 0.0

        # Prevent division by zero if speed is zero (though unlikely)
        current_speed = self.speed if self.speed > 0 else 1.0
        self.vx = norm_move_x * current_speed
        self.vy = norm_move_y * current_speed

        # --- Apply velocity and handle collisions (Axis-by-axis) ---

        # Move X
        self.x += self.vx
        self.rect.x = int(self.x)

        # Check X collisions
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                # Collision occurred, adjust position based on direction of movement
                if self.vx > 0: # Moving right, hit left side of obstacle
                    self.x = obstacle.rect.left - self.width
                elif self.vx < 0: # Moving left, hit right side of obstacle
                    self.x = obstacle.rect.right
                self.vx = 0 # Stop horizontal movement
                self.rect.x = int(self.x) # Update rect position
                break # Only need to resolve collision with one obstacle per axis

        # Move Y
        self.y += self.vy
        self.rect.y = int(self.y)

        # Check Y collisions
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                # Collision occurred, adjust position
                if self.vy > 0: # Moving down, hit top side of obstacle
                    self.y = obstacle.rect.top - self.height
                elif self.vy < 0: # Moving up, hit bottom side of obstacle
                    self.y = obstacle.rect.bottom
                self.vy = 0 # Stop vertical movement
                self.rect.y = int(self.y) # Update rect position
                break

        # --- Screen Boundary Collision ---
        # Use max/min to clamp position, effectively stopping at boundaries
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))

        # Update final rect position after all adjustments
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)


    def get_position(self) -> tuple[float, float]:
        """Returns the center position of the car."""
        return self.x + self.width / 2.0, self.y + self.height / 2.0

    def get_velocity(self) -> tuple[float, float]:
        """Returns the current velocity (vx, vy) of the car."""
        return self.vx, self.vy

    def draw(self, screen: pygame.Surface):
        """Draws the player car on the screen."""
        pygame.draw.rect(screen, self.color, self.rect)

        # Optional: Draw direction indicator based on velocity
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1: # Draw only if moving significantly
            start_x = self.rect.centerx
            start_y = self.rect.centery
            # Normalize display vector using imported function
            norm_vx, norm_vy = normalize_vector(self.vx, self.vy) # Line 142
            scale = 15 # Length of the indicator line
            end_x = start_x + norm_vx * scale
            end_y = start_y + norm_vy * scale
            try:
                pygame.draw.line(screen, WHITE, (start_x, start_y), (int(end_x), int(end_y)), 2)
            except ValueError: # Catch potential errors if coords are extreme/NaN
                 # print(f"Warning: Invalid coordinates for player direction line: {(start_x, start_y)} to {(end_x, end_y)}")
                 pass # Silently ignore drawing error for indicator
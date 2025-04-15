import pygame
import math
import random
from constants import (CAR_WIDTH, CAR_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, RED, YELLOW, WHITE,
                     PATHFINDING_UPDATE_RATE, ATTACKER_PATH_COLOR)
from utils import distance, normalize_vector
from obstacle import Obstacle
from ai.pathfinding import AStar

class AttackerAI:
    """AI-controlled car that chases a target using A* pathfinding."""

    def __init__(self, x: float, y: float, pathfinder: AStar):
        """
        Initializes the Attacker AI car.

        Args:
            x: Initial x-coordinate (top-left).
            y: Initial y-coordinate (top-left).
            pathfinder: An initialized AStar instance for navigation.
        """
        self.x = x
        self.y = y
        self.width = CAR_WIDTH
        self.height = CAR_HEIGHT
        self.max_speed = 3.5 # Attacker speed (adjust as needed relative to player/defender)
        self.vx = 0.0
        self.vy = 0.0
        self.color = RED
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)

        self.pathfinder = pathfinder
        self.path: list[tuple[float, float]] = []
        self.current_waypoint: tuple[float, float] | None = None
        # Stagger initial path updates slightly to avoid all AI calculating at once if multiple exist
        self.path_update_counter = random.randint(0, PATHFINDING_UPDATE_RATE // 2)
        self.target_car = None # The car object this AI is chasing

    def set_target(self, target_car):
        """Sets the car object the AI should chase."""
        self.target_car = target_car
        self.path = [] # Clear old path when target changes
        self.current_waypoint = None
        self.path_update_counter = PATHFINDING_UPDATE_RATE # Force immediate path recalc

    def update(self, obstacles: list[Obstacle]):
        """
        Updates the AI's state: recalculates path if needed, determines movement target,
        calculates velocity with obstacle avoidance, and updates physics.

        Args:
            obstacles: List of Obstacle objects in the environment.
        """
        if not self.target_car:
            self.vx = 0
            self.vy = 0
            # Just stand still if no target
            return

        attacker_pos = self.get_position()
        target_pos = self.target_car.get_position() # Get target's current center position

        # --- Pathfinding Logic ---
        self.path_update_counter += 1
        needs_new_path = not self.path or self.path_update_counter >= PATHFINDING_UPDATE_RATE

        if needs_new_path:
            self.path_update_counter = 0
            # Note: Assuming obstacles are static, pathfinder grid is updated once at start.
            # If obstacles moved, you'd call self.pathfinder.update_obstacles(obstacles) here.
            new_path = self.pathfinder.find_path(attacker_pos, target_pos)
            if new_path:
                self.path = new_path
                self.current_waypoint = self.path[0] if self.path else None
                # print(f"Attacker AI: New path ({len(self.path)} wp). First: {self.current_waypoint}") # Debug
            else:
                self.path = []
                self.current_waypoint = target_pos # Fallback: target directly
                # print("Attacker AI: No A* path found. Targeting directly.") # Debug

        # --- Waypoint Following ---
        if self.path and self.current_waypoint:
            dist_to_waypoint = distance(attacker_pos[0], attacker_pos[1], self.current_waypoint[0], self.current_waypoint[1])
            waypoint_reach_threshold = 25 # How close to get before advancing

            if dist_to_waypoint < waypoint_reach_threshold:
                self.path.pop(0) # Remove reached waypoint
                if self.path:
                    self.current_waypoint = self.path[0]
                    # print(f"Attacker AI: Reached wp. Next: {self.current_waypoint}") # Debug
                else:
                    self.current_waypoint = target_pos # Path complete, target final pos
                    # print("Attacker AI: Path complete. Targeting final pos.") # Debug
                    self.path = [] # Explicitly clear path list when done
        # Ensure we target directly if path becomes empty after pop
        elif not self.path:
             self.current_waypoint = target_pos

        # --- Movement Calculation (Targeting the current waypoint) ---
        if self.current_waypoint:
            self.calculate_movement_velocity(self.current_waypoint, obstacles)
        else:
            self.vx = 0 # Stop if no waypoint (shouldn't normally happen)
            self.vy = 0

        # --- Physics Update (Apply velocity and handle collisions) ---
        self.update_physics(obstacles)

    def calculate_movement_velocity(self, move_target_pos: tuple[float, float], obstacles: list[Obstacle]):
        """
        Sets the car's velocity (vx, vy) towards a specific target position,
        incorporating simple local obstacle avoidance steering.
        """
        if not move_target_pos:
            self.vx = 0
            self.vy = 0
            return

        car_center_x, car_center_y = self.get_position()
        target_dx = move_target_pos[0] - car_center_x
        target_dy = move_target_pos[1] - car_center_y

        # Normalize target direction vector
        norm_target_dx, norm_target_dy = normalize_vector(target_dx, target_dy)

        # Move at max speed towards target
        target_speed = self.max_speed

        # --- Basic Local Obstacle Avoidance ---
        avoidance_dx = 0.0
        avoidance_dy = 0.0
        avoidance_active = False
        avoidance_radius = self.width * 2.0 # How close to trigger avoidance

        for obstacle in obstacles:
            obstacle_center_x = obstacle.center[0]
            obstacle_center_y = obstacle.center[1]
            obstacle_dist = distance(car_center_x, car_center_y, obstacle_center_x, obstacle_center_y)

            if obstacle_dist < avoidance_radius:
                away_dx = car_center_x - obstacle_center_x
                away_dy = car_center_y - obstacle_center_y
                norm_away_dx, norm_away_dy = normalize_vector(away_dx, away_dy)

                # Strength increases closer to obstacle
                strength = (1.0 - (obstacle_dist / avoidance_radius)) * 1.5 # Multiplier enhances effect
                strength = max(0, strength) # Clamp strength

                avoidance_dx += norm_away_dx * strength
                avoidance_dy += norm_away_dy * strength
                if strength > 0.01:
                     avoidance_active = True

        # --- Combine Target Direction with Avoidance Force ---
        final_dx, final_dy = norm_target_dx, norm_target_dy # Default to target direction

        if avoidance_active:
            avoid_mag = math.hypot(avoidance_dx, avoidance_dy)
            if avoid_mag > 0.01:
                norm_av_dx = avoidance_dx / avoid_mag
                norm_av_dy = avoidance_dy / avoid_mag

                # Blend target and avoidance vectors
                # Simple blend: weight can be constant or dynamic
                avoid_weight = 0.6 # Constant weight for avoidance force (tune this)
                # avoid_weight = min(0.8, avoid_mag * 0.5) # Dynamic weight example

                final_dx = norm_target_dx * (1.0 - avoid_weight) + norm_av_dx * avoid_weight
                final_dy = norm_target_dy * (1.0 - avoid_weight) + norm_av_dy * avoid_weight

                # Renormalize the final blended vector
                final_dx, final_dy = normalize_vector(final_dx, final_dy)

        # --- Set Final Velocity ---
        self.vx = final_dx * target_speed
        self.vy = final_dy * target_speed


    def update_physics(self, obstacles: list[Obstacle]):
        """Applies velocity and handles collisions with obstacles and screen bounds."""
        old_x, old_y = self.x, self.y

        # Apply velocity
        self.x += self.vx
        self.y += self.vy

        # Update rect for collision checks
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        # Obstacle Collision Resolution (Revert & Bounce)
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                # Revert position to pre-collision state
                self.x, self.y = old_x, old_y

                # Approximate bounce based on velocity direction
                if abs(self.vx) > abs(self.vy): # More horizontal movement
                     self.vx *= -0.5 # Bounce X, dampen Y
                     self.vy *= 0.8
                else: # More vertical movement
                     self.vy *= -0.5 # Bounce Y, dampen X
                     self.vx *= 0.8

                # Update rect to reverted position
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                break # Handle one collision per frame


        # Screen Boundary Collision
        bounce_factor = -0.3 # How much velocity reverses
        dampen_factor = 0.8 # How much orthogonal velocity is reduced

        if self.x < 0:
            self.x = 0
            self.vx *= bounce_factor
            self.vy *= dampen_factor
        elif self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
            self.vx *= bounce_factor
            self.vy *= dampen_factor

        if self.y < 0:
            self.y = 0
            self.vy *= bounce_factor
            self.vx *= dampen_factor
        elif self.y > SCREEN_HEIGHT - self.height:
            self.y = SCREEN_HEIGHT - self.height
            self.vy *= bounce_factor
            self.vx *= dampen_factor

        # Final rect update after all adjustments
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)


    def get_position(self) -> tuple[float, float]:
        """Returns the center position of the AI car."""
        return self.x + self.width / 2.0, self.y + self.height / 2.0

    def get_velocity(self) -> tuple[float, float]:
         """Returns the current velocity (vx, vy)."""
         return self.vx, self.vy

    def draw(self, screen: pygame.Surface):
        """Draws the attacker AI car and its velocity indicator."""
        # Draw car body
        pygame.draw.rect(screen, self.color, self.rect)

        # Draw velocity indicator if moving
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            center_x = self.rect.centerx
            center_y = self.rect.centery
            # Scale velocity for drawing
            end_x = center_x + self.vx * 5
            end_y = center_y + self.vy * 5
            try:
                pygame.draw.line(screen, YELLOW, (center_x, center_y), (int(end_x), int(end_y)), 2)
            except ValueError: # Catch potential errors if coords are extreme
                 print(f"Warning: Invalid coordinates for attacker velocity line: {(center_x, center_y)} to {(end_x, end_y)}")


    def draw_path(self, screen: pygame.Surface, color: tuple[int,int,int] = ATTACKER_PATH_COLOR, dot_size: int = 3):
        """Helper function to draw the AI's current A* path."""
        if not self.path: return
        # Convert path points (floats) to integers for drawing
        try:
            points_int = [(int(p[0]), int(p[1])) for p in self.path]
            # Draw lines connecting waypoints if more than one point exists
            if len(points_int) > 1:
                pygame.draw.lines(screen, color, False, points_int, 1)
            # Draw circles at each waypoint
            for point in points_int:
                pygame.draw.circle(screen, color, point, dot_size)
            # Highlight the current target waypoint
            if self.current_waypoint:
                    # Draw a white circle outline around the current waypoint
                    pygame.draw.circle(screen, WHITE, (int(self.current_waypoint[0]), int(self.current_waypoint[1])), dot_size + 2, 1)
        except (ValueError, TypeError): # Catch errors during drawing if path/waypoint invalid
             print(f"Warning: Invalid coordinates for drawing attacker path/waypoint.")
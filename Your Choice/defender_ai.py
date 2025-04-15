import pygame
import math
# Import necessary constants including colors used in draw method
from constants import (CAR_WIDTH, CAR_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, BLUE,
                     BUFFER_BEHIND_OBSTACLE, YELLOW, HIDE_TARGET_COLOR, WHITE,
                     DARK_GRAY, STATE_IDLE_COLOR, STATE_EVADE_COLOR, STATE_PATROL_COLOR,
                     STATE_HIDE_COLOR, STATE_RETURN_COLOR) # Import all needed colors
from utils import distance, normalize_vector, check_line_of_sight
from obstacle import Obstacle # Use the unified Obstacle class
from ai.fsm import FSM, DefenseState # Import FSM logic from ai subpackage

class DefenderAI:
    """AI-controlled car that attempts to hide or evade a target using an FSM."""

    def __init__(self, x: float, y: float):
        """
        Initializes the Defender AI car.

        Args:
            x: Initial x-coordinate (top-left).
            y: Initial y-coordinate (top-left).
        """
        self.x = x
        self.y = y
        self.width = CAR_WIDTH
        self.height = CAR_HEIGHT
        self.max_speed = 4.0 # Defender speed
        self.vx = 0.0
        self.vy = 0.0
        self.color = BLUE
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)

        self.fsm = FSM() # Initialize the Finite State Machine
        self.target_car = None # The car object this AI is reacting to
        self.current_move_target: tuple[float, float] | None = None # The specific point to move towards

    def set_target(self, target_car):
        """Sets the car object the AI should react to (evade/hide from)."""
        self.target_car = target_car
        # Optionally reset FSM state or force evaluation when target is set/changed
        # self.fsm.change_state(DefenseState.IDLE) # Example: Go to IDLE initially

    def set_patrol_points(self, points: list[tuple[float, float]]):
        """Sets patrol points for the FSM."""
        self.fsm.set_patrol_points(points)
        # Optionally switch to patrol state if not currently under threat
        if self.fsm.current_state == DefenseState.IDLE:
            self.fsm.change_state(DefenseState.PATROL)

    def update(self, obstacles: list[Obstacle]):
        """
        Updates the AI's state using the FSM, calculates movement velocity
        based on the FSM's target, and updates physics.

        Args:
            obstacles: List of Obstacle objects in the environment.
        """
        if not self.target_car:
            self.vx = 0
            self.vy = 0
            # Stand still if no target to react to
            return

        # --- FSM Update ---
        # The FSM determines the *behavioral goal* (e.g., hide, evade, patrol)
        # and returns the *position* to move towards to achieve that goal.
        self.current_move_target = self.fsm.update(self, self.target_car, obstacles)

        # --- Movement Calculation ---
        # Move towards the target position provided by the FSM
        if self.current_move_target:
            self.calculate_movement_velocity(self.current_move_target, obstacles)
        else:
            # FSM didn't provide a target (shouldn't happen with fallbacks), stop.
            self.vx = 0
            self.vy = 0

        # --- Physics Update ---
        self.update_physics(obstacles)


    def calculate_movement_velocity(self, move_target_pos: tuple[float, float], obstacles: list[Obstacle]):
        """
        Sets the car's velocity (vx, vy) towards the FSM's target position,
        incorporating enhanced local obstacle avoidance suitable for hiding.
        Avoidance is weakened for the obstacle likely used for cover.
        """
        if not move_target_pos:
            self.vx = 0
            self.vy = 0
            return

        car_center_x, car_center_y = self.get_position()
        target_dx = move_target_pos[0] - car_center_x
        target_dy = move_target_pos[1] - car_center_y
        dist_to_target = math.hypot(target_dx, target_dy)

        # Normalize target direction vector
        norm_target_dx, norm_target_dy = normalize_vector(target_dx, target_dy)

        # Adjust speed (e.g., slow down when close to target, especially hide target)
        if self.fsm.current_state == DefenseState.HIDE and dist_to_target < self.width * 2:
             # Slow down proportionally when very close to hide spot
             target_speed = max(1.0, self.max_speed * (dist_to_target / (self.width * 4)))
        elif dist_to_target < 10:
             target_speed = 0 # Stop if very close to any target
        else:
             target_speed = self.max_speed # Otherwise move at max speed

        # --- Enhanced Local Obstacle Avoidance (modified from original DefenseCar) ---
        avoidance_dx = 0.0
        avoidance_dy = 0.0
        avoidance_active = False
        base_avoidance_radius = self.width * 2.5 # Base radius for detection

        # Identify the likely "cover" obstacle if hiding near one
        cover_obstacle = None
        min_dist_target_obs = float('inf')
        # Use fsm.current_hide_target as the reference point if available and in HIDE state
        hide_target_ref = self.fsm.current_hide_target if self.fsm.current_state == DefenseState.HIDE else None

        if hide_target_ref:
             target_pt = hide_target_ref
             for obs in obstacles:
                  obs_center_x = obs.center[0]
                  obs_center_y = obs.center[1]
                  d = distance(target_pt[0], target_pt[1], obs_center_x, obs_center_y)
                  # Check if distance is within buffer zone of the hide target
                  # and if it's the closest such obstacle found so far
                  if d < (obs.size / 2.0 + BUFFER_BEHIND_OBSTACLE * 1.2) and d < min_dist_target_obs :
                       min_dist_target_obs = d
                       cover_obstacle = obs

        # Calculate avoidance forces, modifying strength for cover obstacle
        for obstacle in obstacles:
            is_likely_cover = (obstacle == cover_obstacle)
            # Significantly reduce avoidance strength for the cover obstacle when hiding
            avoidance_modifier = 0.2 if is_likely_cover else 1.0

            obstacle_center_x = obstacle.center[0]
            obstacle_center_y = obstacle.center[1]
            obstacle_dist = distance(car_center_x, car_center_y, obstacle_center_x, obstacle_center_y)

            # Only apply avoidance if within the base radius
            if obstacle_dist < base_avoidance_radius:
                away_dx = car_center_x - obstacle_center_x
                away_dy = car_center_y - obstacle_center_y
                norm_away_dx, norm_away_dy = normalize_vector(away_dx, away_dy)

                # Strength increases closer to obstacle, modulated by cover status
                strength = (1.0 - (obstacle_dist / base_avoidance_radius)) * avoidance_modifier
                strength = max(0, strength) # Ensure strength isn't negative

                avoidance_dx += norm_away_dx * strength
                avoidance_dy += norm_away_dy * strength
                if strength > 0.01: # Only set active if strength is meaningful
                     avoidance_active = True

        # --- Combine Target Direction with Avoidance ---
        final_dx, final_dy = norm_target_dx, norm_target_dy # Default to target direction

        if avoidance_active:
            avoid_mag = math.hypot(avoidance_dx, avoidance_dy)
            if avoid_mag > 0.01: # Ensure avoidance vector is not zero
                norm_av_dx = avoidance_dx / avoid_mag
                norm_av_dy = avoidance_dy / avoid_mag

                # Check opposition: dot product of target dir and avoidance dir
                opposition_dot = norm_target_dx * norm_av_dx + norm_target_dy * norm_av_dy

                # Dynamic weight based on opposition (less weight if avoidance opposes target strongly)
                if opposition_dot < -0.7: # Strongly opposing
                     avoid_weight = 0.2
                elif opposition_dot < -0.2: # Generally opposing
                     avoid_weight = 0.4
                else: # Not opposing much or aligned
                     avoid_weight = 0.8 # Default higher weight

                # Blend: target * (1-weight) + avoidance * weight
                final_dx = norm_target_dx * (1.0 - avoid_weight) + norm_av_dx * avoid_weight
                final_dy = norm_target_dy * (1.0 - avoid_weight) + norm_av_dy * avoid_weight
                final_dx, final_dy = normalize_vector(final_dx, final_dy) # Renormalize final vector

        # --- Set Final Velocity ---
        self.vx = final_dx * target_speed
        self.vy = final_dy * target_speed


    def update_physics(self, obstacles: list[Obstacle]):
        """Applies velocity and handles collisions (identical to AttackerAI physics)."""
        old_x, old_y = self.x, self.y

        # Apply velocity
        self.x += self.vx
        self.y += self.vy

        # Update rect position
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        # Obstacle Collision Resolution (Revert & Bounce)
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                self.x, self.y = old_x, old_y # Revert position

                # Bounce velocity based on dominant collision axis (approx)
                if abs(self.vx) > abs(self.vy):
                     self.vx *= -0.5 # Bounce X, dampen Y
                     self.vy *= 0.8
                else:
                     self.vy *= -0.5 # Bounce Y, dampen X
                     self.vx *= 0.8

                self.rect.x = int(self.x) # Update rect to reverted position
                self.rect.y = int(self.y)
                break # Handle one collision per frame

        # Screen Boundary Collision
        bounce_factor = -0.3
        dampen_factor = 0.8
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

        # Final rect update
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)


    def get_position(self) -> tuple[float, float]:
        """Returns the center position of the AI car."""
        return self.x + self.width / 2.0, self.y + self.height / 2.0

    def get_velocity(self) -> tuple[float, float]:
         """Returns the current velocity (vx, vy)."""
         return self.vx, self.vy

    def draw(self, screen: pygame.Surface):
        """Draws the defender AI car and its state/target info."""
        # Draw car body
        pygame.draw.rect(screen, self.color, self.rect)

        # Draw FSM state indicator (small circle near top-left of car rect)
        # Using color constants imported from constants.py
        state_color = {
            DefenseState.IDLE: STATE_IDLE_COLOR,
            DefenseState.EVADE: STATE_EVADE_COLOR,
            DefenseState.PATROL: STATE_PATROL_COLOR,
            DefenseState.HIDE: STATE_HIDE_COLOR,
            DefenseState.RETURN_TO_SAFE_AREA: STATE_RETURN_COLOR
        }.get(self.fsm.current_state, DARK_GRAY) # Use DARK_GRAY as fallback
        indicator_pos = (self.rect.left + 5, self.rect.top + 5)
        pygame.draw.circle(screen, state_color, indicator_pos, 5)

        # Draw current movement target (from FSM) as a yellow circle/line
        if self.current_move_target:
            try:
                tgt_x, tgt_y = int(self.current_move_target[0]), int(self.current_move_target[1])
                pygame.draw.circle(screen, YELLOW, (tgt_x, tgt_y), 4, 1) # Yellow circle outline
                # Draw line from car center to target
                pygame.draw.line(screen, YELLOW, self.rect.center, (tgt_x, tgt_y), 1)
            except (ValueError, TypeError): # Catch potential errors if target is invalid
                print(f"Warning: Invalid coordinates for defender move target: {self.current_move_target}")


        # Draw specific HIDE target (if different from move target) as a purple circle
        if self.fsm.current_state == DefenseState.HIDE and self.fsm.current_hide_target:
             try:
                hide_tgt_x, hide_tgt_y = int(self.fsm.current_hide_target[0]), int(self.fsm.current_hide_target[1])
                current_move_int = (int(self.current_move_target[0]), int(self.current_move_target[1])) if self.current_move_target else None
                # Draw only if hide target is valid and different from the immediate move target
                if (hide_tgt_x, hide_tgt_y) != current_move_int:
                    pygame.draw.circle(screen, HIDE_TARGET_COLOR, (hide_tgt_x, hide_tgt_y), 6, 2) # Purple thick circle
             except (ValueError, TypeError):
                  print(f"Warning: Invalid coordinates for defender hide target: {self.fsm.current_hide_target}")
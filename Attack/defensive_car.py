import pygame
import math
from constants import *
# Import DefenseState if needed for potential future FSM state check within move_to_target
# from ai.fsm import DefenseState
from utils import distance, normalize_vector, is_in_screen


class DefenseCar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = CAR_WIDTH
        self.height = CAR_HEIGHT
        self.max_speed = 4
        self.vx = 0
        self.vy = 0
        self.color = BLUE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move_to_target(self, target_pos, obstacles):
        """
        Sets the car's velocity towards target position, including basic obstacle avoidance.
        Avoidance is weakened for the obstacle closest to the target (likely cover).
        """
        if not target_pos:
            # No target, stop moving
            self.vx = 0
            self.vy = 0
            return

        car_center_x = self.x + self.width / 2
        car_center_y = self.y + self.height / 2
        dx = target_pos[0] - car_center_x
        dy = target_pos[1] - car_center_y
        dist = max(0.1, distance(0, 0, dx, dy))
        dx, dy = normalize_vector(dx, dy) # Target direction

        # Adjust speed based on distance to target (simple approach)
        target_speed = min(self.max_speed, dist / 10) # Speed ramps up as it gets further

        # --- Basic Local Obstacle Avoidance Steering ---
        avoidance_dx = 0
        avoidance_dy = 0
        avoidance_active = False

        # Find the obstacle closest to the *target* position.
        # Assume this is the obstacle the car is trying to use for cover if hiding.
        cover_obstacle = None
        min_dist_target_obs = float('inf')
        if target_pos: # Ensure target_pos is valid before using it
             for obs in obstacles:
                  obs_center_x = obs.x + obs.size / 2
                  obs_center_y = obs.y + obs.size / 2
                  d = distance(target_pos[0], target_pos[1], obs_center_x, obs_center_y)
                  # Find obstacle closest to the target point.
                  if d < min_dist_target_obs:
                       min_dist_target_obs = d
                       cover_obstacle = obs

        # --- Loop through obstacles for avoidance calculation ---
        for obstacle in obstacles:
            # Determine if this is the likely cover obstacle
            is_likely_cover = False
            if cover_obstacle is not None and obstacle == cover_obstacle:
                 # Check if the target is indeed close to this identified cover obstacle
                 # Using a threshold relative to obstacle size + buffer seems reasonable
                 if min_dist_target_obs < (obstacle.size / 2 + BUFFER_BEHIND_OBSTACLE) * 1.2: # Allow some tolerance
                      is_likely_cover = True

            # Set the avoidance strength modifier based on whether it's cover
            if is_likely_cover:
                 # Apply weaker avoidance for the cover obstacle
                 avoidance_modifier = 0.3 # Significantly reduce effect (tune this value)
            else:
                 # Use normal avoidance strength for other obstacles
                 avoidance_modifier = 1.0

            # --- Calculate avoidance force for this obstacle ---
            obstacle_center_x = obstacle.x + obstacle.size / 2
            obstacle_center_y = obstacle.y + obstacle.size / 2
            obstacle_dist = distance(car_center_x, car_center_y,
                                     obstacle_center_x, obstacle_center_y)

            # Define the base radius within which avoidance kicks in
            base_avoidance_radius = self.width * 2.5 # Adjust as needed

            # Check if within the (potentially modified) radius
            effective_avoidance_radius = base_avoidance_radius # Start with base radius

            # No need to modify radius itself for Option B, just the strength
            # effective_avoidance_radius = base_avoidance_radius * avoidance_modifier

            if obstacle_dist < effective_avoidance_radius:
                # Calculate direction away from the obstacle
                away_dx = car_center_x - obstacle_center_x
                away_dy = car_center_y - obstacle_center_y
                away_dx, away_dy = normalize_vector(away_dx, away_dy)

                # Calculate base strength (stronger when closer)
                strength = (1.0 - (obstacle_dist / effective_avoidance_radius))

                # Apply the modifier to the strength
                strength *= avoidance_modifier # Weaken effect if it's the cover obstacle

                # Accumulate avoidance vector components
                if strength > 0: # Only add if there's actual strength
                    avoidance_dx += away_dx * strength
                    avoidance_dy += away_dy * strength
                    avoidance_active = True


        # --- Combine Target Direction with Avoidance ---
        if avoidance_active:
            # Normalize the combined avoidance vector only if it has magnitude
            avoidance_mag = math.sqrt(avoidance_dx**2 + avoidance_dy**2)
            if avoidance_mag > 0.01:
                norm_av_dx = avoidance_dx / avoidance_mag
                norm_av_dy = avoidance_dy / avoidance_mag

                # --- NEW: Check how much avoidance opposes target direction ---
                # Dot product between target direction and *normalized* avoidance direction
                opposition_dot = dx * norm_av_dx + dy * norm_av_dy
                # opposition_dot = -1 means directly opposing
                # opposition_dot = 1 means pointing same direction
                # opposition_dot = 0 means perpendicular

                # Dynamically adjust avoidance weight based on opposition
                # If avoidance strongly opposes target (e.g., dot < -0.5), heavily reduce its weight
                if opposition_dot < -0.5:
                     avoid_weight = 0.1 # Very low weight if opposing strongly
                elif opposition_dot < 0:
                     avoid_weight = 0.3 # Low weight if generally opposing
                else:
                     avoid_weight = 0.7 # Default higher weight if not opposing

                final_dx = dx * (1.0 - avoid_weight) + norm_av_dx * avoid_weight # Use normalized avoidance vector
                final_dy = dy * (1.0 - avoid_weight) + norm_av_dy * avoid_weight # Use normalized avoidance vector
                final_dx, final_dy = normalize_vector(final_dx, final_dy) # Ensure final result is normalized
            else:
                # Avoidance calculated but resulted in near-zero vector, use target direction
                 final_dx, final_dy = dx, dy

        else:
            # No avoidance necessary
            final_dx, final_dy = dx, dy

        # Set final velocity based on combined direction and target speed
        self.vx = final_dx * target_speed
        self.vy = final_dy * target_speed


    def update(self, obstacles):
        """Update car position based on velocity with collision detection."""
        # Save old position for collision resolution
        old_x, old_y = self.x, self.y

        # Update X position
        self.x += self.vx
        self.rect.x = int(self.x) # Use int for rect position

        # Check for collisions in X direction
        collided_x = False
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                # Revert X position
                self.x = old_x
                self.rect.x = int(old_x)
                # Dampen velocity component due to collision
                self.vx *= -0.5 # Bounce slightly
                collided_x = True
                break

        # Update Y position
        self.y += self.vy
        self.rect.y = int(self.y) # Use int for rect position

        # Check for collisions in Y direction
        # Note: A collision might resolve X, then still collide on Y in the new frame.
        # Re-checking all obstacles for Y collision is generally needed.
        collided_y = False
        for obstacle in obstacles:
             if self.rect.colliderect(obstacle.rect):
                # Revert Y position
                self.y = old_y
                self.rect.y = int(old_y)
                # Dampen velocity component due to collision
                self.vy *= -0.5 # Bounce slightly
                collided_y = True
                break # Stop checking Y after first collision


        # Keep within screen boundaries (apply after potential collision resolution)
        bounce_factor = -0.5 # How much velocity reverses on hitting boundary

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

        # Update rect position finally after all adjustments
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)


    def get_position(self):
        """Get the center position of the car."""
        return (self.x + self.width/2, self.y + self.height/2)
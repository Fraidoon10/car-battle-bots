from enum import Enum
import math
# Make sure utils are imported correctly
from utils import distance, normalize_vector, check_line_of_sight
# Import constants needed
from constants import (SAFE_DISTANCE, MIN_DISTANCE, SCREEN_WIDTH, SCREEN_HEIGHT,
                     HIDE_TRIGGER_DISTANCE, BUFFER_BEHIND_OBSTACLE,
                     MAX_HIDE_SEARCH_OBSTACLES, VERY_CLOSE_DISTANCE,
                     OBSTACLE_SORT_WEIGHT_DIST, OBSTACLE_SORT_WEIGHT_ANGLE)
import pygame # Needed for get_ticks in timer example (if used)

class DefenseState(Enum):
    """States for the defensive car's FSM."""
    IDLE = 0
    EVADE = 1  # Now primarily a fallback or emergency state
    PATROL = 2
    HIDE = 3   # New state for seeking cover
    RETURN_TO_SAFE_AREA = 4

class FSM:
    """Finite State Machine for the defensive car, prioritizing hiding."""

    def __init__(self):
        self.current_state = DefenseState.IDLE
        self.patrol_points = []
        self.current_patrol_index = 0
        self.state_handlers = {
            DefenseState.IDLE: self.handle_idle,
            DefenseState.EVADE: self.handle_evade,
            DefenseState.PATROL: self.handle_patrol,
            DefenseState.HIDE: self.handle_hide, # Add handler for HIDE
            DefenseState.RETURN_TO_SAFE_AREA: self.handle_return_to_safe_area
        }
        self.last_target_pos = None
        self.current_hide_target = None # Store the specific hide spot being targeted

        # Optional: Timer for state stability (can uncomment if needed)
        # self.state_entry_time = 0
        # self.min_state_time = 500 # e.g., 0.5 seconds minimum in any state

    def set_patrol_points(self, points):
        self.patrol_points = points
        self.current_patrol_index = 0

    def _is_safe(self, defense_pos, player_pos, obstacles):
        """Checks if the defender is currently hidden from the player."""
        return check_line_of_sight(player_pos, defense_pos, obstacles)

    def update(self, defense_car, player_car, obstacles, screen_width, screen_height):
        """Update the FSM based on current conditions and return a target position."""
        defense_pos = defense_car.get_position()
        player_pos = player_car.get_position()

        # --- Pre-computation for state transitions ---
        dist_to_player = distance(player_pos[0], player_pos[1], defense_pos[0], defense_pos[1])
        is_currently_safe = self._is_safe(defense_pos, player_pos, obstacles)

        # --- Core State Transition Logic ---
        next_state = self.current_state # Assume no change initially

        # Optional Timer Check (Uncomment if using timer)
        # current_time = pygame.time.get_ticks()
        # time_in_state = current_time - self.state_entry_time
        # allow_transition = time_in_state > self.min_state_time

        # Conditions to switch states (evaluate these based on priority)
        if dist_to_player < VERY_CLOSE_DISTANCE:
             # Highest priority: If player is extremely close, force simple EVADE
             next_state = DefenseState.EVADE
        elif not is_currently_safe and dist_to_player < HIDE_TRIGGER_DISTANCE:
             # If not safe and player is reasonably close, try to HIDE
             next_state = DefenseState.HIDE
        elif is_currently_safe and self.current_state == DefenseState.HIDE:
             # If already hiding and safe, stay in HIDE (or maybe IDLE if player is far?)
             if dist_to_player > HIDE_TRIGGER_DISTANCE * 1.2: # If player moves away while hidden
                 next_state = DefenseState.PATROL if self.patrol_points else DefenseState.IDLE
             else:
                 next_state = DefenseState.HIDE # Maintain HIDE state
        elif self.current_state == DefenseState.HIDE and not is_currently_safe:
             # If was hiding but now exposed (player moved), re-evaluate HIDE
             next_state = DefenseState.HIDE # Stay in HIDE to find a *new* spot
        elif dist_to_player > HIDE_TRIGGER_DISTANCE * 1.2: # If player is far away
             # Default to PATROL or IDLE when player is not a threat
             next_state = DefenseState.PATROL if self.patrol_points else DefenseState.IDLE
        # Add other transitions as needed (e.g., from PATROL to HIDE)


        # --- Execute State Handler ---
        # Handle state change and get target from the *new* state if it changed
        if next_state != self.current_state: # and allow_transition): # Add timer check if using
            print(f"FSM Changing State: {self.current_state.name} -> {next_state.name}") # Debug state change
            self.current_state = next_state
            # Optional Timer Reset (Uncomment if using timer)
            # self.state_entry_time = pygame.time.get_ticks()
            self.current_hide_target = None # Reset hide target when state changes

        # Get target from the (potentially new) current state's handler
        handler = self.state_handlers[self.current_state]
        target_position = handler(defense_car, player_car, obstacles, screen_width, screen_height)

        # --- Target Position Validation ---
        if target_position is not None and not (math.isnan(target_position[0]) or math.isnan(target_position[1])):
            self.last_target_pos = target_position
        else:
            # Fallback if handler returns invalid target
            target_position = self.last_target_pos if self.last_target_pos else defense_pos

        # Store the specific hide target if in HIDE state
        if self.current_state == DefenseState.HIDE:
            self.current_hide_target = target_position

        return target_position


    def handle_idle(self, defense_car, player_car, obstacles, screen_width, screen_height):
        """IDLE: Wait. Transitions handled in main update logic."""
        # No movement target needed, just stay put. Transitions are handled centrally.
        return defense_car.get_position()

    def handle_patrol(self, defense_car, player_car, obstacles, screen_width, screen_height):
        """PATROL: Move between waypoints. Transitions handled in main update logic."""
        if not self.patrol_points:
            # Should have transitioned to IDLE already, but fallback safety
            return defense_car.get_position()

        defense_pos = defense_car.get_position()
        target = self.patrol_points[self.current_patrol_index]
        dist_to_target = distance(defense_pos[0], defense_pos[1], target[0], target[1])

        if dist_to_target < 30:
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
            target = self.patrol_points[self.current_patrol_index]
            print(f"Patrolling to point {self.current_patrol_index}: {target}")

        return target

    def handle_evade(self, defense_car, player_car, obstacles, screen_width, screen_height):
        """EVADE: Simple fallback - move directly away from player."""
        # This is now mainly for when the player is VERY close or hiding fails.
        player_pos = player_car.get_position()
        defense_pos = defense_car.get_position()

        dx = defense_pos[0] - player_pos[0]
        dy = defense_pos[1] - player_pos[1]
        dx, dy = normalize_vector(dx, dy)

        # Target slightly further than SAFE_DISTANCE to encourage clearing the area
        target_x = defense_pos[0] + dx * SAFE_DISTANCE * 1.1
        target_y = defense_pos[1] + dy * SAFE_DISTANCE * 1.1

        # Basic boundary clamping (could be improved)
        margin = defense_car.width
        target_x = max(margin, min(target_x, screen_width - margin))
        target_y = max(margin, min(target_y, screen_height - margin))

        # Transitions are handled centrally now, so just return the target
        return (target_x, target_y)

    def handle_hide(self, defense_car, player_car, obstacles, screen_width, screen_height):
        """HIDE: Find the best obstacle to hide behind and target that spot."""
        defense_pos = defense_car.get_position()
        player_pos = player_car.get_position()

        # 0. Check if already safe at current hide target
        if self.current_hide_target and distance(defense_pos[0], defense_pos[1], self.current_hide_target[0], self.current_hide_target[1]) < 20:
             if self._is_safe(defense_pos, player_pos, obstacles):
                  # Close to target and safe, just stay put
                  return defense_pos
             else:
                  # Reached target but it's not safe anymore, find a new one
                  self.current_hide_target = None


        # 1. Find Potential Cover Obstacles
        candidate_obstacles = []
        for obs in obstacles:
            obs_center = (obs.rect.centerx, obs.rect.centery)
            dist_def_obs = distance(defense_pos[0], defense_pos[1], obs_center[0], obs_center[1])
            dist_ply_obs = distance(player_pos[0], player_pos[1], obs_center[0], obs_center[1])
            dist_ply_def = distance(player_pos[0], player_pos[1], defense_pos[0], defense_pos[1])

            # Simple filter: Obstacle should be roughly between player and defender,
            # or closer to defender than player is to defender.
            if dist_ply_obs < dist_ply_def * 1.2 and dist_def_obs < dist_ply_def * 1.5:
                 # Calculate angle Attacker -> Defender -> Obstacle
                 vec_def_ply = (player_pos[0] - defense_pos[0], player_pos[1] - defense_pos[1])
                 vec_def_obs = (obs_center[0] - defense_pos[0], obs_center[1] - defense_pos[1])
                 dot = vec_def_ply[0]*vec_def_obs[0] + vec_def_ply[1]*vec_def_obs[1]
                 mag_ply = math.sqrt(vec_def_ply[0]**2 + vec_def_ply[1]**2)
                 mag_obs = math.sqrt(vec_def_obs[0]**2 + vec_def_obs[1]**2)
                 if mag_ply > 0 and mag_obs > 0:
                     angle_cos = dot / (mag_ply * mag_obs)
                     angle_rad = math.acos(max(-1.0, min(1.0, angle_cos))) # Clamp for precision issues
                     angle_deg = math.degrees(angle_rad)

                     # Score based on distance and angle (lower is better)
                     # Prioritize obstacles closer to the defender and more directly 'behind' relative to player
                     score = (dist_def_obs * OBSTACLE_SORT_WEIGHT_DIST +
                              angle_deg * OBSTACLE_SORT_WEIGHT_ANGLE) # Lower angle relative to player line is better
                     candidate_obstacles.append({'obstacle': obs, 'score': score})


        # Sort candidates (lowest score first) and limit
        candidate_obstacles.sort(key=lambda x: x['score'])
        potential_spots = []

        # 2. Calculate and Evaluate Hiding Spots for best candidates
        for candidate in candidate_obstacles[:MAX_HIDE_SEARCH_OBSTACLES]:
            obs = candidate['obstacle']
            obs_center = (obs.rect.centerx, obs.rect.centery)

            # Vector from player to obstacle
            dx_po = obs_center[0] - player_pos[0]
            dy_po = obs_center[1] - player_pos[1]
            dx_po, dy_po = normalize_vector(dx_po, dy_po)

            # Calculate point directly behind obstacle
            hide_x = obs_center[0] + dx_po * (obs.size / 2 + BUFFER_BEHIND_OBSTACLE)
            hide_y = obs_center[1] + dy_po * (obs.size / 2 + BUFFER_BEHIND_OBSTACLE)
            potential_spot = (hide_x, hide_y)

            # Ensure spot is within screen bounds (simple check)
            if not (0 < hide_x < screen_width and 0 < hide_y < screen_height):
                continue

            # 3. Check if this spot is actually safe (LOS check)
            if self._is_safe(potential_spot, player_pos, obstacles):
                 # Store the safe spot and its distance from the defender
                 dist_to_spot = distance(defense_pos[0], defense_pos[1], hide_x, hide_y)
                 potential_spots.append({'pos': potential_spot, 'dist': dist_to_spot})
                 # Optimization: If we found a good spot, maybe stop searching early?
                 # if len(potential_spots) >= 1: break


        # 4. Select Best Hiding Spot (closest reachable one)
        if potential_spots:
            # Sort potential spots by distance to defender (closest first)
            potential_spots.sort(key=lambda x: x['dist'])
            best_spot = potential_spots[0]['pos']
            print(f"Hiding: Found safe spot at {best_spot}")
            return best_spot
        else:
            # 5. No Safe Spot Found - Fallback to EVADE
            print("Hiding: No safe spot found, falling back to EVADE.")
            # Transitioning back to EVADE should happen in the main update loop
            # For now, just return an evasion target from here as a fallback action
            evade_target = self.handle_evade(defense_car, player_car, obstacles, screen_width, screen_height)
            return evade_target


    def handle_return_to_safe_area(self, defense_car, player_car, obstacles, screen_width, screen_height):
        """RETURN_TO_SAFE_AREA: Move towards screen center if stuck or lost."""
        # Transitions handled centrally.
        target_x = screen_width / 2
        target_y = screen_height / 2
        return (target_x, target_y)
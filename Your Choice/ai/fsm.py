# CombinedChaseHideGame/ai/fsm.py
# --- START OF FILE fsm.py ---

from enum import Enum
import math
import pygame # Needed for get_ticks in timer example (if used)
# Updated imports to top-level modules
from utils import distance, normalize_vector, check_line_of_sight
from constants import (SAFE_DISTANCE, MIN_DISTANCE, # MIN_DISTANCE might be unused
                     HIDE_TRIGGER_DISTANCE, BUFFER_BEHIND_OBSTACLE,
                     MAX_HIDE_SEARCH_OBSTACLES, VERY_CLOSE_DISTANCE,
                     OBSTACLE_SORT_WEIGHT_DIST, OBSTACLE_SORT_WEIGHT_ANGLE,
                     SCREEN_WIDTH, SCREEN_HEIGHT) # Import screen dims if needed

class DefenseState(Enum):
    """States for the defensive car's FSM."""
    IDLE = 0
    EVADE = 1  # Now primarily a fallback or emergency state
    PATROL = 2
    HIDE = 3   # New state for seeking cover
    RETURN_TO_SAFE_AREA = 4 # Optional state, e.g., if lost

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
        self.last_target_pos = None # Store last valid target
        self.current_hide_target = None # Store the specific hide spot being targeted by HIDE state

        # Optional: Timer for state stability
        self.state_entry_time = 0
        self.min_state_time = 500 # e.g., 0.5 seconds minimum in any state

    def set_patrol_points(self, points: list[tuple[float, float]]):
        """Sets the patrol points for the PATROL state."""
        self.patrol_points = points
        self.current_patrol_index = 0
        # If setting patrol points, perhaps default to PATROL state?
        # if not self.current_state == DefenseState.HIDE and not self.current_state == DefenseState.EVADE:
        #    self.change_state(DefenseState.PATROL)


    def _is_safe(self, defense_pos: tuple[float, float], player_pos: tuple[float, float], obstacles: list) -> bool:
        """Checks if the defender is currently hidden from the player (LOS blocked)."""
        # Note: check_line_of_sight returns True if BLOCKED, False if CLEAR.
        # So, "safe" means LOS is blocked.
        return check_line_of_sight(player_pos, defense_pos, obstacles)

    def change_state(self, next_state: DefenseState):
        """Changes the current state and resets timer/hide target."""
        if self.current_state != next_state:
            print(f"FSM Changing State: {self.current_state.name} -> {next_state.name}") # Debug
            self.current_state = next_state
            self.state_entry_time = pygame.time.get_ticks()
            self.current_hide_target = None # Reset hide target when state changes
            # Reset last target pos maybe? Or keep it for fallback? Keeping it seems safer.
            # self.last_target_pos = None


    def update(self, defense_car, player_car, obstacles: list) -> tuple[float, float]:
        """
        Update the FSM based on current game conditions.
        Determines the appropriate state and returns a target position for the defense_car.
        """
        defense_pos = defense_car.get_position()
        player_pos = player_car.get_position() # Assuming player_car has get_position

        # --- Pre-computation for state transitions ---
        dist_to_player = distance(player_pos[0], player_pos[1], defense_pos[0], defense_pos[1])
        is_currently_safe = self._is_safe(defense_pos, player_pos, obstacles)

        # --- State Transition Logic ---
        next_state = self.current_state # Assume no change initially

        # Timer check for state stability
        current_time = pygame.time.get_ticks()
        time_in_state = current_time - self.state_entry_time
        allow_transition = time_in_state >= self.min_state_time

        # Evaluate transitions only if minimum time in state is met (or for critical overrides)
        if dist_to_player < VERY_CLOSE_DISTANCE:
            # Highest priority: If player is extremely close, force EVADE regardless of timer
            next_state = DefenseState.EVADE
        elif allow_transition:
            # --- Evaluate other transitions based on priority ---
            if not is_currently_safe and dist_to_player < HIDE_TRIGGER_DISTANCE:
                # If not safe and player is reasonably close, try to HIDE
                next_state = DefenseState.HIDE
            elif is_currently_safe and self.current_state == DefenseState.HIDE:
                # If currently hiding and safe:
                if dist_to_player > HIDE_TRIGGER_DISTANCE * 1.2: # If player moves far away
                    next_state = DefenseState.PATROL if self.patrol_points else DefenseState.IDLE
                else:
                    next_state = DefenseState.HIDE # Maintain HIDE state
            elif self.current_state == DefenseState.HIDE and not is_currently_safe:
                # If was hiding but now exposed (player moved), re-evaluate HIDE
                next_state = DefenseState.HIDE # Stay in HIDE to find a *new* spot immediately
            elif dist_to_player > HIDE_TRIGGER_DISTANCE * 1.1: # If player is far away (use hysteresis)
                # Default to PATROL or IDLE when player is not a threat
                if self.current_state != DefenseState.PATROL and self.current_state != DefenseState.IDLE:
                     next_state = DefenseState.PATROL if self.patrol_points else DefenseState.IDLE
            # Add transitions from PATROL/IDLE to HIDE if player gets close
            elif (self.current_state == DefenseState.PATROL or self.current_state == DefenseState.IDLE) and \
                 dist_to_player < HIDE_TRIGGER_DISTANCE:
                 next_state = DefenseState.HIDE


        # --- Apply State Change ---
        if next_state != self.current_state:
            self.change_state(next_state)

        # --- Execute State Handler ---
        handler = self.state_handlers.get(self.current_state, self.handle_idle) # Fallback to idle
        target_position = handler(defense_car, player_car, obstacles)

        # --- Target Position Validation & Fallback ---
        if target_position is not None and not (math.isnan(target_position[0]) or math.isnan(target_position[1])):
            self.last_target_pos = target_position
        else:
            # Fallback if handler returns invalid target (e.g., None or NaN)
            target_position = self.last_target_pos if self.last_target_pos else defense_pos
            print(f"Warning: FSM handler for state {self.current_state.name} returned invalid target. Using fallback: {target_position}")

        # Store the specific hide target if in HIDE state for visualization/logic
        if self.current_state == DefenseState.HIDE and handler == self.handle_hide:
             # Only update current_hide_target if handle_hide provided a valid spot
             # handle_hide might return an evade target if no spot is found
             if target_position != self.last_target_pos: # Check if it's a newly calculated spot
                  potential_hide_spot = self.find_best_hiding_spot(defense_car, player_car, obstacles)
                  if potential_hide_spot:
                      self.current_hide_target = potential_hide_spot
                  # else: # If no spot found, handle_hide returns evade target, don't set current_hide_target
                  #     pass


        return target_position

    # --- State Handler Implementations ---

    def handle_idle(self, defense_car, player_car, obstacles: list) -> tuple[float, float]:
        """IDLE: Stay put. Transitions handled in main update logic."""
        return defense_car.get_position()

    def handle_patrol(self, defense_car, player_car, obstacles: list) -> tuple[float, float]:
        """PATROL: Move between waypoints. Transitions handled in main update logic."""
        if not self.patrol_points:
            self.change_state(DefenseState.IDLE) # Should not happen if logic is right, but safe
            return defense_car.get_position()

        defense_pos = defense_car.get_position()
        target = self.patrol_points[self.current_patrol_index]
        dist_to_target = distance(defense_pos[0], defense_pos[1], target[0], target[1])

        # Check if close enough to the current waypoint
        waypoint_radius = 30 # How close to be considered "reached"
        if dist_to_target < waypoint_radius:
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
            target = self.patrol_points[self.current_patrol_index]
            print(f"Patrolling to point {self.current_patrol_index}: {target}")
            # Set last_target_pos explicitly here?
            self.last_target_pos = target

        return target

    def handle_evade(self, defense_car, player_car, obstacles: list) -> tuple[float, float]:
        """EVADE: Simple fallback - move directly away from player."""
        player_pos = player_car.get_position()
        defense_pos = defense_car.get_position()

        dx = defense_pos[0] - player_pos[0]
        dy = defense_pos[1] - player_pos[1]
        norm_dx, norm_dy = normalize_vector(dx, dy)

        # Target slightly further than SAFE_DISTANCE to encourage clearing the area
        target_x = defense_pos[0] + norm_dx * SAFE_DISTANCE * 1.1
        target_y = defense_pos[1] + norm_dy * SAFE_DISTANCE * 1.1

        # Basic boundary clamping
        margin = defense_car.width # Use car dimensions as margin
        target_x = max(margin, min(target_x, SCREEN_WIDTH - margin))
        target_y = max(margin, min(target_y, SCREEN_HEIGHT - margin))

        return (target_x, target_y)


    def find_best_hiding_spot(self, defense_car, player_car, obstacles: list) -> tuple[float, float] | None:
        """Finds the best hiding spot behind an obstacle."""
        defense_pos = defense_car.get_position()
        player_pos = player_car.get_position()

        candidate_obstacles = []
        for obs in obstacles:
            # Simple filter: only consider obstacles somewhat near the defender
            obs_center = (obs.rect.centerx, obs.rect.centery)
            dist_def_obs = distance(defense_pos[0], defense_pos[1], obs_center[0], obs_center[1])
            # Max distance to consider an obstacle for hiding
            max_relevant_dist = HIDE_TRIGGER_DISTANCE * 1.5
            if dist_def_obs > max_relevant_dist:
                continue

            dist_ply_obs = distance(player_pos[0], player_pos[1], obs_center[0], obs_center[1])
            dist_ply_def = distance(player_pos[0], player_pos[1], defense_pos[0], defense_pos[1])

            # Obstacle needs to be generally between player and defender or closer to defender
            if dist_ply_obs < dist_ply_def * 1.2 or dist_def_obs < dist_ply_def:
                 # Calculate angle: Player -> Defender -> Obstacle
                 vec_def_ply = (player_pos[0] - defense_pos[0], player_pos[1] - defense_pos[1])
                 vec_def_obs = (obs_center[0] - defense_pos[0], obs_center[1] - defense_pos[1])
                 mag_ply = math.hypot(vec_def_ply[0], vec_def_ply[1])
                 mag_obs = math.hypot(vec_def_obs[0], vec_def_obs[1])

                 angle_deg = 180 # Default to max penalty if vectors are zero
                 if mag_ply > 0.1 and mag_obs > 0.1:
                     dot = vec_def_ply[0]*vec_def_obs[0] + vec_def_ply[1]*vec_def_obs[1]
                     angle_cos = max(-1.0, min(1.0, dot / (mag_ply * mag_obs))) # Clamp cosine
                     angle_rad = math.acos(angle_cos)
                     angle_deg = math.degrees(angle_rad)
                     # We want the angle relative to the line *away* from the player
                     # A smaller angle means the obstacle is more directly behind the defender relative to the player
                     # Angle from Player->Defender line to Defender->Obstacle line. Low is good.

                 # Score based on distance and angle (lower is better)
                 score = (dist_def_obs * OBSTACLE_SORT_WEIGHT_DIST +
                          angle_deg * OBSTACLE_SORT_WEIGHT_ANGLE)
                 candidate_obstacles.append({'obstacle': obs, 'score': score})


        # Sort candidates (lowest score first) and limit search
        candidate_obstacles.sort(key=lambda x: x['score'])
        potential_spots = []

        for candidate in candidate_obstacles[:MAX_HIDE_SEARCH_OBSTACLES]:
            obs = candidate['obstacle']
            obs_center = (obs.rect.centerx, obs.rect.centery)

            # Vector from player towards obstacle center (direction to hide behind)
            dx_po = obs_center[0] - player_pos[0]
            dy_po = obs_center[1] - player_pos[1]
            norm_dx_po, norm_dy_po = normalize_vector(dx_po, dy_po)

            # Calculate point behind obstacle
            buffer = obs.size / 2.0 + BUFFER_BEHIND_OBSTACLE
            hide_x = obs_center[0] + norm_dx_po * buffer
            hide_y = obs_center[1] + norm_dy_po * buffer
            potential_spot = (hide_x, hide_y)

            # Ensure spot is within screen bounds (simple check)
            margin = 10 # Small margin from edge
            if not (margin < hide_x < SCREEN_WIDTH - margin and margin < hide_y < SCREEN_HEIGHT - margin):
                continue

            # Check if this spot is actually safe (LOS check from player to spot)
            if self._is_safe(potential_spot, player_pos, obstacles):
                 dist_to_spot = distance(defense_pos[0], defense_pos[1], hide_x, hide_y)
                 potential_spots.append({'pos': potential_spot, 'dist': dist_to_spot})
                 # Optimization: Found one good spot, maybe that's enough?
                 # break # Uncomment to take the first valid spot found from sorted list


        # Select Best Hiding Spot (closest safe one)
        if potential_spots:
            potential_spots.sort(key=lambda x: x['dist']) # Sort by distance to defender
            best_spot = potential_spots[0]['pos']
            # print(f"Hiding: Found safe spot at {tuple(map(int,best_spot))}")
            return best_spot
        else:
            # No Safe Spot Found
            return None


    def handle_hide(self, defense_car, player_car, obstacles: list) -> tuple[float, float]:
        """HIDE: Find the best obstacle to hide behind and target that spot."""
        defense_pos = defense_car.get_position()
        player_pos = player_car.get_position() # Needed for safety check

        # 0. Check if already close to current target and safe
        if self.current_hide_target and distance(defense_pos[0], defense_pos[1], self.current_hide_target[0], self.current_hide_target[1]) < 20:
            if self._is_safe(defense_pos, player_pos, obstacles):
                 # Close to target and safe, stay put
                 return defense_pos
            else:
                 # Reached target but it became unsafe, find a new one
                 self.current_hide_target = None # Force recalculation

        # 1. If we don't have a target, or the current one isn't safe anymore, find one
        if not self.current_hide_target:
             best_spot = self.find_best_hiding_spot(defense_car, player_car, obstacles)
             if best_spot:
                 self.current_hide_target = best_spot # Store the newly found target
                 # print(f"Hiding: Targeting new spot {tuple(map(int,best_spot))}")
                 return best_spot # Return the new target
             else:
                 # No safe spot found - Fallback to EVADE immediately
                 print("Hiding: No safe spot found, falling back to EVADE.")
                 # Change state in the main update loop based on this fallback?
                 # For now, just return an evasion target directly from here.
                 evade_target = self.handle_evade(defense_car, player_car, obstacles)
                 # We should probably trigger state change *out* of HIDE here
                 # self.change_state(DefenseState.EVADE) # Let main loop handle this?
                 return evade_target
        else:
            # We have a target, move towards it
             # Check if the existing target is *still* safe before returning it
             if self._is_safe(self.current_hide_target, player_pos, obstacles):
                return self.current_hide_target
             else:
                # Existing target became unsafe, find a new one
                self.current_hide_target = None # Clear old target
                # Rerun the find logic immediately
                return self.handle_hide(defense_car, player_car, obstacles)


    def handle_return_to_safe_area(self, defense_car, player_car, obstacles: list) -> tuple[float, float]:
        """RETURN_TO_SAFE_AREA: Move towards screen center."""
        # This state might be entered if the car gets stuck or lost
        target_x = SCREEN_WIDTH / 2
        target_y = SCREEN_HEIGHT / 2
        # Maybe transition back to PATROL/IDLE once center is reached?
        defense_pos = defense_car.get_position()
        if distance(defense_pos[0], defense_pos[1], target_x, target_y) < 50:
             self.change_state(DefenseState.PATROL if self.patrol_points else DefenseState.IDLE)

        return (target_x, target_y)

# --- END OF FILE fsm.py ---
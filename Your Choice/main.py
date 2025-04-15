import pygame
import sys
import random
import math
import time
import traceback # Import traceback module for detailed error printing
from enum import Enum

# --- Core Components ---
from constants import *
from utils import distance, check_line_of_sight
from obstacle import Obstacle, generate_obstacles
from player_car import PlayerCar
from attacker_ai import AttackerAI
from defender_ai import DefenderAI

# --- AI Modules ---
from ai import AStar, PositionPredictor, FSM, DefenseState

# --- Rendering ---
from rendering import (draw_menu, draw_game_over, draw_grid, draw_obstacles,
                      draw_player_car, draw_attacker_ai, draw_defender_ai,
                      draw_path, draw_prediction, draw_tracking_laser, draw_debug_info)

# --- Game States ---
class GameState(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

def setup_game(mode: str) -> dict:
    """Initializes all game objects based on the selected mode."""
    game_objects = {}

    # --- AI Component Initialization (Common) ---
    pathfinder = AStar() # Used by AttackerAI, potentially usable by DefenderAI if needed
    predictor = PositionPredictor() # Used for visualizing player movement prediction

    # --- Create Cars based on Mode ---
    if mode == "hider": # Player is Hider (Blue), AI is Attacker (Red)
        player = PlayerCar(SCREEN_WIDTH // 4, SCREEN_HEIGHT * 3 // 4, role="hider")
        ai_car = AttackerAI(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 4, pathfinder)
        ai_car.set_target(player) # Attacker targets the player
        game_objects['player'] = player
        game_objects['ai'] = ai_car
        game_objects['chaser'] = ai_car # Reference for laser/game over logic
        game_objects['hider'] = player
    elif mode == "chaser": # Player is Chaser (Red), AI is Defender (Blue)
        player = PlayerCar(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2, role="chaser")
        ai_car = DefenderAI(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 2)
        ai_car.set_target(player) # Defender reacts to the player
        # Optionally set patrol points for Defender
        patrol_pts = generate_patrol_points() # Generate some points
        if patrol_pts: # Check if points were generated
             ai_car.set_patrol_points(patrol_pts)
        game_objects['player'] = player
        game_objects['ai'] = ai_car
        game_objects['chaser'] = player # Reference for laser/game over logic
        game_objects['hider'] = ai_car
    else:
        raise ValueError(f"Invalid game mode: {mode}")

    # --- Generate Obstacles ---
    # Ensure obstacles avoid initial positions of both cars
    cars_to_avoid = [game_objects['player'], game_objects['ai']]
    obstacles = generate_obstacles(cars_to_avoid=cars_to_avoid, num_obstacles=NUM_OBSTACLES)
    game_objects['obstacles'] = obstacles

    # --- Update Pathfinder Grid ---
    # Critical for AttackerAI, do it once after obstacles are generated
    pathfinder.update_obstacles(obstacles)
    game_objects['pathfinder'] = pathfinder # Store if needed elsewhere

    # --- Initialize Game State Variables ---
    game_objects['predictor'] = predictor
    game_objects['predicted_path'] = []
    game_objects['los_start_time'] = None # For timed game over in Hider mode

    # --- Display Toggles ---
    game_objects['show_grid'] = False
    game_objects['show_debug'] = True
    game_objects['show_predictions'] = True
    game_objects['show_laser'] = True
    game_objects['show_ai_path'] = True # Toggle for AttackerAI path specifically

    game_objects['game_mode'] = mode # Store the mode

    return game_objects


# Example patrol point generation (can be moved to utils or constants if complex)
def generate_patrol_points(num_points=4, margin=150):
    """Generate random patrol points, e.g., for DefenderAI."""
    points = []
    center_x, center_y = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2
    # Ensure radii are positive
    radius_x = max(10, (SCREEN_WIDTH - 2 * margin) / 2)
    radius_y = max(10, (SCREEN_HEIGHT - 2 * margin) / 2)
    if radius_x <= 0 or radius_y <= 0:
         print("Warning: Cannot generate patrol points with current margin/screen size.")
         return [] # Return empty list if radius is non-positive

    for i in range(num_points):
        angle = random.uniform(0, 360) # Random angles
        # Slightly randomize radius as well
        r_x = radius_x * random.uniform(0.7, 1.0)
        r_y = radius_y * random.uniform(0.7, 1.0)
        x = center_x + r_x * math.cos(math.radians(angle))
        y = center_y + r_y * math.sin(math.radians(angle))
        # Ensure points are within screen bounds (clamp)
        x = max(margin, min(x, SCREEN_WIDTH - margin))
        y = max(margin, min(y, SCREEN_HEIGHT - margin))
        points.append((x, y))
    return points


def game_loop(screen: pygame.Surface, clock: pygame.time.Clock, game_objects: dict) -> str:
    """Runs the main game simulation for one round."""
    running_this_game = True
    winner = None # Track who won ("hider" or "chaser")

    # Extract objects for easier access
    player: PlayerCar = game_objects['player']
    ai_car = game_objects['ai'] # Could be AttackerAI or DefenderAI
    obstacles: list[Obstacle] = game_objects['obstacles']
    predictor: PositionPredictor = game_objects['predictor']
    game_mode: str = game_objects['game_mode']
    chaser = game_objects['chaser'] # Whoever is doing the chasing
    hider = game_objects['hider']   # Whoever is hiding/evading

    # Retrieve display toggles (use get with default False if needed)
    show_grid = game_objects.get('show_grid', False)
    show_debug = game_objects.get('show_debug', True)
    show_predictions = game_objects.get('show_predictions', True)
    show_laser = game_objects.get('show_laser', True)
    show_ai_path = game_objects.get('show_ai_path', True)

    # LOS timer variables (relevant when player is hider)
    los_start_time = game_objects.get('los_start_time') # Get initial value (likely None)


    while running_this_game:
        # --- Error Catching Wrapper for Frame ---
        # Wrap the core logic of a single frame update in a try-except
        # to catch errors and report them without necessarily crashing the outer loop.
        try:
            current_ticks = pygame.time.get_ticks() # Get current time for timers

            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit" # Signal to exit application
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Option 1: Go back to menu
                        # return "menu" # This would need handling in the outer loop
                        # Option 2: Quit application entirely
                        return "quit"
                    # Toggles (only active during gameplay)
                    if event.key == pygame.K_g: show_grid = not show_grid
                    if event.key == pygame.K_d: show_debug = not show_debug
                    if event.key == pygame.K_p: show_predictions = not show_predictions
                    if event.key == pygame.K_l: show_laser = not show_laser
                    if event.key == pygame.K_t: show_ai_path = not show_ai_path

            # --- Input ---
            keys = pygame.key.get_pressed()

            # --- Updates ---
            # Update Player (with specific try-except)
            try:
                player.update(keys, obstacles)
            except Exception as e:
                print(f"\n--- ERROR DURING PLAYER UPDATE ---")
                print(f"Error: {e}")
                traceback.print_exc()
                print(f"---------------------------------")
                return "menu" # Return to menu on error

            # Update AI (Attacker or Defender) (with specific try-except)
            try:
                ai_car.update(obstacles)
            except Exception as e:
                print(f"\n--- ERROR DURING AI UPDATE ({type(ai_car).__name__}) ---")
                print(f"Error: {e}")
                traceback.print_exc()
                print(f"---------------------------------")
                return "menu" # Return to menu on error


            # Update Prediction Data
            try:
                hider_pos = hider.get_position()
                hider_vel = hider.get_velocity()
                predictor.add_observation(hider_pos, hider_vel, current_ticks / 1000.0)
                predicted_path = []
                if show_predictions:
                    if hider_vel[0] != 0 or hider_vel[1] != 0:
                         predicted_path = predictor.predict_future_path(hider_pos, hider_vel)
            except Exception as e:
                print(f"\n--- ERROR DURING PREDICTION UPDATE ---")
                print(f"Error: {e}")
                traceback.print_exc()
                print(f"-------------------------------------")
                return "menu" # Return to menu on error


            # --- Game Over Checks ---
            chaser_pos = chaser.get_position()
            hider_pos = hider.get_position() # Re-get in case positions updated

            if game_mode == "hider": # Player is Hider, AI is Chaser (AttackerAI)
                los_blocked = check_line_of_sight(chaser_pos, hider_pos, obstacles)
                dist_ch_hi = distance(chaser_pos[0], chaser_pos[1], hider_pos[0], hider_pos[1])
                max_laser_dist = math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT)

                if not los_blocked and dist_ch_hi <= max_laser_dist:
                    if los_start_time is None:
                        los_start_time = current_ticks
                    else:
                        duration = current_ticks - los_start_time
                        if duration >= LOS_TIMER_DURATION:
                            print(f"CAUGHT! LOS held for {duration}ms.")
                            winner = "chaser"
                            running_this_game = False
                else:
                    los_start_time = None

            elif game_mode == "chaser": # Player is Chaser, AI is Hider (DefenderAI)
                catch_distance = (player.width + ai_car.width) / 2.0 * 0.8
                dist_ch_hi = distance(chaser_pos[0], chaser_pos[1], hider_pos[0], hider_pos[1])

                if dist_ch_hi <= catch_distance:
                    print(f"CAUGHT! Player caught AI at distance {dist_ch_hi:.1f}.")
                    winner = "chaser"
                    running_this_game = False

            # --- Rendering ---
            screen.fill(BLACK)
            if show_grid: draw_grid(screen)

            if show_predictions and predicted_path:
                draw_prediction(screen, predicted_path)

            if isinstance(ai_car, AttackerAI) and show_ai_path:
                 draw_path(screen, ai_car.path, color=ATTACKER_PATH_COLOR)
                 if ai_car.current_waypoint:
                     try:
                        wp_int = (int(ai_car.current_waypoint[0]), int(ai_car.current_waypoint[1]))
                        pygame.draw.circle(screen, WHITE, wp_int, 5, 1)
                     except (TypeError, ValueError): pass

            draw_obstacles(screen, obstacles)

            if isinstance(ai_car, AttackerAI):
                 draw_attacker_ai(screen, ai_car, show_path=False)
            elif isinstance(ai_car, DefenderAI):
                 draw_defender_ai(screen, ai_car)
            draw_player_car(screen, player)

            if show_laser:
                 laser_max_len = math.hypot(SCREEN_WIDTH, SCREEN_HEIGHT) * LASER_MAX_LENGTH_FACTOR
                 draw_tracking_laser(screen, chaser, hider, laser_max_len, obstacles)

            if show_debug:
                los_info = None
                if game_mode == "hider":
                     los_info = (los_start_time, LOS_TIMER_DURATION)
                draw_debug_info(screen, clock, game_mode, ai_car, los_info)

            pygame.display.flip()
            clock.tick(FPS)

        # --- Exception Handling for the Frame ---
        except Exception as e:
            print(f"\n--- ERROR DURING GAME FRAME ---")
            print(f"Error: {e}")
            traceback.print_exc() # Print detailed traceback
            print(f"------------------------------------")
            # Decide recovery: Quit or go back to menu? Returning to menu is safer.
            return "menu" # Returning "menu" signals the outer loop to reset

        # End of game loop iteration (while running_this_game)

    # --- After game loop ends (normally or via winner) ---
    if winner:
        return winner # "chaser" or "hider"
    else:
        # If loop exited potentially without a winner (e.g., ESC pressed inside loop)
        # The explicit 'return "quit"' for ESC is now handled inside the loop's event handling
        # If we somehow exit the loop without running_this_game = False (shouldn't happen),
        # default to quit.
        return "quit"


def game_over_loop(screen: pygame.Surface, clock: pygame.time.Clock, winner: str) -> str:
    """Displays the game over screen and waits for user action."""
    while True:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return "quit"
                if event.key == pygame.K_SPACE:
                    return "restart" # Signal to go back to menu
                if event.key == pygame.K_ESCAPE: # Allow ESC to quit from game over too
                     return "quit"

        # Drawing
        screen.fill(BLACK) # Clear screen
        draw_game_over(screen, winner)
        pygame.display.flip()
        clock.tick(FPS) # Keep ticking


def menu_loop(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
     """Displays the main menu and handles selection."""
     selected_option = 0
     options = ["hider", "chaser", "quit_app"] # Corresponds to rendering order

     while True:
          # Event Handling
          for event in pygame.event.get():
               if event.type == pygame.QUIT:
                    return "quit_app"
               if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                         return "quit_app"
                    if event.key == pygame.K_UP:
                         selected_option = (selected_option - 1) % len(options)
                    if event.key == pygame.K_DOWN:
                         selected_option = (selected_option + 1) % len(options)
                    if event.key == pygame.K_RETURN:
                         return options[selected_option] # Return "hider", "chaser", or "quit_app"

          # Drawing
          # Pass the index of the selected option for highlighting
          draw_menu(screen, selected_option)
          pygame.display.flip()
          clock.tick(FPS)


# --- Main Application Execution ---
def main():
    pygame.init()
    # Error handling for display initialization
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    except pygame.error as e:
        print(f"Error initializing display: {e}")
        sys.exit(1)

    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    current_state = GameState.MENU
    running = True
    game_objects = {}
    winner = None

    while running:
        if current_state == GameState.MENU:
            menu_result = menu_loop(screen, clock)
            if menu_result == "quit_app":
                running = False
            else:
                try:
                    print(f"Setting up game mode: Player is {menu_result.upper()}")
                    game_objects = setup_game(menu_result)
                    current_state = GameState.PLAYING
                except Exception as e:
                    print(f"Error setting up game: {e}")
                    traceback.print_exc() # Print setup error details
                    current_state = GameState.MENU # Go back to menu on setup error


        elif current_state == GameState.PLAYING:
            # Outer try-except remains, but inner one in game_loop provides more detail first
            try:
                game_result = game_loop(screen, clock, game_objects) # Returns winner, "menu", or "quit"

                if game_result == "quit":
                    running = False
                elif game_result == "menu": # If game loop explicitly returned "menu" due to error
                    current_state = GameState.MENU
                    winner = None
                    game_objects = {}
                else: # Game ended normally with a winner
                    winner = game_result # Store winner ("hider" or "chaser")
                    current_state = GameState.GAME_OVER
                    # pygame.time.wait(500) # Optional delay
            except Exception as e:
                 # This outer catch handles unexpected errors *not* caught within game_loop's frame catch
                 print(f"\n--- UNHANDLED Runtime Error in Game ---")
                 print(f"Error: {e}")
                 traceback.print_exc()
                 print(f"------------------------------------")
                 current_state = GameState.MENU # Fallback to menu
                 print("Returning to menu due to unhandled error.")


        elif current_state == GameState.GAME_OVER:
            game_over_result = game_over_loop(screen, clock, winner) # Returns "restart" or "quit"
            if game_over_result == "quit":
                running = False
            elif game_over_result == "restart":
                current_state = GameState.MENU # Go back to menu
                winner = None
                game_objects = {} # Clear old game objects

    pygame.quit()
    print("Game exited cleanly.")
    sys.exit()


if __name__ == "__main__":
    main()
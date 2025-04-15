import pygame
import sys
import random
import time
import math
from constants import *
from attackercar import AttackerCar, Obstacle, generate_obstacles
from hidingcar import HidingCar
from rendering import (draw_attacker_car, draw_hiding_car, draw_obstacles, # Updated drawing functions
                      draw_path, draw_prediction, draw_debug_info, draw_grid, # draw_debug_info is now used
                      draw_tracking_laser)
# Keep utils, A*, predictor
from utils import distance, check_line_of_sight
from ai.pathfinding import AStar
from ai.prediction import PositionPredictor

# Function to encapsulate the main game logic for restarting
def game_loop(screen, clock):
    # --- Create Cars (Roles Swapped) ---
    player_hider = HidingCar(SCREEN_WIDTH // 4, SCREEN_HEIGHT * 3 // 4)
    attacker = AttackerCar(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 4)

    obstacles = generate_obstacles(15, player_hider, attacker) # Pass both cars

    # --- Initialize AI components for Attacker ---
    pathfinder = AStar()
    pathfinder.update_obstacles(obstacles)
    predictor = PositionPredictor()

    # --- AI Variables ---
    attacker_path = []
    path_update_counter = 0
    attacker_current_waypoint = None

    # --- Display Toggles ---
    show_grid = False
    show_debug = True
    show_predictions = True # Predict player's future path
    show_laser = True
    show_attacker_path = True # Toggle for attacker's A* path

    laser_length = math.sqrt(SCREEN_WIDTH**2 + SCREEN_HEIGHT**2) # Full diagonal for laser check

    # --- Game State Variables ---
    running_this_game = True # Controls the loop for this specific game instance
    game_over = False
    game_over_timer = 0
    GAME_OVER_DISPLAY_TIME = 2000 # ms - Reduced slightly for responsiveness
    RESTART_DELAY = 500 # ms - Brief delay before showing restart text

    # --- LOS Timer Variables ---
    los_start_time = None # Time when continuous LOS began
    LOS_TIMER_DURATION = 1500 # 1.5 seconds in milliseconds

    # --- Main Game Loop for this instance ---
    while running_this_game:
        current_time = pygame.time.get_ticks()

        # --- Event Processing ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT" # Signal to exit the outer loop
            elif event.type == pygame.KEYDOWN:
                 if event.key == pygame.K_ESCAPE:
                      return "QUIT" # Signal to exit

                 if game_over:
                     # Check if enough time has passed to show restart prompt
                     if current_time - game_over_timer > GAME_OVER_DISPLAY_TIME + RESTART_DELAY:
                         if event.key == pygame.K_SPACE:
                             return "RESTART" # Signal to restart
                         elif event.key == pygame.K_q: # Add a quit option on game over screen
                             return "QUIT"
                 else: # Only process game toggles if game is not over
                    if event.key == pygame.K_g: show_grid = not show_grid
                    if event.key == pygame.K_d: show_debug = not show_debug
                    if event.key == pygame.K_p: show_predictions = not show_predictions
                    if event.key == pygame.K_l: show_laser = not show_laser
                    if event.key == pygame.K_t: show_attacker_path = not show_attacker_path # Toggle attacker path

        if game_over:
            # --- Game Over Screen ---
            screen.fill(BLACK)
            font_large = pygame.font.SysFont(None, 72)
            text = font_large.render("CAUGHT!", True, RED)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30))
            screen.blit(text, text_rect)

            # Show restart/quit prompt after delay
            if current_time - game_over_timer > GAME_OVER_DISPLAY_TIME + RESTART_DELAY:
                 font_small = pygame.font.SysFont(None, 36)
                 restart_text = font_small.render("Press SPACE to Restart or Q to Quit", True, WHITE)
                 restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 40))
                 screen.blit(restart_text, restart_rect)

            pygame.display.flip()
            clock.tick(FPS)
            continue # Skip rest of the game loop until restart/quit

        # --- Input and Updates ---
        keys = pygame.key.get_pressed()
        player_hider.update_player(keys, obstacles)
        player_pos = player_hider.get_position()

        # Predict player movement
        predictor.add_observation(player_pos, (player_hider.vx, player_hider.vy), current_time / 1000.0)
        predicted_path = []
        if show_predictions:
            predicted_path = predictor.predict_future_path(player_pos, (player_hider.vx, player_hider.vy))

        # --- Update Attacker AI ---
        attacker_pos = attacker.get_position()
        path_update_counter += 1
        if path_update_counter >= PATHFINDING_UPDATE_RATE or not attacker_path:
            path_update_counter = 0
            pathfinder.update_obstacles(obstacles)
            attacker_path = pathfinder.find_path(attacker_pos, player_pos)
            if attacker_path:
                attacker_current_waypoint = attacker_path[0]
            else:
                attacker_current_waypoint = player_pos
                attacker_path = []

        # Follow Path / Target
        if attacker_path and attacker_current_waypoint:
            dist_to_waypoint = distance(attacker_pos[0], attacker_pos[1], attacker_current_waypoint[0], attacker_current_waypoint[1])
            if dist_to_waypoint < 20:
                attacker_path.pop(0)
                if attacker_path:
                    attacker_current_waypoint = attacker_path[0]
                else:
                    attacker_current_waypoint = player_pos
        elif not attacker_path:
             attacker_current_waypoint = player_pos

        # Move Attacker
        if attacker_current_waypoint:
            attacker.move_to_target(attacker_current_waypoint, obstacles)
        attacker.update_physics(obstacles)

        # --- Check Game Over Condition (Timed LOS) ---
        los_blocked = True # Assume blocked initially
        dist_att_plr = distance(attacker_pos[0], attacker_pos[1], player_pos[0], player_pos[1])

        if dist_att_plr <= laser_length: # Only check LOS if within max laser range
            los_blocked = check_line_of_sight(attacker_pos, player_pos, obstacles)

        if not los_blocked:
            # Player is in Line of Sight
            if los_start_time is None:
                # LOS just started
                los_start_time = current_time
                print(f"LOS Detected at {los_start_time}") # Debug
            else:
                # LOS is continuous, check duration
                duration = current_time - los_start_time
                # print(f"LOS Duration: {duration} ms") # Debug
                if duration >= LOS_TIMER_DURATION:
                    print(f"GAME OVER - Caught after {duration}ms LOS!")
                    game_over = True
                    game_over_timer = current_time # Record time of actual game over
                    los_start_time = None # Reset timer state
        else:
            # Player is NOT in Line of Sight (or out of range)
            if los_start_time is not None:
                 print(f"LOS Lost at {current_time}") # Debug
            los_start_time = None # Reset timer if LOS is broken

        # --- Rendering ---
        screen.fill(BLACK)
        if show_grid: draw_grid(screen)

        # Draw Paths
        if show_attacker_path and attacker_path:
            draw_path(screen, attacker_path, color=(255, 100, 100))
        if show_predictions and predicted_path:
            draw_prediction(screen, predicted_path, color=(50, 50, 200))

        draw_obstacles(screen, obstacles)

        # Draw Cars
        draw_attacker_car(screen, attacker)
        draw_hiding_car(screen, player_hider)

        if show_laser:
            draw_tracking_laser(screen, attacker, player_hider, laser_length, obstacles)

        # Draw Debug Info
        if show_debug:
            fps = clock.get_fps()
            draw_debug_info(screen, fps, attacker_current_waypoint)
            if los_start_time is not None:
                 timer_font = pygame.font.SysFont(None, 24)
                 los_duration = (current_time - los_start_time) / 1000.0
                 timer_text = f"LOS Timer: {los_duration:.1f}s / {LOS_TIMER_DURATION/1000.0:.1f}s"
                 timer_color = WHITE if los_duration < LOS_TIMER_DURATION else RED
                 timer_surface = timer_font.render(timer_text, True, timer_color)
                 screen.blit(timer_surface, (10, 70)) # Adjust position as needed

        pygame.display.flip()
        clock.tick(FPS)

    return "QUIT"

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE + " - You are the Blue Car (Hide!)")
    clock = pygame.time.Clock()

    while True: # Outer loop for restarting
        game_result = game_loop(screen, clock) # Run the game instance

        if game_result == "QUIT":
            break # Exit the outer loop
        elif game_result == "RESTART":
            print("Restarting game...")
            continue # Go to the next iteration of the outer loop

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
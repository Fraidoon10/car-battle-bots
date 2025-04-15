import pygame
import sys
import random
import time
import math
from constants import *
from entities import PlayerCar, generate_obstacles
from defensive_car import DefenseCar
from rendering import (draw_player_car, draw_defense_car, draw_obstacles,
                      draw_path, draw_prediction, draw_debug_info, draw_grid,
                      draw_tracking_laser)
from utils import distance
from ai.fsm import FSM, DefenseState
from ai.pathfinding import AStar
from ai.prediction import PositionPredictor

def generate_patrol_points():
    """Generate random patrol points for the defensive car."""
    points = []
    margin = 100  # Margin from screen edges

    # Generate points forming a circuit
    num_points = 4
    for i in range(num_points):
        angle = i * (360 / num_points)
        radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) / 3

        x = SCREEN_WIDTH / 2 + radius * math.cos(math.radians(angle))
        y = SCREEN_HEIGHT / 2 + radius * math.sin(math.radians(angle))

        # Ensure points are within screen
        x = max(margin, min(x, SCREEN_WIDTH - margin))
        y = max(margin, min(y, SCREEN_HEIGHT - margin))

        points.append((x, y))

    return points

def main():
    # Initialize pygame
    pygame.init()

    # Create the screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)

    # Create clock for controlling FPS
    clock = pygame.time.Clock()

    # Create player car
    player = PlayerCar(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)

    # Create defensive car
    defense = DefenseCar(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 2)

    # Generate obstacles
    obstacles = generate_obstacles(15, player, defense)

    # Initialize AI components
    fsm = FSM()
    fsm.set_patrol_points(generate_patrol_points())

    pathfinder = AStar()
    pathfinder.update_obstacles(obstacles)

    predictor = PositionPredictor()

    # Initialize variables for AI processing
    path = []
    predicted_path = []
    current_target = None
    path_update_counter = 0

    # Toggle flags for display options
    show_grid = False
    show_debug = True
    show_predictions = True
    show_laser = True  # Flag for laser tracking

    # Calculate laser length (half the screen diagonal) - dynamic length
    laser_length = math.sqrt(SCREEN_WIDTH**2 + SCREEN_HEIGHT**2) / 2

    # Game loop
    running = True
    while running:
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:  # Toggle grid
                    show_grid = not show_grid
                elif event.key == pygame.K_d:  # Toggle debug info
                    show_debug = not show_debug
                elif event.key == pygame.K_p:  # Toggle predictions
                    show_predictions = not show_predictions
                elif event.key == pygame.K_l:  # Toggle laser
                    show_laser = not show_laser
                # Removed 'O' toggle as laser obstacle check is always on when obstacles are passed

        # Get keyboard input
        keys = pygame.key.get_pressed()

        # Update player car with obstacle collision detection
        player.update(keys, obstacles)

        # Get positions and velocities
        player_pos = player.get_position()
        player_vel = player.get_velocity()
        defense_pos = defense.get_position()

        # Add player position observation for prediction
        predictor.add_observation(player_pos, player_vel, pygame.time.get_ticks() / 1000.0)

        # Update FSM to get target position
        target_pos = fsm.update(defense, player, obstacles, SCREEN_WIDTH, SCREEN_HEIGHT)

        # If we need to update pathfinding
        path_update_counter += 1
        if path_update_counter >= PATHFINDING_UPDATE_RATE or not path:
            path_update_counter = 0

            if target_pos:
                # Update pathfinder obstacle grid
                pathfinder.update_obstacles(obstacles)

                # Find path to target
                path = pathfinder.find_path(defense_pos, target_pos)

                # If path exists, set first waypoint as current target
                if path:
                    current_target = path[0]
                else:
                    # If no path found, still try to move towards the raw target
                    current_target = target_pos
            else:
                path = []
                current_target = None

        # If we have a path, follow it
        if path and len(path) > 0:
            # Check if we've reached the current waypoint
            if distance(defense_pos[0], defense_pos[1], path[0][0], path[0][1]) < 20:
                # Move to next waypoint
                path.pop(0)
                if path:
                    current_target = path[0]
                # If path is now empty, the target might be the final FSM target
                elif target_pos:
                    current_target = target_pos


        # Move defensive car towards target
        defense.move_to_target(current_target, obstacles)
        # Update defensive car based on calculated velocity and collisions
        defense.update(obstacles)

        # Generate prediction of player's future path
        if show_predictions:
            predicted_path = predictor.predict_future_path(player_pos, player_vel)

        # Clear the screen
        screen.fill(BLACK)

        # Draw grid if enabled
        if show_grid:
            draw_grid(screen)

        # Draw path if exists
        if path:
            draw_path(screen, path)

        # Draw predicted path if enabled
        if show_predictions and predicted_path:
            draw_prediction(screen, predicted_path)

        # Draw obstacles
        draw_obstacles(screen, obstacles)

        # Draw cars and laser
        draw_player_car(screen, player) # Draw player car

        if show_laser:
            # Draw laser with obstacle checking (obstacles always passed)
            draw_tracking_laser(screen, player, defense, laser_length, obstacles)

        draw_defense_car(screen, defense, fsm) # Draw defense car

        # Draw debug info if enabled
        if show_debug:
            fps = clock.get_fps()
            draw_debug_info(screen, defense, fsm.current_state, fps)

        # Update display
        pygame.display.flip()

        # Control the frame rate
        clock.tick(FPS)

    # Quit pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
import pygame
import math
from constants import *
from ai.fsm import DefenseState

def draw_player_car(screen, car): # Removed unused target_car and laser_length params
    """Draw the player-controlled car."""
    # Draw the car body
    pygame.draw.rect(screen, car.color, car.rect)

    # Draw direction indicator (a small line showing which way the car is moving)
    if car.vx != 0 or car.vy != 0:
        # Starting point at the center of the car
        start_x = car.x + car.width // 2
        start_y = car.y + car.height // 2

        # End point in the direction of movement
        scale = 20  # Length of the indicator line
        end_x = start_x + car.vx * scale // car.speed if car.speed != 0 else start_x
        end_y = start_y + car.vy * scale // car.speed if car.speed != 0 else start_y

        pygame.draw.line(screen, (255, 255, 255), (start_x, start_y), (end_x, end_y), 2)

    # Removed redundant laser drawing block, as it's called separately

def draw_tracking_laser(screen, source_car, target_car, max_length, obstacles=None):
    """Draw a tracking laser from source car to target car with obstacle checking."""
    # Get the center positions of both cars
    source_x = source_car.x + source_car.width // 2
    source_y = source_car.y - 5  # Position laser slightly above the car

    target_x = target_car.x + target_car.width // 2
    target_y = target_car.y + target_car.height // 2

    # Calculate direction vector
    dx = target_x - source_x
    dy = target_y - source_y

    # Calculate distance
    dist_to_target = math.sqrt(dx * dx + dy * dy)

    # Normalize direction vector
    if dist_to_target > 0:
        dx /= dist_to_target
        dy /= dist_to_target

    # Calculate potential laser end point (limited by max_length)
    effective_laser_length = min(dist_to_target, max_length)
    laser_end_x = source_x + dx * effective_laser_length
    laser_end_y = source_y + dy * effective_laser_length

    # Check for obstacles in the laser path if provided
    hit_obstacle = False
    hit_point = (laser_end_x, laser_end_y)
    collision_distance = effective_laser_length # Start with the full possible length

    if obstacles:
        # Ray casting algorithm to find first collision
        step_size = 5  # Check every 5 pixels along the ray
        current_dist = 0

        while current_dist < effective_laser_length:
            # Calculate current point along the ray
            current_x = source_x + dx * current_dist
            current_y = source_y + dy * current_dist

            # Create a small rect for collision checking
            check_rect = pygame.Rect(current_x - 2, current_y - 2, 4, 4)

            # Check if hitting any obstacle
            for obstacle in obstacles:
                if obstacle.rect.colliderect(check_rect):
                    hit_obstacle = True
                    hit_point = (current_x, current_y)
                    collision_distance = current_dist # Record distance where collision happened
                    break

            if hit_obstacle:
                break

            current_dist += step_size

    # Use hit point or original end point based on collision check
    final_laser_end_x, final_laser_end_y = hit_point

    # Draw the laser (red beam with yellow core)
    pygame.draw.line(screen, LASER_RED, (source_x, source_y),
                    (final_laser_end_x, final_laser_end_y), 5)  # Outer red glow
    pygame.draw.line(screen, LASER_CORE, (source_x, source_y),
                    (final_laser_end_x, final_laser_end_y), 2)  # Inner yellow core

    # Draw a small targeting reticle at the end of the laser
    pygame.draw.circle(screen, LASER_RED, (int(final_laser_end_x), int(final_laser_end_y)), 4, 1)
    pygame.draw.line(screen, LASER_RED,
                    (final_laser_end_x - 4, final_laser_end_y),
                    (final_laser_end_x + 4, final_laser_end_y), 1)
    pygame.draw.line(screen, LASER_RED,
                    (final_laser_end_x, final_laser_end_y - 4),
                    (final_laser_end_x, final_laser_end_y + 4), 1)

    # If laser hits the target (meaning no obstacle collision happened *before* reaching the target)
    if not hit_obstacle and dist_to_target <= max_length:
        pygame.draw.circle(screen, (255, 200, 50),
                          (int(target_x), int(target_y)), 10, 2)


def draw_defense_car(screen, car, fsm=None):
    """Draw the AI-controlled defensive car with state indicator and hide target."""
    pygame.draw.rect(screen, car.color, car.rect)

    # Draw car center point
    center_x = car.x + car.width // 2
    center_y = car.y + car.height // 2
    pygame.draw.circle(screen, (255, 255, 0), (int(center_x), int(center_y)), 3)

    # Draw velocity vector
    if hasattr(car, 'vx') and hasattr(car, 'vy'):
        if car.vx != 0 or car.vy != 0:
            scale = 20
            end_x = center_x + car.vx * scale
            end_y = center_y + car.vy * scale
            pygame.draw.line(screen, (255, 255, 0), (center_x, center_y), (end_x, end_y), 2)

    # Draw state indicator if FSM is available
    if fsm:
        # Use the name for the dictionary key, which is safer if the enum value changes
        state_name = fsm.current_state.name
        indicator_color = {
            'IDLE': (200, 200, 200),
            'EVADE': (255, 100, 100),
            'PATROL': (100, 255, 100),
            'HIDE': (150, 50, 255), # Color for HIDE
            'RETURN_TO_SAFE_AREA': (255, 255, 0)
        }.get(state_name, (200, 200, 200)) # Use get for fallback

        pygame.draw.circle(screen, indicator_color, (int(car.x), int(car.y)), 5)

        # Draw the current hide target if in HIDE state and target exists
        # Now DefenseState is defined
        if fsm.current_state == DefenseState.HIDE and fsm.current_hide_target:
            tgt_x, tgt_y = fsm.current_hide_target
            pygame.draw.circle(screen, HIDE_TARGET_COLOR, (int(tgt_x), int(tgt_y)), 6)
            pygame.draw.line(screen, WHITE, (center_x, center_y), (int(tgt_x), int(tgt_y)), 1)

def draw_obstacles(screen, obstacles):
    """Draw all obstacles."""
    for obstacle in obstacles:
        pygame.draw.rect(screen, obstacle.color, obstacle.rect)

def draw_path(screen, path, color=(50, 200, 50), dot_size=3):
    """Draw a path as a series of dots."""
    if not path:
        return

    for point in path:
        pygame.draw.circle(screen, color, (int(point[0]), int(point[1])), dot_size)

    # Connect dots with lines
    if len(path) > 1:
        pygame.draw.lines(screen, color, False,
                          [(int(p[0]), int(p[1])) for p in path], 1)

def draw_prediction(screen, points, color=(200, 50, 50), dot_size=2):
    """Draw a predicted path."""
    draw_path(screen, points, color, dot_size)

def draw_debug_info(screen, defense_car, fsm_state, fps):
    """Draw debug information."""
    font = pygame.font.SysFont(None, 24)

    # Draw state
    state_text = f"State: {fsm_state.name}"
    state_surface = font.render(state_text, True, (255, 255, 255))
    screen.blit(state_surface, (10, 10))

    # Draw FPS
    fps_text = f"FPS: {fps:.1f}"
    fps_surface = font.render(fps_text, True, (255, 255, 255))
    screen.blit(fps_surface, (10, 40))

    # Draw position
    pos_text = f"Pos: ({int(defense_car.x)}, {int(defense_car.y)})"
    pos_surface = font.render(pos_text, True, (255, 255, 255))
    screen.blit(pos_surface, (10, 70))

def draw_grid(screen):
    """Draw a grid for debugging pathfinding."""
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, (20, 20, 20), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, (20, 20, 20), (0, y), (SCREEN_WIDTH, y))
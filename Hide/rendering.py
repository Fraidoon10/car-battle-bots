import pygame
import math
from constants import *

def draw_attacker_car(screen, car):
    """Draw the AI-controlled attacking car."""
    pygame.draw.rect(screen, car.color, car.rect)
    if car.vx != 0 or car.vy != 0:
        center_x = car.x + car.width // 2
        center_y = car.y + car.height // 2
        end_x = center_x + car.vx * 5 # Shorter scale for velocity viz
        end_y = center_y + car.vy * 5
        pygame.draw.line(screen, (255, 255, 0), (center_x, center_y), (end_x, end_y), 2)

def draw_hiding_car(screen, car):
    """Draw the player-controlled hiding car."""
    pygame.draw.rect(screen, car.color, car.rect)
    if car.vx != 0 or car.vy != 0:
        start_x = car.x + car.width // 2
        start_y = car.y + car.height // 2
        # Normalize display vector if needed, or just use raw vx/vy scaled
        norm_vx, norm_vy = car.vx, car.vy
        mag = math.sqrt(norm_vx**2 + norm_vy**2)
        if mag > 0:
             norm_vx /= mag
             norm_vy /= mag
        scale = 15 # Length of the indicator line
        end_x = start_x + norm_vx * scale
        end_y = start_y + norm_vy * scale
        pygame.draw.line(screen, WHITE, (start_x, start_y), (int(end_x), int(end_y)), 2)

# --- Laser function remains the same, but called with different args in main ---
def draw_tracking_laser(screen, source_car, target_car, max_length, obstacles=None):
    """Draw a tracking laser from source car to target car with obstacle checking."""
    source_x = source_car.x + source_car.width // 2
    # Adjust laser origin position if desired (e.g., front of car)
    source_y = source_car.y + source_car.height // 4 # Example: slightly forward

    target_x = target_car.x + target_car.width // 2
    target_y = target_car.y + target_car.height // 2

    dx = target_x - source_x
    dy = target_y - source_y
    dist_to_target = math.sqrt(dx * dx + dy * dy)

    if dist_to_target > 0:
        dx /= dist_to_target
        dy /= dist_to_target

    effective_laser_length = min(dist_to_target, max_length)
    laser_end_x = source_x + dx * effective_laser_length
    laser_end_y = source_y + dy * effective_laser_length

    hit_obstacle = False
    hit_point = (laser_end_x, laser_end_y)
    collision_distance = effective_laser_length

    if obstacles:
        step_size = 5
        current_dist = step_size
        while current_dist < effective_laser_length:
            current_x = source_x + dx * current_dist
            current_y = source_y + dy * current_dist
            check_rect = pygame.Rect(current_x - 1, current_y - 1, 3, 3) # Smaller check rect
            for obstacle in obstacles:
                if obstacle.rect.colliderect(check_rect):
                    hit_obstacle = True
                    hit_point = (current_x, current_y)
                    collision_distance = current_dist
                    break
            if hit_obstacle: break
            current_dist += step_size

    final_laser_end_x, final_laser_end_y = hit_point

    # Draw laser (Red beam)
    pygame.draw.line(screen, LASER_RED, (source_x, source_y), (final_laser_end_x, final_laser_end_y), 3)
    # Draw core (Yellow)
    pygame.draw.line(screen, LASER_CORE, (source_x, source_y), (final_laser_end_x, final_laser_end_y), 1)

    # Reticle at end
    pygame.draw.circle(screen, LASER_RED, (int(final_laser_end_x), int(final_laser_end_y)), 4, 1)

    # Target hit effect (if LOS clear and reaches target)
    if not hit_obstacle and dist_to_target <= max_length:
         pygame.draw.circle(screen, (255, 200, 50, 150), # Semi-transparent yellow circle on target
                           (int(target_x), int(target_y)), int(target_car.width * 0.7), 2)


# --- Other drawing functions (obstacles, path, prediction, debug, grid) remain largely the same ---
def draw_obstacles(screen, obstacles):
    for obstacle in obstacles:
        pygame.draw.rect(screen, obstacle.color, obstacle.rect)

def draw_path(screen, path, color=(50, 200, 50), dot_size=3):
    if not path: return
    points_int = [(int(p[0]), int(p[1])) for p in path]
    if len(points_int) > 1:
        pygame.draw.lines(screen, color, False, points_int, 1)
    for point in points_int:
        pygame.draw.circle(screen, color, point, dot_size)

def draw_prediction(screen, points, color=(200, 50, 50), dot_size=2):
    draw_path(screen, points, color, dot_size) # Use the same logic

def draw_debug_info(screen, fps, attacker_target_waypoint):
    """Draws debug information like FPS and attacker target."""
    font = pygame.font.SysFont(None, 24)
    y_offset = 10

    # Draw Attacker Target
    target_text = f"Attacker Target: {tuple(map(int, attacker_target_waypoint)) if attacker_target_waypoint else 'None'}"
    target_surface = font.render(target_text, True, WHITE)
    screen.blit(target_surface, (10, y_offset))
    y_offset += 30 # Move down for next line

    # Draw FPS
    fps_text = f"FPS: {fps:.1f}"
    fps_surface = font.render(fps_text, True, WHITE)
    screen.blit(fps_surface, (10, y_offset))

def draw_grid(screen):
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, SCREEN_HEIGHT)) # Darker grid
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, (40, 40, 40), (0, y), (SCREEN_WIDTH, y))
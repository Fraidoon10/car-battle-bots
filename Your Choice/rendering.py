import pygame
import math
from constants import * # Import all constants for colors etc.
# Import specific car types for type hinting if desired
from player_car import PlayerCar
from attacker_ai import AttackerAI
from defender_ai import DefenderAI
from obstacle import Obstacle
# Import FSM state for defender drawing logic
from ai.fsm import DefenseState
# Import necessary utility functions
from utils import normalize_vector # <--- CONFIRMED IMPORT


# --- Car Drawing Functions ---
def draw_player_car(screen: pygame.Surface, car: PlayerCar):
    """Draws the player-controlled car."""
    car.draw(screen)

def draw_attacker_ai(screen: pygame.Surface, car: AttackerAI, show_path: bool = False):
    """Draws the Attacker AI car."""
    # Path drawing is handled separately in main loop for layer control
    car.draw(screen)

def draw_defender_ai(screen: pygame.Surface, car: DefenderAI):
     """Draws the Defender AI car, including state and target indicators."""
     car.draw(screen)

# --- Obstacle Drawing ---
def draw_obstacles(screen: pygame.Surface, obstacles: list[Obstacle]):
    """Draws all obstacles in the list."""
    for obstacle in obstacles:
        obstacle.draw(screen)

# --- Path and Prediction Drawing ---
def draw_path(screen: pygame.Surface, path: list[tuple[float, float]], color: tuple[int,int,int] = PATH_COLOR, dot_size: int = 3):
    """Draws a generic path as a series of connected dots."""
    if not path or len(path) < 1:
        return
    try:
        points_int = [(int(p[0]), int(p[1])) for p in path]
        if len(points_int) > 1:
            pygame.draw.lines(screen, color, False, points_int, 1)
        for point in points_int:
            pygame.draw.circle(screen, color, point, dot_size)
    except (TypeError, ValueError) as e:
        print(f"Warning: Error drawing path - {e}.")

def draw_prediction(screen: pygame.Surface, predicted_path: list[tuple[float, float]], color: tuple[int,int,int] = PREDICTION_COLOR, dot_size: int = 2):
    """Draws a predicted path (uses the generic draw_path)."""
    draw_path(screen, predicted_path, color, dot_size)

# --- Laser Drawing ---
def draw_tracking_laser(screen: pygame.Surface, source_car, target_car, max_length: float, obstacles: list[Obstacle]):
    """
    Draws a 'laser' line from source to target, stopping at obstacles.
    """
    try:
        source_pos = source_car.get_position()
        target_pos = target_car.get_position()
        source_x, source_y = source_pos
        target_x, target_y = target_pos
    except AttributeError:
        print("Warning: source or target car missing get_position() method in draw_tracking_laser.")
        return

    dx = target_x - source_x
    dy = target_y - source_y
    dist_to_target = math.hypot(dx, dy)

    # Normalize direction (using imported function)
    norm_dx, norm_dy = normalize_vector(dx, dy) # Line 86 - requires import

    effective_laser_length = min(dist_to_target, max_length)
    potential_end_x = source_x + norm_dx * effective_laser_length
    potential_end_y = source_y + norm_dy * effective_laser_length

    hit_obstacle = False
    final_laser_end_x = potential_end_x
    final_laser_end_y = potential_end_y

    step_size = 5.0
    current_dist = step_size
    while current_dist < effective_laser_length:
        current_x = source_x + norm_dx * current_dist
        current_y = source_y + norm_dy * current_dist
        for obstacle in obstacles:
            if obstacle.rect.collidepoint(current_x, current_y):
                hit_obstacle = True
                final_laser_end_x = current_x
                final_laser_end_y = current_y
                break
        if hit_obstacle:
            break
        current_dist += step_size

    offset_dist = source_car.width / 3.0
    laser_start_x = source_x + norm_dx * offset_dist
    laser_start_y = source_y + norm_dy * offset_dist

    try:
        pygame.draw.line(screen, LASER_RED, (laser_start_x, laser_start_y),
                        (final_laser_end_x, final_laser_end_y), 5)
        pygame.draw.line(screen, LASER_CORE, (laser_start_x, laser_start_y),
                        (final_laser_end_x, final_laser_end_y), 2)

        reticle_pos = (int(final_laser_end_x), int(final_laser_end_y))
        pygame.draw.circle(screen, LASER_RED, reticle_pos, 6, 1)
        pygame.draw.line(screen, LASER_RED, (reticle_pos[0] - 6, reticle_pos[1]), (reticle_pos[0] + 6, reticle_pos[1]), 1)
        pygame.draw.line(screen, LASER_RED, (reticle_pos[0], reticle_pos[1] - 6), (reticle_pos[0], reticle_pos[1] + 6), 1)
    except (ValueError, TypeError):
         print(f"Warning: Invalid coordinates for drawing laser or reticle.")

    if not hit_obstacle and dist_to_target <= max_length:
        try:
            pygame.draw.circle(screen, YELLOW, (int(target_x), int(target_y)), int(target_car.width * 0.7), 2)
        except (ValueError, TypeError):
            print(f"Warning: Invalid coordinates for drawing target hit effect.")

# --- Debug and UI Drawing ---
def draw_grid(screen: pygame.Surface):
    """Draws a background grid for visual reference."""
    grid_line_color = (40, 40, 40)
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, grid_line_color, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, grid_line_color, (0, y), (SCREEN_WIDTH, y))

def draw_debug_info(screen: pygame.Surface, clock: pygame.time.Clock, game_mode: str, ai_car=None, los_timer_info=None):
    """Draws various debug information on the screen."""
    try:
        font = pygame.font.SysFont(None, 24)
        y_offset = 10
        x_offset = 10

        fps = clock.get_fps()
        fps_text = f"FPS: {fps:.1f}"
        fps_surface = font.render(fps_text, True, WHITE)
        screen.blit(fps_surface, (x_offset, y_offset))
        y_offset += 25

        mode_text = f"Mode: Player is {game_mode.upper()}"
        mode_surface = font.render(mode_text, True, WHITE)
        screen.blit(mode_surface, (x_offset, y_offset))
        y_offset += 25

        if isinstance(ai_car, DefenderAI):
            state_text = f"AI State: {ai_car.fsm.current_state.name}"
            state_surface = font.render(state_text, True, WHITE)
            screen.blit(state_surface, (x_offset, y_offset))
            y_offset += 25
            if ai_car.fsm.current_hide_target:
                 try:
                    hide_tgt = tuple(map(int, ai_car.fsm.current_hide_target))
                    hide_text = f"Hide Target: {hide_tgt}"
                    hide_surface = font.render(hide_text, True, HIDE_TARGET_COLOR)
                    screen.blit(hide_surface, (x_offset, y_offset))
                    y_offset += 25
                 except (TypeError, ValueError): pass
        elif isinstance(ai_car, AttackerAI):
            if ai_car.current_waypoint:
                 try:
                    wp = tuple(map(int, ai_car.current_waypoint))
                    wp_text = f"AI Waypoint: {wp}"
                 except (TypeError, ValueError):
                     wp_text = "AI Waypoint: Invalid"
            else:
                 wp_text = "AI Waypoint: None"
            wp_surface = font.render(wp_text, True, WHITE)
            screen.blit(wp_surface, (x_offset, y_offset))
            y_offset += 25
            path_len_text = f"Path Length: {len(ai_car.path)}"
            path_len_surface = font.render(path_len_text, True, WHITE)
            screen.blit(path_len_surface, (x_offset, y_offset))
            y_offset += 25

        if los_timer_info:
            start_time, duration_ms = los_timer_info
            if start_time is not None:
                elapsed_ms = pygame.time.get_ticks() - start_time
                elapsed_s = elapsed_ms / 1000.0
                target_s = duration_ms / 1000.0
                timer_text = f"LOS Timer: {elapsed_s:.1f}s / {target_s:.1f}s"
                timer_color = RED if elapsed_ms >= duration_ms else YELLOW
                timer_surface = font.render(timer_text, True, timer_color)
                screen.blit(timer_surface, (x_offset, y_offset))
                y_offset += 25

    except Exception as e:
         print(f"Error rendering debug info: {e}")

# --- Menu Drawing ---
def draw_menu(screen: pygame.Surface, selected_option: int):
    """Draws the main menu screen."""
    try:
        screen.fill(BLACK)
        font_title = pygame.font.SysFont(None, 72)
        font_options = pygame.font.SysFont(None, 48)

        title_text = TITLE
        title_surface = font_title.render(title_text, True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
        screen.blit(title_surface, title_rect)

        options = ["Play as Hider (Blue)", "Play as Chaser (Red)", "Quit"]
        y_start = SCREEN_HEIGHT / 2
        option_height = 60

        for i, option in enumerate(options):
            color = YELLOW if i == selected_option else LIGHT_GRAY
            option_surface = font_options.render(option, True, color)
            option_rect = option_surface.get_rect(center=(SCREEN_WIDTH / 2, y_start + i * option_height))
            screen.blit(option_surface, option_rect)

        font_instr = pygame.font.SysFont(None, 24)
        instr_text = "Use UP/DOWN arrows to select, ENTER to confirm."
        instr_surface = font_instr.render(instr_text, True, WHITE)
        instr_rect = instr_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.85))
        screen.blit(instr_surface, instr_rect)
    except Exception as e:
        print(f"Error drawing menu: {e}")

# --- Game Over Drawing ---
def draw_game_over(screen: pygame.Surface, winner: str):
    """Draws the game over screen."""
    try:
        font_large = pygame.font.SysFont(None, 80)
        font_small = pygame.font.SysFont(None, 36)

        if winner == "hider":
            message = "HIDER WINS! (Survived)"
            color = BLUE
        elif winner == "chaser":
            message = "CHASER WINS! (Caught)"
            color = RED
        else:
            message = "GAME OVER"
            color = WHITE

        text_surface = font_large.render(message, True, color)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40))
        screen.blit(text_surface, text_rect)

        prompt_text = "Press SPACE to Play Again or Q to Quit"
        prompt_surface = font_small.render(prompt_text, True, WHITE)
        prompt_rect = prompt_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40))
        screen.blit(prompt_surface, prompt_rect)
    except Exception as e:
        print(f"Error drawing game over screen: {e}")
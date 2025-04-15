import heapq
import math
from constants import GRID_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from utils import world_to_grid, grid_to_world, distance

class AStar:
    def __init__(self):
        self.grid_width = SCREEN_WIDTH // GRID_SIZE
        self.grid_height = SCREEN_HEIGHT // GRID_SIZE
        self.directions = [(0, -1), (1, 0), (0, 1), (-1, 0),
                           (1, -1), (1, 1), (-1, 1), (-1, -1)]  # Including diagonals
        self.obstacle_padding = 1 # How many grid cells around an obstacle are also blocked
        self.reset()

    def reset(self):
        self.grid = [[0 for _ in range(self.grid_height)] for _ in range(self.grid_width)]

    def update_obstacles(self, obstacles):
        """Update grid with obstacle positions, including padding."""
        self.reset()
        for obstacle in obstacles:
            # Get the grid range covered by the obstacle
            min_gx, min_gy = world_to_grid(obstacle.x, obstacle.y)
            max_gx, max_gy = world_to_grid(obstacle.x + obstacle.size, obstacle.y + obstacle.size)

            # Mark the obstacle cells and surrounding padding cells
            for gx in range(min_gx - self.obstacle_padding, max_gx + 1 + self.obstacle_padding):
                for gy in range(min_gy - self.obstacle_padding, max_gy + 1 + self.obstacle_padding):
                    if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                        self.grid[gx][gy] = 1  # 1 means obstacle/blocked

    def heuristic(self, a, b):
        """Euclidean distance heuristic (more accurate for diagonal movement)."""
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
        # Alternatively, use Manhattan: return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(self, start_pos, end_pos):
        """A* pathfinding algorithm."""
        # Convert world positions to grid positions
        start = world_to_grid(start_pos[0], start_pos[1])
        end = world_to_grid(end_pos[0], end_pos[1])

        # Ensure start and end are within grid bounds
        start = (min(max(0, start[0]), self.grid_width-1),
                 min(max(0, start[1]), self.grid_height-1))
        end = (min(max(0, end[0]), self.grid_width-1),
               min(max(0, end[1]), self.grid_height-1))

        # If start or end is on an obstacle, find nearest free cell (could be slow)
        if self.grid[start[0]][start[1]] == 1:
            start = self._find_nearest_free_cell(start)
            if not start: return [] # No free cell found near start
        if self.grid[end[0]][end[1]] == 1:
            end = self._find_nearest_free_cell(end)
            if not end: return [] # No free cell found near end

        # Check if start or end became invalid after finding nearest free cell
        if not start or not end:
            return []

        # Initialize open and closed lists
        open_list = []
        closed_set = set()

        # Add start node to open list: (f_score, g_score, position)
        # Store g_score in tuple to break ties in favor of paths closer to start
        start_g = 0
        start_h = self.heuristic(start, end)
        start_f = start_g + start_h
        heapq.heappush(open_list, (start_f, start_h, start)) # Use f_score, then h_score for priority

        came_from = {}
        g_score = {start: start_g}
        # f_score dictionary no longer strictly needed due to heapq storing f_score

        while open_list:
            f_prio, h_prio, current = heapq.heappop(open_list)

            if current == end:
                # Reconstruct path
                path = []
                temp = current
                while temp in came_from:
                    path.append(grid_to_world(temp[0], temp[1]))
                    temp = came_from[temp]
                # Optional: Add the start position's world coordinate if needed
                # path.append(start_pos)
                return path[::-1]  # Return reversed path

            closed_set.add(current)

            # Check all neighbors
            for dx, dy in self.directions:
                neighbor = (current[0] + dx, current[1] + dy)

                # Check if neighbor is valid
                if not (0 <= neighbor[0] < self.grid_width and 0 <= neighbor[1] < self.grid_height):
                    continue

                # Check if neighbor is an obstacle
                if self.grid[neighbor[0]][neighbor[1]] == 1:
                    continue

                # Check if neighbor is already evaluated
                if neighbor in closed_set:
                    continue

                # Calculate tentative g score (cost from start to neighbor)
                move_cost = 1.414 if dx*dy != 0 else 1 # Diagonal cost is sqrt(2)
                tentative_g = g_score[current] + move_cost

                # If neighbor not in open list or we found a better path
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h_score = self.heuristic(neighbor, end)
                    f_score = tentative_g + h_score

                    # Check if neighbor is already in the priority queue to update it
                    # This check is complex; usually easier to just push and let heapq handle duplicates
                    # (pulling the one with the lower f_score first)
                    heapq.heappush(open_list, (f_score, h_score, neighbor))

        # No path found
        return []

    def _find_nearest_free_cell(self, pos):
        """Find nearest grid cell that is not an obstacle using BFS."""
        queue = [(pos, 0)]  # (position, distance)
        visited = {pos}

        while queue:
            (x, y), dist = queue.pop(0)

            # Check if this cell is free
            if self.grid[x][y] == 0:
                return (x, y)

            # Optional: Limit search radius to prevent infinite loops if no path exists
            if dist > max(self.grid_width, self.grid_height): # Limit search distance
                 break

            # Add valid, unvisited neighbors
            for dx, dy in self.directions:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)
                if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height and
                    neighbor not in visited):
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))

        # Fallback: No free cell found within search radius
        print(f"Warning: Could not find free cell near {pos}")
        return None # Indicate failure
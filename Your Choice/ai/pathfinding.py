# CombinedChaseHideGame/ai/pathfinding.py
# --- START OF FILE pathfinding.py ---

import heapq
import math
# Updated imports
from constants import GRID_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from utils import world_to_grid, grid_to_world, distance

class AStar:
    def __init__(self):
        self.grid_width = SCREEN_WIDTH // GRID_SIZE
        self.grid_height = SCREEN_HEIGHT // GRID_SIZE
        # Directions: N, E, S, W, NE, SE, SW, NW
        self.directions = [(0, -1), (1, 0), (0, 1), (-1, 0),
                           (1, -1), (1, 1), (-1, 1), (-1, -1)]
        # Cost for straight vs diagonal moves
        self.move_costs = {
            (0, -1): 1.0, (1, 0): 1.0, (0, 1): 1.0, (-1, 0): 1.0, # Straight
            (1, -1): 1.414, (1, 1): 1.414, (-1, 1): 1.414, (-1, -1): 1.414 # Diagonal approx sqrt(2)
        }
        # How many grid cells around an obstacle are also considered blocked
        # Adjust based on car size vs grid size. 1 is usually reasonable.
        self.obstacle_padding = 1
        self.grid = [] # Initialize grid in reset
        self.reset()

    def reset(self):
        """Resets the grid to all clear (0)."""
        self.grid = [[0 for _ in range(self.grid_height)] for _ in range(self.grid_width)]

    def update_obstacles(self, obstacles: list):
        """
        Updates the internal grid based on a list of obstacle objects.
        Marks cells covered by obstacles and their padding as blocked (1).
        """
        self.reset()
        for obstacle in obstacles:
            # Determine the grid cell range covered by the obstacle
            # Add/subtract 0.1 to handle cases where obstacle edge falls exactly on grid line
            min_gx, min_gy = world_to_grid(obstacle.rect.left - 0.1, obstacle.rect.top - 0.1)
            max_gx, max_gy = world_to_grid(obstacle.rect.right + 0.1, obstacle.rect.bottom + 0.1)

            # Mark the obstacle cells and surrounding padding cells as blocked
            # Iterate over the padded bounding box in grid coordinates
            for gx in range(min_gx - self.obstacle_padding, max_gx + 1 + self.obstacle_padding):
                for gy in range(min_gy - self.obstacle_padding, max_gy + 1 + self.obstacle_padding):
                    # Ensure the grid coordinates are within the grid bounds
                    if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                        self.grid[gx][gy] = 1  # 1 means blocked

    def heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """
        Heuristic function for A*. Estimates cost from node 'a' to node 'b'.
        Using Euclidean distance for accuracy with diagonal movement.
        """
        return math.hypot(a[0] - b[0], a[1] - b[1]) # Euclidean distance
        # Alternative: Manhattan distance (faster but less accurate for diagonal)
        # return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(self, start_pos: tuple[float, float], end_pos: tuple[float, float]) -> list[tuple[float, float]]:
        """
        Finds the shortest path from start_pos to end_pos using A* algorithm.

        Args:
            start_pos: World coordinates (x, y) of the start.
            end_pos: World coordinates (x, y) of the end.

        Returns:
            A list of world coordinate tuples [(x, y), ...] representing the path,
            or an empty list if no path is found.
        """
        # Convert world positions to grid positions
        start_node = world_to_grid(start_pos[0], start_pos[1])
        end_node = world_to_grid(end_pos[0], end_pos[1])

        # Clamp nodes to be within grid boundaries
        start_node = (max(0, min(start_node[0], self.grid_width - 1)),
                      max(0, min(start_node[1], self.grid_height - 1)))
        end_node = (max(0, min(end_node[0], self.grid_width - 1)),
                    max(0, min(end_node[1], self.grid_height - 1)))

        # --- Handle cases where start or end node is blocked ---
        start_is_obstacle = self.grid[start_node[0]][start_node[1]] == 1
        end_is_obstacle = self.grid[end_node[0]][end_node[1]] == 1

        if start_is_obstacle:
            # print(f"Warning: Start node {start_node} is blocked. Finding nearest free cell.")
            start_node = self._find_nearest_free_cell(start_node, end_node) # Pass target to prioritize direction
            if not start_node:
                print("Error: Could not find a free cell near the start position.")
                return [] # No path possible if start is hopelessly blocked

        if end_is_obstacle:
            # print(f"Warning: End node {end_node} is blocked. Finding nearest free cell.")
            end_node = self._find_nearest_free_cell(end_node, start_node) # Pass start to prioritize direction
            if not end_node:
                print("Error: Could not find a free cell near the end position.")
                return [] # No path possible if end is hopelessly blocked

        # Check again if start == end after finding nearest cells
        if start_node == end_node:
             return [grid_to_world(end_node[0], end_node[1])] # Path is just the destination


        # --- A* Algorithm Initialization ---
        open_list = []  # Priority queue (min-heap)
        closed_set = set() # Set of nodes already evaluated

        # Store parent nodes for path reconstruction
        came_from: dict[tuple[int, int], tuple[int, int] | None] = {start_node: None}

        # g_score: Cost from start node to current node
        g_score: dict[tuple[int, int], float] = {start_node: 0.0}

        # f_score: Estimated total cost (g_score + heuristic)
        # We store (f_score, h_score, node) in the heap for tie-breaking (favor lower h_score)
        start_h = self.heuristic(start_node, end_node)
        start_f = g_score[start_node] + start_h
        heapq.heappush(open_list, (start_f, start_h, start_node))

        # --- A* Main Loop ---
        while open_list:
            # Get node with the lowest f_score from the priority queue
            current_f, current_h, current_node = heapq.heappop(open_list)

            # Goal reached?
            if current_node == end_node:
                return self._reconstruct_path(came_from, current_node)

            # If we already processed this node with a lower f_score, skip
            # This handles duplicates pushed onto the heap
            if current_node in closed_set:
                continue

            closed_set.add(current_node)

            # --- Explore Neighbors ---
            for dx, dy in self.directions:
                neighbor_node = (current_node[0] + dx, current_node[1] + dy)

                # Check bounds
                if not (0 <= neighbor_node[0] < self.grid_width and 0 <= neighbor_node[1] < self.grid_height):
                    continue

                # Check if obstacle
                if self.grid[neighbor_node[0]][neighbor_node[1]] == 1:
                    continue

                # Calculate tentative g_score for neighbor
                move_cost = self.move_costs[(dx, dy)]
                tentative_g = g_score[current_node] + move_cost

                # If this path to neighbor is better than any previous one found
                if tentative_g < g_score.get(neighbor_node, float('inf')):
                    # Update path info for this neighbor
                    came_from[neighbor_node] = current_node
                    g_score[neighbor_node] = tentative_g
                    h_score = self.heuristic(neighbor_node, end_node)
                    f_score = tentative_g + h_score

                    # Add neighbor to the open list (priority queue)
                    # No need to check if already present; heapq handles priorities
                    heapq.heappush(open_list, (f_score, h_score, neighbor_node))

        # No path found
        print("A* Warning: No path found.")
        return []

    def _reconstruct_path(self, came_from: dict, current_node: tuple[int, int]) -> list[tuple[float, float]]:
        """Reconstructs the path from end node back to start node."""
        path_world = []
        temp_grid = current_node
        while temp_grid is not None:
            # Convert grid node to world coordinates for the final path
            path_world.append(grid_to_world(temp_grid[0], temp_grid[1]))
            temp_grid = came_from.get(temp_grid) # Move to the parent node

        # The path is reconstructed backwards, so reverse it
        return path_world[::-1]

    def _find_nearest_free_cell(self, start_node: tuple[int, int], target_node: tuple[int, int]) -> tuple[int, int] | None:
        """
        Finds the nearest grid cell to start_node that is not an obstacle (value 0).
        Uses a breadth-first search (BFS) approach, prioritizing cells closer to the target_node.

        Args:
            start_node: The grid coordinates (gx, gy) of the blocked cell.
            target_node: The grid coordinates (gx, gy) of the ultimate pathfinding target.

        Returns:
            The coordinates (gx, gy) of the nearest free cell, or None if none found within search radius.
        """
        queue = [] # Use heapq as a priority queue: (heuristic_to_target, distance_from_start, node)
        visited = {start_node}
        # Initial priority favors cells closer to the overall target
        initial_h = self.heuristic(start_node, target_node)
        heapq.heappush(queue, (initial_h, 0, start_node)) # (priority, distance, node)

        search_radius = max(self.grid_width, self.grid_height) // 2 # Limit search

        while queue:
            prio, dist, (x, y) = heapq.heappop(queue)

            # Check if this cell is free
            if self.grid[x][y] == 0:
                return (x, y) # Found the nearest free cell

            # Stop searching if too far
            if dist >= search_radius:
                continue

            # Explore neighbors
            for dx, dy in self.directions:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)

                # Check bounds and if already visited
                if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height and
                        neighbor not in visited):
                    visited.add(neighbor)
                    # Check if the neighbor itself is blocked (we only queue valid potential *next* steps)
                    # if self.grid[nx][ny] == 0: # Only add free cells? No, add blocked ones too to expand search.
                    neighbor_dist = dist + self.move_costs[(dx, dy)]
                    neighbor_h = self.heuristic(neighbor, target_node) # Heuristic towards path target
                    # Priority combines distance traveled and heuristic to target
                    neighbor_prio = neighbor_dist + neighbor_h
                    heapq.heappush(queue, (neighbor_prio, neighbor_dist, neighbor))

        # No free cell found within the search radius
        print(f"Warning: Could not find a free cell near {start_node} within radius {search_radius}.")
        return None

# --- END OF FILE pathfinding.py ---
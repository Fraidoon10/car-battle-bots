# CombinedChaseHideGame/ai/prediction.py
# --- START OF FILE prediction.py ---

# Updated import
from constants import PREDICTION_STEPS, PREDICTION_INTERVAL, FPS

class PositionPredictor:
    """Predicts future positions of entities based on current velocity."""

    def __init__(self):
        # History might be useful for more advanced prediction (e.g., acceleration)
        # but is currently unused by the linear prediction.
        self.history = []  # List of (position, velocity, timestamp) tuples
        self.max_history = 10

    def add_observation(self, position: tuple[float, float], velocity: tuple[float, float], timestamp: float):
        """Add an observation to history (currently unused by linear predict)."""
        self.history.append((position, velocity, timestamp))
        # Keep history size limited
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def predict_linear(self, position: tuple[float, float], velocity: tuple[float, float], time_delta: float) -> tuple[float, float]:
        """Simple linear prediction: new_pos = old_pos + velocity * time_delta."""
        pred_x = position[0] + velocity[0] * time_delta
        pred_y = position[1] + velocity[1] * time_delta
        return pred_x, pred_y

    def predict_future_path(self, position: tuple[float, float], velocity: tuple[float, float],
                              steps: int = PREDICTION_STEPS, interval: int = PREDICTION_INTERVAL) -> list[tuple[float, float]]:
        """
        Predicts a series of future positions using simple linear extrapolation.

        Args:
            position: Current (x, y) position of the object.
            velocity: Current (vx, vy) velocity of the object.
            steps: Total number of future frames to predict up to.
            interval: The gap (in frames) between predicted points in the path.

        Returns:
            A list of predicted (x, y) position tuples. Returns empty list if FPS is invalid.
        """
        path = []

        if FPS <= 0:
            print("Warning: FPS is zero or negative. Cannot calculate prediction time increment.")
            return path
        if interval <= 0:
             print("Warning: Prediction interval must be positive.")
             return path


        # Time elapsed per frame
        time_increment_per_frame = 1.0 / FPS
        # Time between each prediction point we store
        time_increment_per_point = time_increment_per_frame * interval

        num_points = steps // interval

        for i in range(1, num_points + 1): # Start from 1 to predict future points
            # Total time elapsed from 'now' to this future point
            elapsed_time = time_increment_per_point * i

            # Predict position at that future time
            pred_pos = self.predict_linear(position, velocity, elapsed_time)
            path.append(pred_pos)

        return path

# --- END OF FILE prediction.py ---
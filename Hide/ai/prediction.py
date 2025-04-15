from constants import PREDICTION_STEPS, FPS

class PositionPredictor:
    """Predicts future positions of entities based on current velocity and history."""

    def __init__(self):
        self.history = []  # List of (position, velocity, timestamp) tuples
        self.max_history = 10  # Maximum number of history entries to keep

    def add_observation(self, position, velocity, timestamp):
        """Add an observation to history."""
        self.history.append((position, velocity, timestamp))

        # Keep history size limited
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def predict_linear(self, position, velocity, time_delta):
        """Simple linear prediction based on current velocity and time delta."""
        # predict_position(position[0], position[1], velocity[0], velocity[1], steps)
        pred_x = position[0] + velocity[0] * time_delta
        pred_y = position[1] + velocity[1] * time_delta
        return pred_x, pred_y

    def predict_future_path(self, position, velocity, steps=PREDICTION_STEPS, interval=5):
        """Predict a series of future positions to form a path using linear prediction."""
        path = []

        if FPS <= 0: # Avoid division by zero if FPS is invalid
            print("Warning: FPS is zero or negative, cannot calculate prediction time increment.")
            return path

        # Calculate prediction time increment based on FPS (assuming constant FPS)
        time_increment_per_step = 1.0 / FPS # Time elapsed per frame
        time_increment_per_interval = time_increment_per_step * interval # Time between prediction points

        # Using current position and velocity for prediction
        current_pos = position
        current_vel = velocity # Assuming constant velocity for linear prediction

        for step_index in range(steps // interval):
            # Calculate total time elapsed for this prediction point
            elapsed_time = time_increment_per_interval * (step_index + 1) # Time from now

            # Linear prediction: pos = initial_pos + velocity * time
            pred_pos = self.predict_linear(position, velocity, elapsed_time)
            path.append(pred_pos)

        return path
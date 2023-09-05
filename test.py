import sys
import numpy as np
from vispy import app, scene

# Create a canvas
canvas = scene.SceneCanvas(keys='interactive', bgcolor='white', size=(800, 800), title="Circular Curve Example")
view = canvas.central_widget.add_view()

# Create a circular path
num_segments = 100
theta = np.linspace(0, 2 * np.pi, num_segments)
radius = 0.5
x = radius * np.cos(theta)
y = radius * np.sin(theta)

# Create a scatter plot to represent the circular curve
scatter = scene.visuals.Markers()
scatter.set_data(np.column_stack((x, y)), face_color='blue', size=5)

# Add the scatter plot to the view
view.add(scatter)

# Set the aspect ratio and adjust the viewport to show the full circle
view.camera.set_aspect('equal')
view.camera.set_range()

# Run the app
if __name__ == '__main__':
    canvas.show()
    if sys.flags.interactive == 0:
        app.run()

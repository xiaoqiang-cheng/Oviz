import numpy as np
from vispy import app, scene

# Create a canvas
canvas = scene.SceneCanvas(keys='interactive')
view = canvas.central_widget.add_view()

# Create a camera
cam = scene.TurntableCamera(up='z')

# Set camera parameters
cam.center = (0, 0, 0)  # Initial center point
cam.distance = 5  # Initial distance from center
view.camera = cam

# Create a cube visual
cube = scene.visuals.Cube(size=2, color=(1, 0, 0, 1), edge_color='k')
view.add(cube)

# Function to translate the center point
def translate_center(dx, dy, dz):
    cam.center += np.array([dx, dy, dz])

# Define keyboard events for translation
@canvas.events.key_press.connect
def on_key_press(event):
    if event.text == 'w':
        translate_center(0, 1, 0)  # Move up
    elif event.text == 's':
        translate_center(0, -1, 0)  # Move down
    elif event.text == 'a':
        translate_center(-1, 0, 0)  # Move left
    elif event.text == 'd':
        translate_center(1, 0, 0)  # Move right
    elif event.text == 'q':
        translate_center(0, 0, 1)  # Move forward
    elif event.text == 'e':
        translate_center(0, 0, -1)  # Move backward

# Show the canvas
canvas.show()

# Run the application
app.run()

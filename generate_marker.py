import cv2
import cv2.aruco as aruco
import numpy as np

# --- Configuration ---
MARKER_ID = 23
MARKER_SIZE_PIXELS = 400

# We'll use a very common dictionary
DICTIONARY_NAME = aruco.DICT_6X6_250
FILENAME = f"marker_{MARKER_ID}.png"
# ---------------------

print(f"Generating marker ID {MARKER_ID} from dictionary...")

# Load the dictionary
aruco_dict = aruco.getPredefinedDictionary(DICTIONARY_NAME)

# Create an image to draw the marker on
marker_image = np.zeros((MARKER_SIZE_PIXELS, MARKER_SIZE_PIXELS), dtype=np.uint8)

# Generate the marker
# The '1' at the end is the border thickness
marker_image = aruco.generateImageMarker(aruco_dict, MARKER_ID, MARKER_SIZE_PIXELS, marker_image, 1)

# Save the marker as a PNG file
cv2.imwrite(FILENAME, marker_image)

print(f"Successfully saved marker to {FILENAME}")
print("Please print this file or display it on your phone.")
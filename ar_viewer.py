import cv2
import cv2.aruco as aruco
import numpy as np

print("Starting AR Viewer...")

# 1. Initialize Camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open camera")
    exit()

# 2. Set up the AruCo detector to find our marker
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

print("AR Viewer running. Show marker ID 23 to the camera.")
print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    
    # 3. Detect markers in the frame
    corners, ids, _ = detector.detectMarkers(frame)

    # 4. If any markers are found...
    if ids is not None:
        # Loop through all found markers
        for i, marker_id in enumerate(ids):
            # We only care about our specific marker, ID 23
            if marker_id[0] == 23:
                
                # 'marker_corners' is a list of the 4 corner points
                marker_corners = corners[i][0]
                int_corners = np.int32(marker_corners)

                # --- This is the "Boxes" part ---
                
                # BOX 1: The Green Border
                cv2.polylines(frame, [int_corners], True, (0, 255, 0), 2)
                
                # BOX 2: The Blue Filled "Object"
                overlay = frame.copy()
                cv2.fillPoly(overlay, [int_corners], (255, 100, 0)) # BGR
                alpha = 0.5 # 50% transparent
                frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
                
                # BOX 3: The Text Label
                tl = int_corners[0] # Top-left corner
                cv2.putText(frame, f"Object ID: {marker_id[0]} (Desk)", 
                            (tl[0], tl[1] - 15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.6, (0, 255, 0), 2)

    # 5. Display the final image
    cv2.imshow('AR Viewer - Press Q to Quit', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
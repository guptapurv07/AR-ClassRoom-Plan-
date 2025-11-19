# 📐 Advanced AR Classroom Planner

**Author:** Apurv , Madhvan , Archita
This project implements a 3D planning application using **Pygame** (for the user interface and virtual 3D rendering) integrated with **OpenCV** (for webcam access and Augmented Reality object tracking). The goal is to allow a user to design a classroom layout in a virtual environment and then view/test the placement of virtual objects (desks, chairs) in the real world using AruCo markers.

## ✨ Features

* **3D Layout Editor:** Create and manipulate classroom layouts by placing, moving, rotating, and scaling objects (Desk, Chair, Cabinet, etc.) in a 3D environment.
* **Integrated AR Mode:** Seamlessly switch from the virtual planner to a live webcam feed.
* **AruCo Marker Generation:** Generate unique AruCo marker images directly from the application UI.
* **Object Tracking:** Use specific markers (IDs 23, 24, 25) as real-world anchors to instantly augment the live video feed with simulated virtual objects (colored boxes representing furniture).

## 🚀 Setup and Installation

### 1. Prerequisites

This project requires Python 3 and the following external libraries:

pip install pygame opencv-python opencv-contrib-python numpy

### 2. Project Structure

Ensure all the following files are in the same directory:

File Name	Description
main.py	Starts the application loop.
app.py	Contains the main AdvancedClassroomPlanner class, 3D logic, AR detector setup, and UI event handling. (Contains core AR logic)
ui.py	Handles all button layouts, drawing styles, and 3D object drawing routines.
ar_camera.py	NEW: Manages the webcam feed in a separate thread to prevent the Pygame window from freezing.
objects.py	Defines the Point3D and Object3D data structures.
camera.py	Defines the Camera class for 3D perspective projection.

## 🕹️ How to Run the Project
Run the main application file from your terminal:

Bash
python main.py
Initial Setup:

The application will start in the Room Dimensions Input Screen.

Enter dimensions (e.g., Width: 30, Depth: 30, Height: 10).

Click "Generate Room".

Click the door on the welcome screen to enter the main planner view.

Generate Markers:

Click the "Gen Marker" button on the top UI bar.

This will create files like marker_23.png, marker_24.png, etc., in your project directory.

Test Augmented Reality:

Display the Marker: Open marker_23.png on your phone, tablet, or a second monitor, ensuring it's clearly visible without glare.

Click the "AR Cam" button. The screen will switch to your live camera feed.

Show the marker to your webcam.

Marker ID	Object Simulated	Color
ID 23	Desk	Blue
ID 24	Chair	Red
ID 25	Cabinet	Yellow
⚙️ Technical Design Overview
The AR feature works by separating the slow I/O tasks from the main GUI loop:

Component	Technology	Role
3D Rendering	Pygame	Handles the main drawing window and virtual object geometry.
Camera Feed	ar_camera.py (Threading + OpenCV)	Captures frames from the webcam in a separate thread to prevent the Pygame UI from freezing while waiting for I/O.
Object Detection	OpenCV's AruCo Module	Runs detection logic on the frames to find the ID and 3D pose of the marker.
Drawing Overlay	Pygame (Main Thread)	Uses the marker's corner coordinates to draw the colored shapes (the virtual objects) directly onto the current video frame before displaying it.

# Interactive Cargo Planner

An interactive web application for planning and visualizing cargo loading into trucks, featuring a 3D preview, volumetric fit calculations, and persistent inventory management.

## Project Overview

This project provides a user-friendly interface to simulate loading various types of boxes into different truck sizes. It helps in optimizing space utilization and managing inventory effectively. The application consists of a Python Flask backend for packing logic and inventory management, and a modern web frontend for visualization and interaction.

## Features

* **Truck Selection**: Choose from predefined truck types with varying capacities.
* **Box Configuration**: Select different box types and specify quantities to be loaded.
* **Volumetric Fit Calculation**: Automatically calculates the optimal number of each box type to fit a selected truck based on volume.
* **3D Load Visualization**: View the packed cargo in a detailed 3D environment, allowing for intuitive understanding of the loading plan.
* **Persistent Inventory**: Manage box quantities through a backend database, with options to "Send Cargo" (decrement stock) or "Add Boxes" (increment stock).
* **Responsive Design**: A modern and adaptive user interface built with Tailwind CSS.

## Technologies Used

### Frontend
* **HTML5**
* **CSS3** (with Tailwind CSS)
* **JavaScript**
* **Three.js**: For 3D rendering and visualization of the cargo load.
* **Font Awesome**: For various icons.

### Backend
* **Python**: The core language for the server logic.
* **Flask**: A micro web framework for handling API requests.
* **Flask-CORS**: Enables Cross-Origin Resource Sharing for frontend-backend communication.
* **py3dbp**: A Python library used for 3D bin packing algorithms.
* **SQLite**: A lightweight, file-based database for storing box inventory.

## Setup Instructions

To run this application locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [<your-repository-url>](https://github.com/sabazadam/CargoProject)
    cd CargoProject # or your project's root directory
    ```

2.  **Backend Setup:**
    * Navigate to the `backend` directory:
        ```bash
        cd backend
        ```
    * Install the required Python packages:
        ```bash
        pip install Flask Flask-Cors py3dbp
        ```
    * Run the Flask application:
        ```bash
        python app.py
        ```
        The backend server will start, typically on `http://127.0.0.1:5500`. This will also initialize the `cargo_planner.db` SQLite database file.

3.  **Frontend Setup:**
    * Navigate to the `frontend` directory:
        ```bash
        cd ../frontend
        ```
    * Open `index.html` in your web browser. You can typically just double-click the file or drag it into your browser.

Ensure both the backend server is running and the `index.html` file is open in your browser for the application to function correctly.

## Usage

1.  **Select a Truck**: Click on a truck card in the "Select Truck" section to choose your cargo vehicle.
2.  **Configure Box Quantities**: Adjust the number of each box type you wish to load using the input fields or the `+` and `-` buttons. The "Stock" display shows current inventory.
3.  **Volumetric Fit**: Click "Volumetric Fit" to automatically populate box quantities that fit the selected truck based on available inventory and volume.
4.  **Calculate & View 3D Load**: Click this button to run the packing algorithm and see a 3D visualization of how the selected boxes would be placed inside the truck. *Note: This action does NOT decrement inventory.*
5.  **Send Cargo**: After reviewing the 3D load, click "Send Cargo" to officially dispatch the selected boxes. This action will decrement the corresponding box quantities in your inventory database.
6.  **Add Boxes**: Use this button to manually add more boxes to your inventory. A prompt will appear asking for quantities in a `boxType=amount` format (e.g., `small=5,medium=10`).
7.  **Reset Selections**: Clears all selected box quantities and resets the UI.

Enjoy planning your cargo!

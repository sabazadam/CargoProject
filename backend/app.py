# app.py - The Python Backend Server

from flask import Flask, request, jsonify
from flask_cors import CORS
from py3dbp import Packer, Bin, Item

# 1. Initialize the Flask App
app = Flask(__name__)

# 2. Configure CORS (Cross-Origin Resource Sharing)
# This is crucial to allow our frontend (on a different address) to communicate with this backend.
CORS(app)


# 3. Define the API Endpoint for packing
@app.route('/pack', methods=['POST'])
def pack_boxes():
    """
    Receives truck and box data, calculates the optimal 3D packing,
    and returns the placements of the boxes.
    """
    # Get the JSON data sent from the frontend
    data = request.get_json()

    if not data or 'truck' not in data or 'boxes' not in data:
        return jsonify({"error": "Invalid data format. 'truck' and 'boxes' keys are required."}), 400

    truck_data = data['truck']
    boxes_data = data['boxes']

    try:
        # --- Using py3dbp to calculate placements ---

        # 1. Create the Packer
        packer = Packer()

        # 2. Create the Bin (our truck)
        # Note: We map our dimensions to py3dbp's (W, H, D)
        truck_bin = Bin(
            truck_data['name'],
            truck_data['length'],  # Corresponds to 'width' (W) in py3dbp Bin constructor
            truck_data['height'],  # Corresponds to 'height' (H)
            truck_data['width'],  # Corresponds to 'depth' (D)
            10000  # A large number for max_weight, as we are not constraining by weight
        )
        packer.add_bin(truck_bin)

        # 3. Add the Items (our boxes) to be packed
        for box_key, box in boxes_data.items():
            if box.get('count', 0) > 0:
                for i in range(box['count']):
                    # Add each box instance as an item to be packed
                    packer.add_item(Item(
                        f"{box_key}_{i}",  # Name format: "small_0", "small_1", etc.
                        box['length'],
                        box['height'],
                        box['width'],
                        1  # A dummy weight for each box
                    ))

        # 4. Run the packing algorithm
        print("Starting the packing algorithm...")
        packer.pack(
            bigger_first=True,  # Pack larger items first for better results
            distribute_items=False
        )
        print("Packing algorithm finished.")

        # 5. Format the results to send back to the frontend
        placements = []
        # We only have one bin (the truck)
        packed_bin = packer.bins[0]

        for item in packed_bin.items:
            pos = item.position
            dim = item.get_dimension()

            # ** FIX: Convert Decimal types from py3dbp to float for calculations **
            pos_x, pos_y, pos_z = float(pos[0]), float(pos[1]), float(pos[2])
            dim_w, dim_h, dim_d = float(dim[0]), float(dim[1]), float(dim[2])

            # Center position calculation
            center_x = pos_x + dim_w / 2
            center_y = pos_y + dim_h / 2
            center_z = pos_z + dim_d / 2

            # Adjust from py3dbp's corner-based origin to our Three.js center-based origin
            final_x = center_x - truck_data['length'] / 2
            final_y = center_y
            final_z = center_z - truck_data['width'] / 2

            placements.append({
                'name': item.name,
                # Dimensions for Three.js box geometry
                'length': dim_w,
                'height': dim_h,
                'width': dim_d,
                # Final center coordinates for the Three.js box mesh
                'x_center': final_x,
                'y_center': final_y,
                'z_center': final_z,
                # Extract original key (e.g., "small") to get the color in the frontend
                'key': item.name.split('_')[0]
            })

        unplaced_count = len(packer.unfit_items)
        print(f"Packing complete. Placed: {len(placements)} boxes. Unplaced: {unplaced_count} boxes.")

        return jsonify({
            "placements": placements,
            "unplaced_count": unplaced_count
        }), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        # It's useful to also log the traceback for debugging
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 4. Standard entry point to run the Flask app
if __name__ == '__main__':
    # Runs the app on http://127.0.0.1:5500 (or your chosen port)
    # Make sure this port matches the one in your frontend's fetch call
    app.run(host='0.0.0.0', port=5500, debug=True)

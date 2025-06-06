# app.py - The Python Backend Server

import sqlite3
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from py3dbp import Packer, Bin, Item

# 1. Initialize the Flask App
app = Flask(__name__)

# 2. Configure CORS (Cross-Origin Resource Sharing)
# This is crucial to allow our frontend (on a different address) to communicate with this backend.
CORS(app)

DATABASE = 'cargo_planner.db'

# Initial data that would typically be loaded once into the database
INITIAL_BOX_TYPES_DATA = {
    "small": {"name": "Small Box", "length": 10, "width": 10, "height": 10, "volume": 1000, "icon": "fa-box-archive", "color": "0xff0000"},
    "medium": {"name": "Medium Box", "length": 20, "width": 20, "height": 20, "volume": 8000, "icon": "fa-box-open", "color": "0x00ff00"},
    "large": {"name": "Large Box", "length": 30, "width": 30, "height": 30, "volume": 27000, "icon": "fa-boxes-stacked", "color": "0x0000ff"},
    "flat": {"name": "Flat Box", "length": 40, "width": 30, "height": 5, "volume": 6000, "icon": "fa-box", "color": "0xffff00"},
    "long": {"name": "Long Box", "length": 50, "width": 10, "height": 10, "volume": 5000, "icon": "fa-box-tissue", "color": "0xff00ff"}
}

INITIAL_INVENTORY_DATA = {
    "small": 100, "medium": 50, "large": 20, "flat": 30, "long": 40
}

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS boxes (
            key TEXT PRIMARY KEY,
            name TEXT,
            length REAL,
            width REAL,
            height REAL,
            volume REAL,
            color TEXT,
            stock INTEGER
        )
    ''')

    # Insert initial data if the table is empty
    for box_key, box_data in INITIAL_BOX_TYPES_DATA.items():
        # Check if the box already exists to prevent duplicate inserts on subsequent runs
        cursor.execute("SELECT key FROM boxes WHERE key = ?", (box_key,))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO boxes (key, name, length, width, height, volume, color, stock) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    box_key,
                    box_data['name'],
                    box_data['length'],
                    box_data['width'],
                    box_data['height'],
                    box_data['volume'],
                    box_data['color'],
                    INITIAL_INVENTORY_DATA.get(box_key, 0) # Get initial stock from INITIAL_INVENTORY_DATA
                )
            )
    conn.commit()
    conn.close()

def get_box_data_from_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Sort by volume ascending to ensure consistent order on the frontend
    cursor.execute("SELECT key, name, length, width, height, volume, color, stock FROM boxes ORDER BY volume ASC")
    boxes = {}
    for row in cursor.fetchall():
        box_key, name, length, width, height, volume, color, stock = row
        boxes[box_key] = {
            "name": name,
            "length": length,
            "width": width,
            "height": height,
            "volume": volume,
            "color": int(color, 16), # Convert hex string back to integer for Three.js
            "stock": stock
        }
    conn.close()
    return boxes

def update_box_stock_in_db(cursor, box_key, change_amount):
    # Note: this function now requires a cursor to be passed to support transactions
    cursor.execute("UPDATE boxes SET stock = stock + ? WHERE key = ?", (change_amount, box_key))

@app.before_request
def before_request():
    init_db()

@app.route('/inventory', methods=['GET'])
def get_inventory():
    try:
        boxes_data = get_box_data_from_db()
        inventory_response = {}
        for key, data in boxes_data.items():
            inventory_response[key] = {
                **data,
                "color": hex(data["color"]),
                # FIXED: Add the icon from the initial static data into the API response
                "icon": INITIAL_BOX_TYPES_DATA.get(key, {}).get("icon", "fa-box")
            }
        return jsonify(inventory_response), 200
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/inventory/update_batch', methods=['POST'])
def update_inventory_batch():
    data = request.get_json()
    if not data or 'updates' not in data or not isinstance(data['updates'], list):
        return jsonify({"error": "Invalid data format. 'updates' array is required."}), 400

    updates = data['updates']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        for update in updates:
            box_key = update.get('box_key')
            change_amount = update.get('change_amount')

            if not box_key or change_amount is None:
                raise ValueError("Each update must include 'box_key' and 'change_amount'.")

            # Optional: Check if stock would go negative if change_amount is negative
            if change_amount < 0:
                 cursor.execute("SELECT stock FROM boxes WHERE key = ?", (box_key,))
                 current_stock = cursor.fetchone()
                 if current_stock and current_stock[0] + change_amount < 0:
                     raise ValueError(f"Cannot decrement stock for '{box_key}' below zero.")

            update_box_stock_in_db(cursor, box_key, change_amount)

        conn.commit()
        return jsonify({"message": "Inventory updated successfully."}), 200
    except Exception as e:
        conn.rollback()
        print(f"Error updating inventory batch: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/pack', methods=['POST'])
def pack_boxes():
    data = request.get_json()

    if not data or 'truck' not in data or 'boxes' not in data:
        return jsonify({"error": "Invalid data format. 'truck' and 'boxes' keys are required."}), 400

    truck_data = data['truck']
    boxes_data_requested = data['boxes'] # These are the boxes requested for packing

    try:
        packer = Packer()
        truck_bin = Bin(
            truck_data['name'],
            truck_data['length'],
            truck_data['height'],
            truck_data['width'],
            10000
        )
        packer.add_bin(truck_bin)

        # Fetch actual box data (including current stock) from the database
        available_boxes_db = get_box_data_from_db()

        for box_key, box_info_requested in boxes_data_requested.items():
            if box_key in available_boxes_db:
                # Use the stock from the database as the actual available count
                # and take the minimum of requested count and available stock
                actual_count = min(box_info_requested.get('count', 0), available_boxes_db[box_key]['stock'])
                # Only add items if their actual count is greater than 0
                if actual_count > 0:
                    for i in range(actual_count):
                        packer.add_item(Item(
                            f"{box_key}_{i}",
                            available_boxes_db[box_key]['length'],
                            available_boxes_db[box_key]['height'],
                            available_boxes_db[box_key]['width'],
                            1
                        ))
            else:
                print(f"Warning: Box type '{box_key}' not found in database.")


        print("Starting the packing algorithm...")
        packer.pack(
            bigger_first=True,
            distribute_items=False
        )
        print("Packing algorithm finished.")

        placements = []
        packed_bin = packer.bins[0]
        # We no longer decrement stock here. Stock is decremented only on 'Send Cargo'.
        # The frontend will be responsible for refreshing its view based on what was *placed*.

        for item in packed_bin.items:
            pos = item.position
            dim = item.get_dimension()

            pos_x, pos_y, pos_z = float(pos[0]), float(pos[1]), float(pos[2])
            dim_w, dim_h, dim_d = float(dim[0]), float(dim[1]), float(dim[2])

            center_x = pos_x + dim_w / 2
            center_y = pos_y + dim_h / 2
            center_z = pos_z + dim_d / 2

            final_x = center_x - truck_data['length'] / 2
            final_y = center_y
            final_z = center_z - truck_data['width'] / 2

            box_key = item.name.split('_')[0]
            placements.append({
                'name': item.name,
                'length': dim_w,
                'height': dim_h,
                'width': dim_d,
                'x_center': final_x,
                'y_center': final_y,
                'z_center': final_z,
                'key': box_key
            })

        unplaced_count = len(packer.unfit_items)
        print(f"Packing complete. Placed: {len(placements)} boxes. Unplaced: {unplaced_count} boxes.")

        return jsonify({
            "placements": placements,
            "unplaced_count": unplaced_count,
            # No 'updated_inventory' here, as inventory is not updated by /pack anymore
        }), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# 4. Standard entry point to run the Flask app
if __name__ == '__main__':
    init_db() # Ensure DB is initialized when running the app directly
    # Runs the app on http://127.0.0.1:5500 (or your chosen port)
    # Make sure this port matches the one in your frontend's fetch call
    app.run(host='0.0.0.0', port=5500, debug=True)
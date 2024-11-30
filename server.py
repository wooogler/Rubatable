from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flexispot import LoctekMotion, SERIAL_PORT
import threading

# Flask web server setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Desk control setup
locktek = LoctekMotion(socketio)

desk_thread = None
height_thread = None
stop_event = threading.Event()

def control_desk(direction):
    locktek.execute_command("wake_up")
    locktek.move(direction)

# WebSocket event handler
@socketio.on('control')
def handle_control(data):
    global desk_thread
    height = 0

    if isinstance(data, dict) and data.get("action") == "UP":
        print('UP')
        if desk_thread is None or not desk_thread.is_alive():
            desk_thread = socketio.start_background_task(control_desk, "up")
        result = "Raising the desk."
    elif isinstance(data, dict) and data.get("action") == "DOWN":
        print('DOWN')
        if desk_thread is None or not desk_thread.is_alive():
            desk_thread = socketio.start_background_task(control_desk, "down")
        result = "Lowering the desk."
    elif isinstance(data, dict) and data.get("action") == "STOP":
        print('STOP')
        locktek.stop()
        if desk_thread and desk_thread.is_alive():
            desk_thread.join()
            desk_thread = None
        result = "Desk movement stopped."
    elif isinstance(data, dict) and data.get("action") == "GET_HEIGHT":
        print('GET_HEIGHT')
        height = locktek.get_height_when_sleep()
        socketio.emit('height_update', {'height': height})
        result = "Getting the desk height."
    elif isinstance(data, dict) and data.get("action") == "MOVE_TO_HEIGHT":
        target_height = data.get("height")
        if target_height is not None:
            print(f'MOVE_TO_HEIGHT: {target_height}')
            if desk_thread is None or not desk_thread.is_alive():
                desk_thread = socketio.start_background_task(locktek.move_to_height, target_height)
            result = f"Moving to height {target_height}."
        else:
            result = "Invalid height value."
    else:
        result = "Invalid command."

    emit('response', {'status': 'success', 'action': data, 'result': result, 'height': height})

# Run the server
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

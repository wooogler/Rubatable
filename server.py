from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import serial
from flexispot import LoctekMotion, SERIAL_PORT
import threading

# Flask web server setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Desk control setup
ser = serial.Serial(SERIAL_PORT, 9600, timeout=None)
locktek = LoctekMotion(ser)

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

    if data == "UP":
        print('UP')
        if desk_thread is None or not desk_thread.is_alive():
            desk_thread = socketio.start_background_task(control_desk, "up")
        result = "Raising the desk."
    elif data == "DOWN":
        print('DOWN')
        if desk_thread is None or not desk_thread.is_alive():
            desk_thread = socketio.start_background_task(control_desk, "down")
        result = "Lowering the desk."
    elif data == "STOP":
        print('STOP')
        locktek.stop()
        if desk_thread and desk_thread.is_alive():
            desk_thread.join()
            desk_thread = None
        result = "Desk movement stopped."
    elif data == "GET_HEIGHT":
        print('GET_HEIGHT')
        height = locktek.get_height()

        result = "Getting the desk height."
    else:
        result = "Invalid command."

    emit('response', {'status': 'success', 'action': data, 'result': result, 'height': height})

# Run the server
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

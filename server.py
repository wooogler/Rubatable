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
ser = serial.Serial(SERIAL_PORT, 9600, timeout=500)
locktek = LoctekMotion(ser)

desk_thread = None
stop_event = threading.Event()

def control_desk(direction):
    locktek.execute_command("wake_up")
    while not stop_event.is_set():
        locktek.move(direction)
        height = locktek.current_height()
        if height is not None:
            socketio.emit('height_update', {'height': height})
            print(f"Current Height: {height}")
        socketio.sleep(0.1)  # Use socketio.sleep instead of time.sleep

# WebSocket event handler
@socketio.on('control')
def handle_control(data):
    global desk_thread, stop_event
    
    if data == "UP":
        print('UP')
        if desk_thread is None or not desk_thread.is_alive():
            stop_event.clear()
            desk_thread = socketio.start_background_task(control_desk, "up")
        result = "Raising the desk."
    elif data == "DOWN":
        print('DOWN')
        if desk_thread is None or not desk_thread.is_alive():
            stop_event.clear()
            desk_thread = socketio.start_background_task(control_desk, "down")
        result = "Lowering the desk."
    elif data == "STOP":
        print('STOP')
        if desk_thread and desk_thread.is_alive():
            stop_event.set()
            desk_thread.join()
            desk_thread = None
        locktek.stop()
        result = "Desk movement stopped."
    else:
        result = "Invalid command."
    
    height = locktek.current_height()
    emit('response', {'status': 'success', 'action': data, 'result': result, 'height': height})

# Run the server
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
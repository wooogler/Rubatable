from flask import Flask, request
from flask_socketio import SocketIO, emit

# Flask web server setup
app = Flask(__name__)
socketio = SocketIO(app)

# Desk control functions
def control_desk_up():
    print("Desk moving up.")
    # Add the actual desk control code here

def control_desk_down():
    print("Desk moving down.")
    # Add the actual desk control code here

# WebSocket event handler
@socketio.on('control')
def handle_control(data):
    if data == "UP":
        control_desk_up()
    elif data == "DOWN":
        control_desk_down()
    emit('response', {'status': 'success', 'action': data})

# Run the server
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
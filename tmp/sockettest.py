from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room


app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('tmp.html')

@socketio.on('request night action')
def response_night_action():
    message='data received'
    target= [1,2,4]
    emit('message', {'msg': message, 'target': target})


if __name__ == '__main__':
    socketio.run(app, host='192.168.2.29', port=5000, debug=True)
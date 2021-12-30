from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import json

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)

players = [
              {"id": 0, "name": 'AAA', 'cast': '', "isActive":False},
              {"id": 1, "name": 'BBB', 'cast': '', "isActive":False},
              {"id": 2, "name": 'CCC', 'cast': '', "isActive":False},
              {"id": 3, "name": 'DDD', 'cast': '', "isActive": False},
          ],


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/player_list')
def show_list():
    return jsonify(players)


@socketio.on('chat message')
def handle_message(data):
    message = 'received message: ' + data
    print(message)
    emit('server_message', 'form server ' + message, broadcast=True)


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('server_message', username + ' さんは ' + room + ' に入室しました', to=room)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('server_message', username + ' さんは ' + room + ' から退出しました', to=room)


if __name__ == '__main__':
    socketio.run(app, host='192.168.2.29', port=5000, debug=True)

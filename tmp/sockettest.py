from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room


players = [{'name': '浩司', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': True},
                {'name': '恵', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': False},
                {'name': '太郎', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': False},
                {'name': 'ポコ', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': False}]

def pop_key(dict_list, key):
    return [dict.pop(key) for dict in dict_list]

a=pop_key(players)



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
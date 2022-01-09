from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room, send
import random

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)

players = [{'index': 0, 'name': '恵', "isActive": False, "sid": '', "isAlive": True, "isGM": False},
           {'index': 1, 'name': 'Koji', "isActive": False, "sid": '', "isAlive": True, "isGM": False},
           {'index': 2, 'name': '裕一', "isActive": False, "sid": '', "isAlive": True, "isGM": False}
           ]


class Cast:
    pass


class Villager(Cast):
    def __init__(self):
        self.name = '市民'
        self.team = 'white'
        self.color = 'white'


class Werewolf(Cast):
    def __init__(self):
        self.name = '人狼'
        self.team = 'black'
        self.color = 'black'


class FortuneTeller(Cast):
    def __init__(self):
        self.name = '占い師'
        self.team = 'white'
        self.color = 'white'


villager = Villager()
wolf = Werewolf()
fortuneTeller = FortuneTeller()
casts = [villager, wolf, fortuneTeller]


class Village:
    def __init__(self, players):
        self.players = players
        self.num = len(players)

    # キャスト決め
    def select_cast(self, casts):
        pass

    # キャストの割り当て
    def assign_cast(self, casts):
        for player, cast in zip(self.players, random.sample(casts, self.num)):
            player["cast"] = cast.name

    def is_assigned(self, sid):
        for player in self.players:
            if player['sid']==sid:
                return player
        return ''


vil = Village(players)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/player_list')
def show_list():
    return jsonify(vil.players)


@socketio.on('join')
def join(index, isActive):
    player = vil.players[index]
    player['sid'] = request.sid
    player['isActive'] = isActive
    print(vil.players)
    # room = player.get('cast')
    # join_room(room)
    emit('broadcast_message', {'players': vil.players}, broadcast=True)


# @socketio.on('candindexateGM')
# def candidateGM(index):
#     for pl in vil.players:
#         pl["isGM"] = False
#     player = vil.players[index]
#     player["isGM"] = True
#     emit('broadcast_message', {'msg': f'{player["name"]}さんはGMです', 'players': vil.players}, broadcast=True)


@socketio.on('casting')
def casting():
    vil.assign_cast(casts)
    emit('broadcast_message', {'players': vil.players}, broadcast=True)

sids=[]
@socketio.on("connect")
def connect():
    sid = request.sid
    sids.append(sid)
    player = vil.is_assigned(sid)
    emit('login', {'data': player}, room=sid)



@socketio.on("disconnect")
def disconnect():
    sid = request.sid
    sids.remove(sid)


if __name__ == '__main__':
    socketio.run(app, host='192.168.2.29', port=5000, debug=True)

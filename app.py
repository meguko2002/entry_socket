from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room, send
import random

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)


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
    def __init__(self):
        self.players = []
        self.namelist = []
        self.casts = []

    def set_players(self,namelist):
        self.namelist = [player['name'] for player in self.players]
        for name in namelist:
            if name not in self.namelist:
                self.players.append({'name': name, "isActive": False, "sid": '', "isAlive": True, "isGM": False})
        for player in self.players:
            if player['name'] not in namelist:
                self.players.remove(player)

    # キャスト決め
    def select_cast(self, casts: object):
        short_num = len(self.players)-len(casts)
        if short_num < 0:
            return -1
        self.casts = casts
        for i in range(short_num):
            self.casts.append(villager)

    # キャストの割り当て
    def assign_cast(self):
        for player, cast in zip(self.players, random.sample(self.casts, len(self.players))):
            player["cast"] = cast.name

    def is_assigned(self, sid):
        for player in self.players:
            if player['sid']==sid:
                return player
        return ''


vil = Village()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gm', methods=["GET", "POST"])
def gm():
    if request.method == "GET":
        return render_template('gm.html')
    else:
        namelist = request.get_json()['data']
        vil.set_players(namelist)
        return jsonify({'res':'サーバーに送信完了'})


@app.route('/player_list')
def show_list():
    return jsonify(vil.players)


@socketio.on('submit member')
def submit_member(namelist):
    vil.set_players(namelist)
    emit('broadcast_message', {'players': vil.players}, broadcast=True)


@socketio.on('join')
def join(index, isActive):
    player = vil.players[index]
    player['sid'] = request.sid
    player['isActive'] = isActive
    message = player['name'] + 'さん、ようこそ' if isActive else ''
    emit('personal_message', {'msg': message, 'data': player['sid']})
    emit('broadcast_message', {'players': vil.players}, broadcast=True)


# @socketio.on('candindateGM')
# def candidateGM(index):
#     for pl in vil.players:
#         pl["isGM"] = False
#     player = vil.players[index]
#     player["isGM"] = True
#     emit('broadcast_message', {'msg': f'{player["name"]}さんはGMです', 'players': vil.players}, broadcast=True)


@socketio.on('casting')
def casting():
    vil.select_cast(casts)
    vil.assign_cast()
    emit('broadcast_message', {'players': vil.players}, broadcast=True)


@socketio.on("disconnect")
def disconnect():
    sid = request.sid
    for player in vil.players:
        if player['sid'] == sid:
            player['isActive'] = False
    emit('broadcast_message', {'players': vil.players}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='192.168.2.29', port=5000, debug=True)

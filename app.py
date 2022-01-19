from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room
import random

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)


class Cast:
    def __init__(self):
        self.name = None

    def __str__(self):
        return self.name
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
        self.players = [{'name': '浩司', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': True},
                        {'name': '恵', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': False},
                        {'name': 'ポコ', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': False}]
        self.casts = []
        self.castnames = []
        self.phase = '参加受付中'

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
        random.shuffle(self.casts)
        self.castnames = [cast.name for cast in self.casts]

    def expel(self, id):
        self.players[id]['isAlive'] = False

    def judge(self):
        white_num = 0
        black_num = 0
        for player, cast in zip(self.players, self.casts):
            if player['isAlive']:
                if cast.team == 'white':
                    white_num += 1
                elif cast.team == 'black':
                    black_num += 1
        if white_num <= black_num:
            self.phase = '人狼勝利'
        elif black_num == 0:
            self.phase = '市民勝利'
        else:
            self.phase = '昼' if self.phase=='夜' else '昼'

    def reset(self):
        for player in self.players:
            player['isAlive'] = True

vil = Village()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/player_list')
def show_list():
    return jsonify(vil.players)


@socketio.on('submit member')
def submit_member(players):
    vil.players = players
    emit('message', {'players': vil.players}, broadcast=True)


@socketio.on('join')
def join(index, isActive):
    player = vil.players[index]
    player['sid'] = request.sid
    room = session.get('room')
    join_room(room)
    player['isActive'] = isActive
    message = player['name'] + 'さん、ようこそ' if isActive else ''
    emit('message', {'msg': message}, room=player['sid'])
    emit('message', {'players': vil.players}, broadcast=True)


@socketio.on('cast')
def cast():
    vil.reset()
    vil.select_cast(casts)
    vil.assign_cast()
    vil.phase = '昼'
    emit('message', {'players': vil.players, 'casts': vil.castnames, 'phase': vil.phase}, broadcast=True)
    for i, player in enumerate(vil.players):
        emit('message', {'msg': player['name']+'さんは'+vil.casts[i].name}, room=player['sid'])

@socketio.on('vote')
def vote(id):
    vil.expel(id)
    emit('message', {'msg': vil.players[id]['name']+'さんは追放されました','players': vil.players, 'phase':'夜'}, broadcast=True)

@socketio.on('judge')
def judge():
    vil.judge()
    emit('message', {'players': vil.players, 'phase': vil.phase, 'msg': vil.phase}, broadcast=True)

@socketio.on('next game')
def next_game():
    vil.reset()
    vil.phase = '参加受付中'
    emit('message', {'players': vil.players,'phase': vil.phase, 'msg': vil.phase}, broadcast=True)

@socketio.on('submit GM')
def give_gm(myindex, index):
    vil.players[myindex]['isGM'] = False
    vil.players[index]['isGM'] = True
    emit('message', {'players': vil.players}, broadcast=True)


@socketio.on('disconnect')
def disconnect():
    sid = request.sid
    # leave_room()
    for player in vil.players:
        if player['sid'] == sid:
            player['isActive'] = False
    emit('message', {'players': vil.players}, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host='192.168.2.29', port=5000, debug=True)

from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room
import random

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)


class Cast:
    def __init__(self):
        self.name = '市民'
        self.team = 'white'
        self.color = 'white'
        self.message = '夜明けまでお待ちください'
        self.has_action = False

    def __str__(self):
        return self.name


class Villager(Cast):
    pass


class Werewolf(Cast):
    def __init__(self):
        self.name = '人狼'
        self.team = 'black'
        self.color = 'black'
        self.message = '誰を襲いますか'
        self.has_action = True


class FortuneTeller(Cast):
    def __init__(self):
        self.name = '占い師'
        self.team = 'white'
        self.color = 'white'
        self.message = '誰を占いますか'
        self.has_action = True


# villager = Villager()
# wolf = Werewolf()
# fortuneTeller = FortuneTeller()
casts = [Villager(), Werewolf(), FortuneTeller()]


class Village:
    def __init__(self):
        self.players = [{'name': '浩司', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': True},
                        {'name': '恵', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': False},
                        {'name': '太郎', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': False},
                        {'name': 'ポコ', 'isActive': False, 'sid': '', 'isAlive': True, 'isGM': False}]
        self.casts = []
        self.castnames = []
        self.phase = '参加受付中'
        self.message=''


    # キャスト決め
    def select_cast(self, casts: object):
        short_num = len(self.players)-len(casts)
        if short_num < 0:
            return -1
        self.casts = casts
        for i in range(short_num):
            self.casts.append(Villager())

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
            self.message = '人狼勝利'
        elif black_num == 0:
            self.phase = '市民勝利'
            self.message = '市民勝利'
        else:
            if self.phase =='昼':
                self.phase = '夜'
                self.message = '恐ろしい夜がやってまいりました'
            else:
                self.phase ='昼'
                self.message = '夜が明けました'


    def setplayers(self, players):
        self.players = players
        for player in self.players:
            if player['isGM']:
                return
        self.players[0]['isGM']= True

    def reset(self):
        for player in self.players:
            player['isAlive'] = True

vil = Village()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/player_list')
def show_list():
    vil.reset()
    return jsonify(vil.players)


@socketio.on('submit member')
def submit_member(players):
    vil.setplayers(players)
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
    emit('message', {'msg': vil.players[id]['name']+'さんは追放されました','players': vil.players}, broadcast=True)

@socketio.on('judge')
def judge():
    vil.judge()
    emit('message', {'players': vil.players, 'phase': vil.phase, 'msg': vil.message}, broadcast=True)

@socketio.on('request night action')
def response_night_action():
    vil.phase = '深夜'
    for player_id, player in enumerate(vil.players):
        target_indices = {}
        if not player['isAlive']:     # 亡くなった方はアクション出来ない
            message = '次のゲームまでお待ちください'
            emit('message', {'msg': message, 'phase': vil.phase}, room=player['sid'])
            continue
        player_cast = vil.casts[player_id]
        message = player_cast.message
        if player_cast.has_action:
            for target_id, target_cast in enumerate(vil.casts):
                target_indices[target_id] = False
                if target_id == player_id:     # 自分自身に対してはアクション出来ない
                    target_indices[target_id] = False
                elif not vil.players[target_id]['isAlive']:  # 死んでいる人に対してはアクション出来ない
                    target_indices[target_id] = False
                elif target_cast.name == '人狼' and player_cast.name == '人狼':  # 人狼同士はアクション出来ない
                    target_indices[target_id] = False
                target_indices[target_id] =True
        emit('message', {'msg': message, 'phase': vil.phase, 'target_indices': target_indices}, room=player['sid'])

@socketio.on('do action')
def action():
    # todo ここに各役職から受け取ったactionに対する処理を記述

    for i, player in enumerate(vil.players):
        message = vil.casts[i].message  # todo ここに役職ごとのメッセージ
        indice = vil.casts[i].vote_indice  # todo ここに役職ごとの対象index
        emit('message', {'msg': message}, room=player['sid'])

    # todo もし全員のactionが完了したら
    judge() # 夜明けor勝敗判定と、playersの状態を全員に告げる


@socketio.on('next game')
def next_game():
    vil.reset()
    vil.phase = '参加受付中'
    emit('message', {'players': vil.players,'phase': vil.phase, 'msg': vil.message}, broadcast=True)


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

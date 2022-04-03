# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room
import random
import pandas as pd

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)

players = [{'name': '山口', 'isAlive': True, 'isGM': True, 'sid': ''},
           {'name': '太郎', 'isAlive': True, 'isGM': False, 'sid': ''},
           {'name': 'じろ', 'isAlive': True, 'isGM': False, 'sid': ''},
           {'name': '三郎', 'isAlive': True, 'isGM': False, 'sid': ''},
           {'name': '史郎', 'isAlive': True, 'isGM': False, 'sid': ''},
           {'name': 'ポコ', 'isAlive': True, 'isGM': False, 'sid': ''}]


class Game:
    def __init__(self, pls):
        self.df = pd.DataFrame(pls)
        self.players = pls
        self.casts = [{'name': '人狼', 'team': 'black', 'color': 'black'},
                      {'name': '占い師', 'team': 'white', 'color': 'white'},
                      {'name': '騎士', 'team': 'white', 'color': 'white'},
                      {'name': '狂人', 'team': 'black', 'color': 'white'},
                      {'name': '狂信者', 'team': 'black', 'color': 'white'},
                      {'name': '市民', 'team': 'white', 'color': 'white'},
                      ]
        self.phase = '参加受付中'
        self.dead_players = []
        self.cast_menu = {"人狼": 2, "占い師": 0, "騎士": 0, "狂人": 0, "狂信者": 0, "市民": 0}
        self.ranshiro = True
        self.renguard = False  # True: 連ガード有り
        self.target_list = []
        # [[],[2,3],[],[4],[]] 左の例だと、id2と3の人狼が襲撃候補としてid=1の人を提出している
        self.wolves = []
        self.citizens = []

    def count_suv_wolf(self):
        count = 0
        for p in self.wolves:
            count += p['isAlive']
        return count

    def count_suv_whites(self):
        count = 0
        for p in self.citizens:
            count += p['isAlive']
        return count

    @property
    def players_for_player(self):  # 配布用players（castは送らない）
        send_keys = ['name', 'isAlive', 'isGM', 'sid']
        return [{key: p[key] for key in send_keys} for p in players]

    def select_cast(self):
        gamecasts = []
        for castname, num in self.cast_menu.items():
            for i in range(num):
                gamecasts.append([x for x in self.casts if x['name'] == castname][0])
        gamecasts = random.sample(gamecasts, len(self.players))
        for player, cast in zip(self.players, gamecasts):
            player['cast'] = cast

    def set_team(self):
        self.citizens = [player for player in self.players if player['cast']['color'] == 'white']
        self.wolves = [player for player in self.players if player['cast']['color'] == 'black']

    def win_judge(self):
        suv_wolf_num = self.count_suv_wolf()
        suv_whites_num = self.count_suv_whites()
        if suv_wolf_num == 0:
            self.phase = '市民勝利'
            return '市民勝利'
        elif suv_whites_num <= suv_wolf_num:
            self.phase = '人狼勝利'
            return '人狼勝利'
        else:
            if self.phase == '昼':
                self.phase = '夜'
                return '夜がきました'
            else:
                self.phase = '昼'
                if not self.dead_players:
                    message = '昨晩、襲撃された方は、いませんでした'
                else:
                    p_names = 'と、'.join([player['name'] for player in self.dead_players])
                    message = '昨晩、' + p_names + 'が襲撃されました'
                self.dead_players = []
                return message

    def search_player(self, sid):
        for index, player in enumerate(self.players):
            if player['sid'] == sid:
                return index, player
        return False

    def judge_casts_action(self):
        self.dead_players = []
        for player in self.players:
            # GJ出なければplayerは被襲撃
            if player['isAlive']:
                if player.get('is_targeted') and not player.get('is_protected'):
                    player['isAlive'] = False
                    self.dead_players.append(player)
            player['is_targeted'] = False

    def player_reset(self):
        for player in self.players:
            player['isAlive'] = True
            player['cast'] = None

    def cast_reset(self):
        self.wolves.clear()
        self.citizens.clear()

    def set_cast_menu(self, cast_menu=None):
        if cast_menu is not None:
            self.cast_menu = cast_menu
        # 市民以外の員数を数えてcast_sumに代入
        cast_sum = 0
        for castname, num in self.cast_menu.items():
            if castname == '市民':
                continue
            cast_sum += int(num)
        # player員数から市民（特殊役でないcast)の員数を計算
        vil_num = len(game.players) - cast_sum
        if vil_num >= 0:
            self.cast_menu['市民'] = vil_num


game = Game(players)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/player_list')
def show_list():
    game.set_cast_menu()
    return jsonify({'phase': game.phase,
                    'players': game.players_for_player,
                    'castMenu': game.cast_menu,
                    'ranshiro': game.ranshiro,
                    'renguard': game.renguard
                    })


@socketio.on('submit member')
def submit_member(players, cancel_players):
    # 参加者キャンセルのため、各参加者のIDを振りなおす
    game.players = [player for player in players if not player['name'] in cancel_players]
    game.set_cast_menu()
    emit('message', {'players': game.players_for_player, 'castMenu': game.cast_menu}, broadcast=True)


@socketio.on('join')
def join(index):
    player = game.players[int(index)]
    player['sid'] = request.sid
    message = player['name'] + 'さん、ようこそ'
    emit('message', {'msg': message, 'mysid': player['sid']}, room=player['sid'])
    emit('message', {'players': game.players_for_player}, broadcast=True)


# リロード対応
@socketio.on('reload')
def rejoin(name):
    sid = request.sid
    for player in game.players:
        if player['name'] == name:
            player['sid'] = sid
            emit('message', {'players': game.players_for_player}, room=player['sid'])
            break
    else:
        print('合致するsidなし')


# 参加ボタンを2度押し、ゲーム参加をキャンセルする
@socketio.on('decline')
def decline():
    sid = request.sid
    for player in game.players:
        if player['sid'] == sid:
            player['sid'] = ''
    emit('message', {'players': game.players_for_player}, broadcast=True)


@socketio.on('set renguard')
def set_renguard(renguard):
    game.renguard = renguard
    emit('message', {'renguard': game.renguard}, broadcast=True)


@socketio.on('set ranshiro')
def set_ranshiro(ranshiro):
    game.ranshiro = ranshiro
    emit('message', {'ranshiro': game.ranshiro}, broadcast=True)


@socketio.on('assign cast')
def assign_cast(cast_menu):
    game.cast_menu = cast_menu
    game.phase = '昼'
    game.player_reset()
    game.cast_reset()
    # キャストの割り当て
    game.select_cast()
    game.set_team()

    # playerごとにキャストリストopencastsを送る
    for player in game.players:
        if player['cast']['name'] in ['人狼', '狂信者']:  # 送り先が人狼または狂信者だったら
            player['opencasts'] = ['人狼' if p['cast']['name'] == '人狼' else '' for p in game.players]

        elif (player['cast']['name'] == '占い師') and game.ranshiro:
            player['opencasts'] = [player['cast']['name'] if p == player else '' for p in game.players]
            if game.ranshiro:
                ranshiro_players = random.sample(game.citizens,2)
                ranshiro_player = ranshiro_players[0] if ranshiro_players[0] != player else ranshiro_players[1]
                for i,p in enumerate(game.players):
                    if p == ranshiro_player:
                        player['opencasts'][i] ='人狼ではない'
                        break
        else:
            player['opencasts'] = [player['cast']['name'] if p == player else '' for p in game.players]

        message = player['name'] + 'は' + player['cast']['name']
        emit('message',
             {'players': game.players_for_player, 'phase': game.phase, 'msg': message,
              'opencasts': player['opencasts']},
             room=player['sid'])


@socketio.on('vote')
def vote(index):
    game.players[index]['isAlive'] = False
    emit('message', {'msg': game.players[index]['name'] + 'は追放されました', 'players': game.players_for_player},
         broadcast=True)


@socketio.on('judge')
def judge():
    message = game.win_judge()
    game.target_list = []
    emit('message', {'players': game.players_for_player, 'phase': game.phase,
                     'msg': message, 'target_list': game.target_list}, broadcast=True)


@socketio.on('request action from gm')
def response_action():
    game.phase = '深夜'
    for player in game.players:
        if not player.get('isAlive', False):
            player['done_action'] = True
            message = '次のゲームまでお待ちください'
            emit('message', {'msg': message, 'phase': game.phase}, room=player['sid'])
        else:
            if player['cast']['name'] in ['人狼']:
                player['done_action'] = False
                player['target_id'] = None
                target_candidates = []
                for p in game.players:
                    if p == player or not p['isAlive']:
                        target_candidates.append(False)
                    elif p in game.wolves:
                        target_candidates.append(False)
                    else:
                        target_candidates.append(True)
                message = '誰を襲いますか'
            elif player['cast']['name'] in ['占い師']:
                player['done_action'] = False
                target_candidates = [False if p == player or not p['isAlive'] else True for p in
                                     game.players]
                message = '誰を占いますか'
            elif player['cast']['name'] in ['騎士']:
                player['done_action'] = False
                target_candidates = []
                for p in game.players:
                    if p == player:
                        target_candidates.append(False)
                    elif not p.get('isAlive', False):
                        target_candidates.append(False)
                    elif not game.renguard:  # もし連続ガード禁止だったら前の晩に守られていた場合は護衛候補にならない
                        target_candidates.append(not p.get('is_protected', False))
                    else:
                        target_candidates.append(True)
                message = '誰を守りますか'

            else:
                player['done_action'] = True
                target_candidates = [False for p in game.players]
                message = '夜明けまでお待ちください'
            emit('message', {'msg': message, 'phase': game.phase, 'target_candidates': target_candidates},
                 room=player['sid'])


@socketio.on('do action')
def action(target_index):
    my_index, player = game.search_player(request.sid)
    if not player['done_action']:
        # if player['cast']['name'] in ['人狼', ]:
        if player in game.wolves:
            message = '誰を襲いますか'
            player['target_id'] = target_index
            # 人狼全員のtargetを洗い出してtarget_list を作成
            # target_list = [[],[2,3],[],[4],[]] 左の例だと、id2と3の人狼が襲撃候補としてid=1の人を提出している
            game.target_list = [[] for p in game.players]
            suv_wolf_num = game.count_suv_wolf()  # wolf生存者数を計算
            for player in game.wolves:
                target_id = player.get('target_id', None)
                if target_id is not None:
                    game.target_list[target_id].append(player['name'])
                    # ターゲット候補が一人に絞れていたらwolf間でターゲットが合意とみなす
                    if len(game.target_list[target_id]) == suv_wolf_num:
                        game.players[target_index]['is_targeted'] = True
                        message = '襲撃先は' + game.players[target_index]['name']
                        for player in game.wolves:
                            player['done_action'] = True
                        break
            for player in game.wolves:
                emit('message', {'msg': message, 'target_list': game.target_list}, room=player['sid'])

        elif player['cast']['name'] in ['占い師', ]:
            if game.players[target_index]['cast']['name'] == '人狼':
                comment = '人狼'
            else:
                comment = '人狼ではない'
            player['opencasts'][target_index] = comment
            message = game.players[target_index]['name'] + 'は' + comment
            player['done_action'] = True
            emit('message', {'msg': message, 'opencasts': player['opencasts']}, room=player['sid'])

        elif player['cast']['name'] in ['騎士']:
            game.players[target_index]['is_protected'] = True
            message = game.players[target_index]['name'] + 'を護衛します'
            player['done_action'] = True
            emit('message', {'msg': message}, room=player['sid'])

    # 全員のactionが完了した後の処理
    for player in game.players:
        if not player['done_action']:
            return
    game.judge_casts_action()  # 全てのcastのアクションから全体の判定
    game.phase = '朝'
    message = '夜のアクションが終了しました'
    emit('message', {'phase': game.phase, 'msg': message}, broadcast=True)


@socketio.on('next game')
def next_game():
    game.player_reset()
    game.cast_reset()
    game.phase = '参加受付中'
    message = '参加受付中'
    emit('message', {'players': game.players_for_player, 'phase': game.phase, 'opencasts': '', 'msg': message},
         broadcast=True)


@socketio.on('submit GM')
def submit_gm(myindex, index):
    game.players[myindex]['isGM'] = False
    game.players[int(index)]['isGM'] = True
    emit('message', {'players': game.players_for_player}, broadcast=True)


@socketio.on('change cast')
def change_cast(new_menu):
    game.set_cast_menu(new_menu)
    emit('message', {'castMenu': game.cast_menu}, broadcast=True)


@socketio.on('disconnect')
def disconnect():
    sid = request.sid
    for id, player in enumerate(game.players):
        if player.get('sid') == sid:
            player['sid'] = ''
            break


if __name__ == '__main__':
    socketio.run(app, host='localhost', debug=True)

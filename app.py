# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room
import random
import json
import pandas as pd

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)


# class Cast:
#
#     def __init__(self):
#         self.name = '市民'
#         self.team = 'white'
#         self.color = 'white'
#         self.gm_message = '夜明けまでお待ちください'
#         # self.done_action = False
#         # self.isAlive = True
#         # self.is_targeted = False
#         # self.is_protected = False
#         # self.target = None
#         self.id = None
#
#     def __str__(self):
#         return self.name
#
#
# class Villager(Cast):
#     def __init__(self):
#         super().__init__()
#
#
# class Werewolf(Cast):
#
#     def __init__(self):
#         super().__init__()
#         self.name = '人狼'
#         self.team = 'black'
#         self.color = 'black'
#         self.gm_message = '誰を襲いますか'
#
#
# class FortuneTeller(Cast):
#     def __init__(self):
#         super().__init__()
#         self.name = '占い師'
#         self.team = 'white'
#         self.color = 'white'
#         self.gm_message = '誰を占いますか'
#
#
# class Knight(Cast):
#     def __init__(self):
#         super().__init__()
#         self.name = '騎士'
#         self.team = 'white'
#         self.color = 'white'
#         self.gm_message = '誰を護衛しますか'
#
#
# class Madman(Cast):
#     def __init__(self):
#         super().__init__()
#         self.name = '狂人'
#         self.team = 'black'
#         self.color = 'white'
#
#
# class Fanatic(Cast):
#     def __init__(self):
#         super().__init__()
#         self.name = '狂信者'
#         self.team = 'black'
#         self.color = 'white'


players = [{'name': '山口', 'isAlive': True, 'sid': '', 'isGM': True},
           {'name': '太郎', 'isAlive': True, 'sid': '', 'isGM': False},
           {'name': 'じろ', 'isAlive': True, 'sid': '', 'isGM': False},
           {'name': '三郎', 'isAlive': True, 'sid': '', 'isGM': False},
           {'name': '史郎', 'isAlive': True, 'sid': '', 'isGM': False},
           {'name': 'ポコ', 'isAlive': True, 'sid': '', 'isGM': False}]



def _count_survivor(pls):
    count = 0
    for p in pls:
        if p['isAlive']:
            count += 1
    return count


def calc_villager(new_cast_num):
    cast_sum = 0
    for cast in new_cast_num:
        cast_sum += int(cast['num'])


class Game:
    def __init__(self, pls):
        self.df = pd.DataFrame(pls)
        self.players = pls
        self.casts =[{'name': '人狼', 'team': 'black', 'color': 'black'},
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
        self.suv_wolf_num = 0
        self.suv_whites_num = 0

    def set_suv_wolf_num(self):
        self.suv_wolf_num = _count_survivor(self.wolves)

    def set_suv_whites_num(self):
        self.suv_whites_num = _count_survivor(self.citizens)

    @property
    def players_for_player(self):  # 配布用players（castは送らない）
        send_list = []
        send_keys = ['name', 'isAlive', 'isGM', 'sid']
        for p in self.players:
            send_player = {}
            for key in send_keys:
                send_player[key] = p.get(key)
            send_list.append(send_player)
        return send_list

    # キャスト決め
    # todo: いちいちcastnameを見に行かないでmapとかで上手くやる。これでは新役職追加に対応できない
    def select_cast(self):
        gamecasts = []
        for castname, num in self.cast_menu.items():
            for i in range(num):
                gamecasts.append([x for x in self.casts if x['name'] == castname][0])
        for player, cast in zip(self.players, gamecasts):
            player['cast'] = cast

    def set_team(self):
        self.citizens = [player for player in self.players if player['cast']['color'] == 'white']
        self.wolves = [player for player in self.players if player['cast']['color'] == 'white']

    #     castnames=[]
    #     for castname, num in self.cast_menu.items():
    #         for i in range(num):
    #             castnames.append(castname)
    #     self.casts = []
    #     for castname in castnames:
    #         if castname == '人狼':
    #             self.casts.append(Werewolf())
    #         elif castname == '占い師':
    #             self.casts.append(FortuneTeller())
    #         elif castname == '騎士':
    #             self.casts.append(Knight())
    #         elif castname == '狂人':
    #             self.casts.append(Madman())
    #         elif castname == '狂信者':
    #             self.casts.append(Fanatic())
    #         else:  # 残りは市民とみなす
    #             self.casts.append(Villager())

    # def expel(self, index):
    #     self.players[index]['isAlive'] = False
        # cast = self.casts[index]
        # cast.isAlive = False

    def win_judge(self):
        self.set_suv_wolf_num()
        self.set_suv_whites_num()
        if self.suv_wolf_num == 0:
            self.phase = '市民勝利'
            return '市民勝利'
        elif self.suv_whites_num <= self.suv_wolf_num:
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
        for id, player in enumerate(self.players):
            # GJ出なければcastは襲撃
            if player['isAlive']:
                if player.get('is_targeted') and not player.get('is_protected'):
                    player['isAlive'] = False
                    self.dead_players.append(player)
            player['is_targeted'] = False
        for player in self.dead_players:
            player['isAlive'] = False

    def player_reset(self):
        for player in self.players:
            player['isAlive'] = True
            player['cast'] = None

    def cast_reset(self):
        # self.casts.clear()
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


@socketio.on('set ranshiro')
def set_ranshiro(ranshiro):
    game.ranshiro = json.loads(ranshiro)  # jsonで帰ってくる"true"は文字列なのでpythonのboolであるTrueに変換
    emit('message', {'ranshiro': ranshiro}, broadcast=True)


@socketio.on('set renguard')
def set_renguard(renguard):
    game.renguard = json.loads(renguard)
    emit('message', {'renguard': renguard}, broadcast=True)


@socketio.on('assign cast')
def assign_cast(cast_menu):
    game.cast_menu = cast_menu
    game.phase = '昼'
    game.player_reset()
    game.cast_reset()
    # キャストの割り当て
    game.select_cast()
    game.set_team()
    # random.shuffle(game.casts)

    # for player, cast in zip(game.players, game.casts):
    #     player['cast'] = cast
    #     if cast.name == '人狼':
    #         game.wolves.append(player)
    #     elif cast.color == 'white':
    #         game.citizens.append(player)

    # playerごとにキャストリストopencastsを送る
    for player in game.players:
        if player['cast']['name'] in ['人狼', '狂信者']:  # 送り先が人狼または狂信者だったら
            player['opencasts'] = ['人狼' if p['cast']['name'] == '人狼' else '' for p in game.players]

        elif player['cast']['name'] == '占い師' and game.ranshiro:
            ranshiro_player = random.choice(game.citizens)
            player['opencasts'] = []
            for p in game.players:
                if p == player:
                    player['opencasts'].append(player['cast']['name'])
                elif p == ranshiro_player:
                    player['opencasts'].append('人狼ではない')
                else:
                    player['opencasts'].append(False)
        else:
            player['opencasts'] = [player['cast']['name'] if p == player else '' for p in game.players]

        message = player['name'] + 'は' + player['cast']['name']
        emit('message',
             {'players': game.players_for_player, 'phase': game.phase, 'msg': message, 'opencasts': player['opencasts']},
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
                target_candidates = [False if p == player or (not p.get('isAlive', False)) else True for p in game.players]
                message = '誰を占いますか'
            elif player['cast']['name'] in ['騎士']:
                player['done_action'] = False
                target_candidates = []
                for p in game.players:
                    if p == player:
                        target_candidates.append(False)
                    elif not p.get('isAlive',False):
                        target_candidates.append(False)
                    elif not game.renguard: # もし連続ガード禁止だったら前の晩に守られていた場合は護衛候補にならない
                        if p.get('is_protected', False):
                            target_candidates.append(False)
                    else:
                        target_candidates.append(True)
                message = '誰を守りますか'

            else:
                player['done_action'] = True
                target_candidates = [False for p in game.players]
                message = '夜明けまでお待ちください'
            # message = player['cast'].gm_message
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
            game.set_suv_wolf_num()  # wolf生存者数を計算
            for player in game.wolves:
                target_id = player.get('target_id', None)
                if target_id is not None:
                    game.target_list[target_id].append(player['name'])
                    # ターゲット候補が一人に絞れていたらwolf間でターゲットが合意とみなす
                    if len(game.target_list[target_id]) == game.suv_wolf_num:
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

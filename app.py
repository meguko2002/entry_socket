# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request,url_for
from flask_socketio import SocketIO, emit
import random
import pandas as pd

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
# app.add_url_rule('/favicon.ico',redirect_to=url_for('static', filename='favicon.ico'))
socketio = SocketIO(app)

players = [{'name': 'さなえ', 'isAlive': True, 'isGM': True, 'sid': '', 'opencast': {}},
           {'name': 'かのん', 'isAlive': True, 'isGM': False, 'sid': '', 'opencast': {}},
           {'name': 'カイ', 'isAlive': True, 'isGM': False, 'sid': '', 'opencast': {}},
           {'name': 'ゆうき', 'isAlive': True, 'isGM': False, 'sid': '', 'opencast': {}},
           {'name': 'かずまさ', 'isAlive': True, 'isGM': False, 'sid': '', 'opencast': {}},
           {'name': '所', 'isAlive': True, 'isGM': False, 'sid': '', 'opencast': {}},
           {'name': 'マミコ', 'isAlive': True, 'isGM': False, 'sid': '', 'opencast': {}},
           {'name': 'きよえ', 'isAlive': True, 'isGM': False, 'sid': '', 'opencast': {}},
           ]


class Game:
    def __init__(self, pls):
        self.df = pd.DataFrame(pls)
        self.players = pls
        self.casts = [{'name': '人狼', 'team': 'black', 'color': 'black'},
                      {'name': '占い師', 'team': 'white', 'color': 'white'},
                      {'name': '騎士', 'team': 'white', 'color': 'white'},
                      {'name': '霊媒師', 'team': 'white', 'color': 'white'},
                      {'name': '狂人', 'team': 'black', 'color': 'white'},
                      {'name': '狂信者', 'team': 'black', 'color': 'white'},
                      {'name': '市民', 'team': 'white', 'color': 'white'},
                      ]
        self.phase = '参加受付中'
        self.dead_players = []
        self.cast_menu = {"人狼": 2, "占い師": 1, "騎士": 1, "霊媒師": 0, "狂人": 1, "狂信者": 0, "市民": 0}
        self.ranshiro = True
        self.renguard = False  # True: 連ガード有り
        self.wolf_target = {}
        # [[],[2,3],[],[4],[]] 左の例だと、id2と3の人狼が襲撃候補としてid=1の人を提出している
        self.wolves = []
        self.citizens = []
        self.outcast = None  # 追放者

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
        return [{key: p[key] for key in send_keys} for p in self.players]

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

    def judge_casts_action(self):
        self.dead_players = []
        for player in self.players:
            # GJ出なければplayerは被襲撃
            if player['isAlive']:
                if player.get('is_targeted'):
                    if player.get('is_protected'):
                        player['is_protected'] = False
                    else:  # 生存していて且つ襲撃されて且つ護衛されていないときに限り襲撃貫通
                        player['isAlive'] = False
                        self.dead_players.append(player)
                    player['is_targeted'] = False

    def player_reset(self):
        for player in self.players:
            player['isAlive'] = True
            player['cast'] = None
            player['opencast'].clear()

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


    def player_obj(self, name):
        return [p for p in self.players if p['name'] == name][0]

    def search_player(self, sid):
        return [p for p in self.players if p['sid'] == sid][0]

    def get_wolf_target(self):
        target_dict = {}
        for p in self.players:
            ws = p.get('targetedby')
            if ws:
                target_dict[p['name']] = [w['name'] for w in ws]
        return target_dict

def target_set(wolf, target):
    pre_target = wolf.get('target')
    if pre_target:
        pre_target['targetedby'].remove(wolf)

    targetedby = target.get('targetedby')
    if targetedby:
        target['targetedby'].append(wolf)
    else:
        target['targetedby'] = [wolf]
    wolf['target'] = target
    return True


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

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@socketio.on('submit member')
def submit_member(add_players, cancel_players):
    # 参加者キャンセルのため、各参加者のIDを振りなおす
    game.players = [player for player in game.players if not player['name'] in cancel_players]
    for name in add_players:
        game.players.append({'name': name, 'isAlive': True, 'isGM': False, 'sid': '', 'opencast': {}})
    game.set_cast_menu()
    tmp = game.players_for_player
    emit('message', {'players': tmp, 'castMenu': game.cast_menu}, broadcast=True)


@socketio.on('join')
def join(name):
    player = game.player_obj(name)
    player['sid'] = request.sid
    message = player['name'] + 'さん、ようこそ'
    emit('message', {'msg': message, 'mysid': player['sid']}, room=player['sid'])
    emit('message', {'players': game.players_for_player}, broadcast=True)


# リロード対応
@socketio.on('reload')
def rejoin(name):
    sid = request.sid
    for player in game.players:
        if player.get('name') == name:
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
        if player.get('sid') == sid:
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
    game.outcast = None
    # キャストの割り当て
    game.select_cast()
    game.set_team()

    # playerごとにキャストリストopencastを送る
    for player in game.players:
        player['opencast'][player['name']] = player['cast']['name']
        if player['cast']['name'] in ['人狼', '狂信者']:  # 送り先が人狼または狂信者だったら
            for i, p in enumerate(game.players):
                if p['cast']['name'] == '人狼':
                    player['opencast'][p['name']] = '人狼'

        elif (player['cast']['name'] == '占い師') and game.ranshiro:
            ranshiro_players = random.sample(game.citizens, 2)
            ranshiro_player = ranshiro_players[0] if ranshiro_players[0] != player else ranshiro_players[1]
            for i, p in enumerate(game.players):
                if p == ranshiro_player:
                    player['opencast'][p['name']] = '人狼ではない'
                    break

        message = player['name'] + 'は' + player['cast']['name']
        emit('message',
             {'players': game.players_for_player, 'phase': game.phase, 'msg': message,
              'opencast': player['opencast']},
             room=player['sid'])


@socketio.on('vote')
def vote(name):
    game.outcast = game.player_obj(name)
    game.outcast['isAlive'] = False
    emit('message', {'msg': game.outcast['name'] + 'は追放されました', 'players': game.players_for_player},
         broadcast=True)


@socketio.on('judge')
def judge():
    message = game.win_judge()
    game.wolf_target.clear()
    emit('message', {'players': game.players_for_player, 'phase': game.phase,
                     'msg': message, 'wolf_target': game.wolf_target}, broadcast=True)


@socketio.on('offer choices')
def offer_choices():
    game.phase = '深夜'
    for player in game.players:
        player['objects'] = []
        if not player.get('isAlive'):
            message = '次のゲームまでお待ちください'
            player['doing_action'] = False

        else:
            if player in game.wolves:
                message = '誰を襲いますか'
                player['doing_action'] = True
                player['target'] = None
                for p in game.players:
                    if p['isAlive'] and not (p in game.wolves):
                        player['objects'].append(p['name'])
            elif player['cast']['name'] in ['占い師']:
                message = '誰を占いますか'
                player['doing_action'] = True
                for p in game.players:
                    if p['isAlive'] and not (p == player):
                        player['objects'].append(p['name'])
            elif player['cast']['name'] in ['騎士']:
                player['doing_action'] = True
                for p in game.players:
                    if p['isAlive'] and not (p == player):
                        # 連続ガードなしで前の晩守られていた場合は次の護衛候補対象外
                        if not game.renguard and p == player.get('last_protect'):
                            continue
                        player['objects'].append(p['name'])
                message = '誰を守りますか'
            elif player['cast']['name'] in ['霊媒師']:
                # todo 前の昼追放された人が人狼か否かを伝える
                if game.outcast in game.wolves:
                    message = game.outcast['name'] + 'は人狼だった。\n夜明けまでお待ちください'
                    player['opencast'][game.outcast['name']] = '人狼'
                else:
                    message = game.outcast['name'] + 'は人狼ではなかった。\n夜明けまでお待ちください'
                    player['opencast'][game.outcast['name']] = '人狼ではない'
                player['doing_action'] = False
            else:
                message = '夜明けまでお待ちください'
                player['doing_action'] = False
        emit('message', {'msg': message, 'phase': game.phase, 'objects': player['objects'],
                         'opencast': player['opencast']}, room=player['sid'])


@socketio.on('do action')
def action(name):
    player = game.search_player(request.sid)
    object = game.player_obj(name)
    if player['doing_action']:
        if player in game.wolves:
            message = '誰を襲いますか'
            target_set(player, object)
            game.wolf_target = game.get_wolf_target()
            """wolf_target = {  target_name:[wolf_name,wolf_name],
                                target_name:[wolf_name,],}            """
            posted_wolves = [w['name'] for w in game.wolves if w.get('target') is not None]
            if len(posted_wolves) == game.count_suv_wolf(): # 狼全員の投票しており
                if len(game.wolf_target) == 1: # 狼全員の投票が一人のターゲットになった時、合意
                    object['is_targeted'] = True
                    message = '襲撃先は' + object['name']
                    for w in game.wolves:
                        w['doing_action'] = False
                        w['target'] = None
                    object['targetedby'] = None

            for p in game.wolves:
                emit('message', {'msg': message, 'wolf_target': game.wolf_target}, room=p['sid'])

        elif player['cast']['name'] in ['占い師', ]:
            if object['cast']['name'] == '人狼':
                comment = '人狼'
            else:
                comment = '人狼ではない'
            player['opencast'][object['name']] = comment
            message = object['name'] + 'は' + comment
            player['doing_action'] = False
            emit('message', {'msg': message, 'opencast': player['opencast'], 'objects': []},
                 room=player['sid'])

        elif player['cast']['name'] in ['騎士']:
            object['is_protected'] = True
            player['last_protect'] = object
            message = object['name'] + 'を護衛します'
            player['doing_action'] = False
            emit('message', {'msg': message, 'objects': []}, room=player['sid'])

    # 全員のactionが完了した後の処理
    for player in game.players:
        if player['doing_action']:
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
    emit('message', {'players': game.players_for_player, 'phase': game.phase, 'opencast': '', 'msg': message},
         broadcast=True)


@socketio.on('submit GM')
def submit_gm(name):
    for player in game.players:
        player['isGM'] = False
    player = game.player_obj(name)
    player['isGM'] = True
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
    # socketio.run(app, host='0.0.0.0', debug=True)

# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit,join_room, leave_room
import random
import pandas as pd

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)

players = [{'name': 'さなえ', 'isActive': False, 'isAlive': True, 'isGM': True,  'opencast': {}},
           {'name': 'かのん', 'isActive': False, 'isAlive': True, 'isGM': False,  'opencast': {}},
           {'name': 'カイ', 'isActive': False, 'isAlive': True, 'isGM': False, 'opencast': {}},
           {'name': 'ゆうき', 'isActive': False, 'isAlive': True, 'isGM': False,  'opencast': {}},
           {'name': 'かずまさ', 'isActive': False, 'isAlive': True, 'isGM': False, 'opencast': {}},
           {'name': '所', 'isActive': False, 'isAlive': True, 'isGM': False, 'opencast': {}},
           {'name': 'マミコ', 'isActive': False, 'isAlive': True, 'isGM': False, 'opencast': {}},
           {'name': 'きよえ', 'isActive': False, 'isAlive': True, 'isGM': False, 'opencast': {}},
           ]

REGURATION = {4: {'cast_menu': {"人狼": 1, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 0,"狂信者":0, "市民": 1},
                  'ranshiro': True, 'renguard': False, 'castmiss': 1},
              5: {'cast_menu': {"人狼": 1, "狂人": 1, "占い師": 1, "騎士": 1,"霊媒師": 0,"狂信者":0,  "市民": 2},
                  'ranshiro': True, 'renguard': False, 'castmiss': 1},
              6: {'cast_menu': {"人狼": 1, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 0,"狂信者":0, "市民": 3},
                  'ranshiro': True, 'renguard': False, 'castmiss': 1},
              7: {'cast_menu': {"人狼": 2, "狂人": 0, "占い師": 1,  "騎士": 1,"霊媒師": 0,"狂信者":0,  "市民": 3},
                  'ranshiro': True, 'renguard': False, 'castmiss': 1},
              8: {'cast_menu': {"人狼": 2, "狂人": 0, "占い師": 1, "騎士": 1,"霊媒師": 0,"狂信者":0,  "市民": 4},
                  'ranshiro': True, 'renguard': False, 'castmiss': 1},
              9: {'cast_menu': {"人狼": 2, "狂人": 1, "占い師": 1, "騎士": 1,"霊媒師": 0,"狂信者":0,  "市民": 3},
                  'ranshiro': True, 'renguard': False, 'castmiss': 0}
              }

CASTS = [{'name': '人狼', 'team': 'black', 'color': 'black'},
         {'name': '占い師', 'team': 'white', 'color': 'white'},
         {'name': '騎士', 'team': 'white', 'color': 'white'},
         {'name': '霊媒師', 'team': 'white', 'color': 'white'},
         {'name': '狂人', 'team': 'black', 'color': 'white'},
         {'name': '狂信者', 'team': 'black', 'color': 'white'},
         {'name': '市民', 'team': 'white', 'color': 'white'},
         ]


class Game:
    def __init__(self, pls):
        self.df = pd.DataFrame(pls)
        self.players = pls
        self.casts = CASTS
        self.phase = '参加受付中'
        self.dead_players = []
        self.cast_menu = REGURATION[len(pls)]['cast_menu']
        self.ranshiro = REGURATION[len(pls)]['ranshiro']
        self.renguard = REGURATION[len(pls)]['renguard']
        self.castmiss = REGURATION[len(pls)]['castmiss']  # True: 役職欠けあり
        self.wolf_target = {}
        self.wolves = []
        self.citizens = []
        self.outcast = None  # 追放者

    @property
    def players_for_player(self):  # 配布用players（castは送らない）
        send_keys = ['name','isActive', 'isAlive', 'isGM']
        res_players=[]
        for p in self.players:
            p_select={}
            for key in send_keys:
                p_select[key] = p.get(key)
            res_players.append(p_select)
        return res_players
        # return [{key: p[key] for key in send_keys} for p in self.players]

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

    def select_cast(self):
        basecasts = []
        for castname, num in self.cast_menu.items():
            for i in range(num):
                basecasts.append(castname)
        # 人狼が役の中に必ず含まれていること（役欠け対応）
        while True:
            gamecasts = random.sample(basecasts, len(self.players))
            if '人狼' in gamecasts:
                break
        for player, castname in zip(self.players, gamecasts):
            player['cast'] = [cast for cast in self.casts if cast['name'] == castname][0]

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

    def set_cast_menu(self, submitted_menu=None):
        if submitted_menu is None:
            submitted_menu = self.cast_menu
        # 市民以外の員数を数えてcast_sumに代入
        non_villager_num = 0
        for castname, num in submitted_menu.items():
            if castname == '市民':
                continue
            non_villager_num += int(num)
        # ゲーム不成立条件（市民の数が負になる）
        if non_villager_num > len(game.players) + self.castmiss:
            return
        else:
            self.cast_menu = submitted_menu
            self.cast_menu['市民'] = len(game.players) - non_villager_num + self.castmiss

    def suggest_cast_menu(self):
        self.cast_menu = REGURATION[len(self.players)]['cast_menu']
        self.ranshiro = REGURATION[len(self.players)]['ranshiro']
        self.renguard = REGURATION[len(self.players)]['renguard']
        self.castmiss = REGURATION[len(self.players)]['castmiss']  # True: 役職欠けあり

    def player_obj(self, name):
        for p in self.players:
            if p['name'] == name:
                return p
        return None

    def restruct_players(self, add_names, del_names):
        new_players=[]
        for p in self.players:
            if p['name'] not in del_names:
                new_players.append(p)
        for name in add_names:
            new_player = {'name': name, 'isActive': False, 'isAlive': True, 'isGM': False, 'opencast': {}}
            new_players.append(new_player)
        self.players =new_players

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
    return jsonify({'phase': game.phase,
                    'players': game.players_for_player,
                    'castMenu': game.cast_menu,
                    'ranshiro': game.ranshiro,
                    'renguard': game.renguard,
                    'castmiss': game.castmiss,
                    })


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


@socketio.on('submit member')
def submit_member(add_names, del_names):
    game.restruct_players(add_names, del_names)
    game.suggest_cast_menu()
    emit_players = game.players_for_player
    emit('message', {'players': emit_players, 'castMenu': game.cast_menu,'ranshiro': game.ranshiro,'renguard': game.renguard,'castmiss': game.castmiss}, broadcast=True)


@socketio.on('join')
def join(name):
    player = game.player_obj(name)
    player['isActive'] = True
    join_room(name)
    player['message'] = player['name'] + 'さん、ようこそ'
    emit('message', {'msg': player['message']}, to=player['name'])
    emit('message', {'players': game.players_for_player}, broadcast=True)


# リロード対応
@socketio.on('reload')
def rejoin(name, isActive):
    for player in game.players:
        if player.get('name') == name:
            player['isActive']=isActive
            emit('message', {'objects': player.get('objects'),
                             'opencast': player.get('opencast'),
                             'msg': player.get('message')
                             }, to=player['name'])
            break
    else:
        # ブラウザのsessionStorageに残っている過去の参加者名前を削除
        emit('message', {'elase_storage': True},to=player['name'])


# 参加ボタンを2度押し、ゲーム参加をキャンセルする
@socketio.on('decline')
def decline(name):
    player = game.player_obj(name)
    player['isActive'] = False
    emit('message', {'players': game.players_for_player}, broadcast=True)


@socketio.on('set renguard')
def set_renguard(renguard):
    game.renguard = renguard
    emit('message', {'renguard': game.renguard}, broadcast=True)


@socketio.on('set ranshiro')
def set_ranshiro(ranshiro):
    game.ranshiro = ranshiro
    emit('message', {'ranshiro': game.ranshiro}, broadcast=True)


@socketio.on('set castmiss')
def set_castmiss(castmiss):
    game.castmiss = int(castmiss)
    game.set_cast_menu()
    emit('message', {'castmiss': game.castmiss, 'castMenu': game.cast_menu}, broadcast=True)


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

        player['message'] = player['name'] + 'は' + player['cast']['name']
        emit('message',
             {'players': game.players_for_player, 'phase': game.phase, 'msg': player['message'],
              'opencast': player['opencast']},
             to=player['name'])


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
            player['message'] = '次のゲームまでお待ちください'
            player['doing_action'] = False

        else:
            if player in game.wolves:
                player['message'] = '誰を襲いますか'
                player['doing_action'] = True
                player['target'] = None
                for p in game.players:
                    if p['isAlive'] and not (p in game.wolves):
                        player['objects'].append(p['name'])
            elif player['cast']['name'] in ['占い師']:
                player['message'] = '誰を占いますか'
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
                player['message'] = '誰を守りますか'
            elif player['cast']['name'] in ['霊媒師']:
                if game.outcast in game.wolves:
                    player['message'] = game.outcast['name'] + 'は人狼だった。\n夜明けまでお待ちください'
                    player['opencast'][game.outcast['name']] = '人狼'
                else:
                    player['message'] = game.outcast['name'] + 'は人狼ではなかった。\n夜明けまでお待ちください'
                    player['opencast'][game.outcast['name']] = '人狼ではない'
                player['doing_action'] = False
            else:
                player['message'] = '夜明けまでお待ちください'
                player['doing_action'] = False
        emit('message', {'msg': player['message'], 'phase': game.phase, 'objects': player['objects'],
                         'opencast': player['opencast']}, to=player['name'])


@socketio.on('do action')
def action(myname, object_name):
    player = game.player_obj(myname)
    object = game.player_obj(object_name)
    if player['doing_action']:
        if player in game.wolves:
            player['message'] = '誰を襲いますか'
            target_set(player, object)
            game.wolf_target = game.get_wolf_target()
            """wolf_target = {  target_name:[wolf_name,wolf_name],
                                target_name:[wolf_name,],}            """
            posted_wolves = [w['name'] for w in game.wolves if w.get('target') is not None]
            if len(posted_wolves) == game.count_suv_wolf():  # 狼全員の投票しており
                if len(game.wolf_target) == 1:  # 狼全員の投票が一人のターゲットになった時、合意
                    object['is_targeted'] = True
                    player['message'] = '襲撃先は' + object['name']
                    for w in game.wolves:
                        w['doing_action'] = False
                        w['target'] = None
                    object['targetedby'] = None

            for wolf in game.wolves:
                emit('message', {'msg': wolf['message'], 'wolf_target': game.wolf_target}, to=wolf['name'])

        elif player['cast']['name'] in ['占い師', ]:
            if object['cast']['name'] == '人狼':
                comment = '人狼'
            else:
                comment = '人狼ではない'
            player['opencast'][object['name']] = comment
            player['message'] = object['name'] + 'は' + comment
            player['doing_action'] = False
            emit('message', {'msg': player['message'], 'opencast': player['opencast'], 'objects': []},
                 to=player['name'])

        elif player['cast']['name'] in ['騎士']:
            object['is_protected'] = True
            player['last_protect'] = object
            player['message'] = object['name'] + 'を護衛します'
            player['doing_action'] = False
            emit('message', {'msg': player['message'], 'objects': []}, to=player['name'])

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


if __name__ == '__main__':
    socketio.run(app, host='localhost', debug=True)
    # socketio.run(app, host='0.0.0.0', debug=True)

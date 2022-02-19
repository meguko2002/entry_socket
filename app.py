# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room
import random

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
socketio = SocketIO(app)


class Cast:

    def __init__(self, ):
        self.name = '市民'
        self.team = 'white'
        self.color = 'white'
        self.gm_message = '夜明けまでお待ちください'
        self.done_action = False
        self.opencasts = []
        self.is_alive = True
        self.is_targeted = False
        self.is_protected = False
        self.target = None

    def __str__(self):
        return self.name


class Villager(Cast):
    def __init__(self):
        super(Villager, self).__init__()
        self.done_action = True


class Werewolf(Cast):
    group = []
    target_dict = {}

    def __init__(self):
        super(Werewolf, self).__init__()
        self.name = '人狼'
        self.team = 'black'
        self.color = 'black'
        self.gm_message = '誰を襲いますか'
        self.id = ''  # 仲間の人狼と連絡を取るためにplayer_idと紐づけて使う
        Werewolf.group.append(self)

    def survivors_num(self):
        num = 0
        for c in self.group:
            if c.is_alive:
                num += 1
        return num


class FortuneTeller(Cast):
    def __init__(self):
        super(FortuneTeller, self).__init__()
        self.name = '占い師'
        self.team = 'white'
        self.color = 'white'
        self.gm_message = '誰を占いますか'
        self.random_white = True


class Knight(Cast):
    def __init__(self):
        super(Knight, self).__init__()
        self.name = '騎士'
        self.team = 'white'
        self.color = 'white'
        self.gm_message = '誰を護衛しますか'
        self.consecutive_guard = False  # True: 連ガード有り


players = [{'name': '太郎', 'isActive': False, 'isAlive': True, 'sid': '', 'isGM': True},
           {'name': '花子', 'isActive': False, 'isAlive': True,  'sid': '',  'isGM': False},
           {'name': 'じろ', 'isActive': False, 'isAlive': True,  'sid': '',  'isGM': False},
           {'name': 'ポコ', 'isActive': False, 'isAlive': True,  'sid': '',  'isGM': False}]


class Village:
    def __init__(self, players):
        self.players = players
        self.casts = []
        self.phase = '参加受付中'
        self.dead_ids = []
        self.cast_menu = {'人狼': 1, '占い師': 0, '騎士': 0}

    # キャスト決め
    def select_cast(self):
        for castname, num in self.cast_menu.items():
            if castname == '人狼':
                Werewolf.group.clear()
                for i in range(num):
                    self.casts.append(Werewolf())
            elif castname == '占い師':
                for i in range(num):
                    self.casts.append(FortuneTeller())
            elif castname == '騎士':
                for i in range(num):
                    self.casts.append(Knight())
        while len(self.casts) < len(self.players):
            self.casts.append(Villager())

        delta = len(self.casts) - len(self.players)
        if delta > 0:
            while True:
                tmp_list = random.sample(self.casts, delta)
                for cast in tmp_list:
                    if cast.name == '人狼':
                        break

    # キャストの割り当て
    def assign_cast(self):
        random.shuffle(self.casts)
        whites = []
        wolves = []
        for index, cast in enumerate(self.casts):
            if cast.color == 'white':
                whites.append(index)
            elif cast.name == '人狼':
                wolves.append(index)

        for my_id, my_cast in enumerate(self.casts):
            # 　基本的に自分の役職以外は分からない
            for target_id, target_cast in enumerate(self.casts):
                if target_id == my_id:
                    my_cast.opencasts.append(my_cast.name)
                else:
                    my_cast.opencasts.append('')

            if my_cast.name in ['人狼', '狂信者']:
                for wolf_id in wolves:
                    my_cast.opencasts[wolf_id] = '人狼'
            elif my_cast.name == '占い師':
                # ランシロありの処理
                if my_cast.random_white:
                    random_white_id = random.choice(whites)
                    my_cast.opencasts[random_white_id] = '人狼ではない'

    def expel(self, index):
        self.players[index]['isAlive'] = False
        cast = self.casts[index]
        cast.is_alive = False

    def judge(self):
        white_num = 0
        black_num = 0
        for cast in self.casts:
            if cast.is_alive:
                if cast.team == 'white':
                    white_num += 1
                elif cast.team == 'black':
                    black_num += 1
        if black_num == 0:
            self.phase = '市民勝利'
            return '市民勝利'
        elif white_num <= black_num:
            self.phase = '人狼勝利'
            return '人狼勝利'

        else:
            if self.phase == '昼':
                self.phase = '夜'
                return '夜がきました'
            else:
                self.phase = '昼'
                if not self.dead_ids:
                    message = '昨晩、襲撃された方は、いませんでした'
                else:
                    p_names = 'と、'.join([self.players[id]['name'] for id in self.dead_ids])
                    message = '昨晩、' + p_names + 'が襲撃されました'
                self.dead_ids = []
                return message

    def setplayers(self, players):
        self.players = players
    #     self.player_reset()
    #     self.cast_reset()
    #     for player in self.players:
    #         if player['isGM']:
    #             return
    #     self.players[0]['isGM'] = True

    def search_player(self, sid):
        for index, player in enumerate(self.players):
            if player['sid'] == sid:
                return index, player
        return False

    def done_all_actions(self):
        for cast in self.casts:
            if cast.is_alive and not cast.done_action:
                return False
        return True

    def judge_casts_action(self):
        self.dead_ids = []
        for id, cast in enumerate(self.casts):
            # GJ出なければcastは襲撃
            if cast.is_alive:
                if cast.is_targeted and not cast.is_protected:
                    cast.is_alive = False
                    self.dead_ids.append(id)
            cast.is_targeted = False

        for id in self.dead_ids:
            self.players[id]['isAlive'] = False

    def player_reset(self):
        for player in self.players:
            player['isAlive'] = True

    def cast_reset(self):
        self.casts.clear()


vil = Village(players)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/player_list')
def show_list():
    return jsonify({'players': vil.players, 'phase': vil.phase})


@socketio.on('submit member')
def submit_member(players):

    for new_id, new_player in enumerate(players):
        for old_player in vil.players:
            if new_player.get('sid','no') == old_player.get('sid','nokey'):
                emit('message', {'id': new_id}, room=old_player['sid'])
        # else :  # oldplayerでキャンセルされた人のsessionStorageを消す
        #     emit('message', {'id': "undefined"}, room=old_player['sid'])

    vil.setplayers(players)
    # GMがキャンセルされたりはしないの？
    #     for player in self.players:
    #         if player['isGM']:
    #             return
    #     self.players[0]['isGM'] = True

    emit('message', {'players': players}, broadcast=True)


@socketio.on('join')
def join(index):
    player = vil.players[int(index)]
    player['sid'] = request.sid
    # session['player'] = player['name']  # sessionにuser情報を保存
    # room = session.get('room')
    # join_room(room)

    # player['isActive'] = isActive
    message = player['name'] + 'さん、ようこそ'
    emit('message', {'msg': message}, room=player['sid'])
    emit('message', {'players': vil.players}, broadcast=True)


# リロード対応
@socketio.on('reload')
def rejoin(old_sid):
    new_sid = request.sid
    for player in vil.players:
        if player['sid'] == old_sid:
            player['sid'] = new_sid
        break
    emit('message', {'players': vil.players, 'casts':vil.casts}, room=player['sid'])


# 参加ボタンを2度押し、ゲーム参加をキャンセルする
@socketio.on('decline')
def decline():
    sid = request.sid
    for player in vil.players:
        if player['sid'] == sid:
            player['sid'] = ''
    emit('message', {'players': vil.players}, broadcast=True)

@socketio.on('assign cast')
def assign_cast():
    vil.player_reset()
    vil.select_cast()
    vil.assign_cast()
    vil.phase = '昼'
    for player, cast in zip(vil.players, vil.casts):
        message = player['name'] + 'は' + cast.name
        emit('message', {'players': vil.players, 'phase': vil.phase, 'msg': message,
                         'casts': cast.opencasts}, room=player['sid'])


@socketio.on('vote')
def vote(index):
    vil.expel(int(index))
    emit('message', {'msg': vil.players[index]['name'] + 'は追放されました', 'players': vil.players},
         broadcast=True)


@socketio.on('judge')
def judge():
    message = vil.judge()
    emit('message', {'players': vil.players, 'phase': vil.phase, 'msg': message}, broadcast=True)


@socketio.on('request action from gm')
def response_action():
    vil.phase = '深夜'
    for player, cast in zip(vil.players, vil.casts):
        if player['isAlive']:
            cast.done_action = False
            message = cast.gm_message
            if cast.name in ['人狼', '占い師', '騎士']:
                target_candidates = []
                for target_index, target in enumerate(vil.casts):
                    if target == cast:  # 自分自身はターゲットから除外
                        continue
                    if target.is_alive:
                        if cast.name == '人狼':
                            if target in cast.group:
                                continue
                        elif cast.name == '騎士':
                            if not cast.consecutive_guard and target.is_protected:
                                target.is_protected = False
                                continue
                        target_candidates.append(target_index)
            else:
                cast.done_action = True
                target_candidates = []
        else:
            message = '次のゲームまでお待ちください'
            target_candidates = []

        emit('message', {'msg': message, 'phase': vil.phase, 'object_indexes': target_candidates}, room=player['sid'])


@socketio.on('do action')
def action(target_index):
    my_index, player = vil.search_player(request.sid)
    cast = vil.casts[my_index]
    if cast.name not in ['人狼', '占い師', '騎士']:
        cast.done_action = True
    elif not cast.done_action:
        if cast.name in ['人狼', ]:
            cast.target_dict[my_index] = int(target_index)
            wolves_agree = False
            if len(cast.target_dict) == cast.survivors_num():
                if len(set(cast.target_dict.values())) == 1:
                    wolves_agree = True
                else:
                    wolves_agree = False
            for p, c in zip(vil.players, vil.casts):
                if c.name == '人狼':
                    if wolves_agree:
                        vil.casts[target_index].is_targeted = True
                        cast.target_dict.clear()
                        c.done_action = True
                        message = '襲撃先は' + vil.players[target_index]['name']
                    else:
                        message = '誰を襲いますか'
                    emit('message', {'msg': message, 'group_target_dict': c.target_dict}, room=p['sid'])

        elif cast.name in ['占い師', ]:
            if vil.casts[target_index].name == '人狼':
                comment = '人狼'
            else:
                comment = '人狼ではない'
            cast.opencasts[target_index] = comment
            message = vil.players[target_index]['name'] + 'は' + comment
            cast.done_action = True
            emit('message', {'msg': message, 'casts': cast.opencasts}, room=player['sid'])

        elif cast.name in ['騎士']:
            vil.casts[target_index].is_protected = True
            message = vil.players[target_index]['name'] + 'を護衛します'
            cast.done_action = True
            emit('message', {'msg': message, 'casts': cast.opencasts}, room=player['sid'])

    # 全員のactionが完了した後の処理
    for c in vil.casts:
        if not c.done_action:
            return
    vil.judge_casts_action()  # 全てのcastのアクションから全体の判定
    vil.phase = '朝'
    message = '夜のアクションが終了しました'
    emit('message', {'phase': vil.phase, 'msg': message}, broadcast=True)


@socketio.on('next game')
def next_game():
    vil.player_reset()
    vil.cast_reset()

    vil.phase = '参加受付中'
    message = '参加受付中'
    emit('message', {'players': vil.players, 'phase': vil.phase, 'casts': '', 'msg': message}, broadcast=True)


@socketio.on('submit GM')
def give_gm(myindex, index):
    vil.players[myindex]['isGM'] = False
    vil.players[int(index)]['isGM'] = True
    emit('message', {'players': vil.players}, broadcast=True)


@socketio.on('change cast')
def change_cast(menu):
    for role in menu:
        name = role['name']
        vil.cast_menu[name] = role.get('num', 0)
    print(menu)
    emit('message', {'menu': menu}, broadcast=True)


@socketio.on('disconnect')
def disconnect():
    sid = request.sid
    # leave_room()
    for id, player in enumerate(vil.players):
        if player.get('sid') == sid:
            player['sid'] = ''
            if player['isGM']:
                next_id = (id + 1) % len(vil.players)
                vil.players[next_id]['isGM'] = True

            break
    emit('message', {'players': vil.players}, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)

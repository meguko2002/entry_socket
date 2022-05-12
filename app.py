from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import random
import hashlib
import pprint

dat = 'python'  # SHA224のハッシュ値

app = Flask(__name__)
app.config['SECRETE_KEY'] = 'ABCDEFTH'
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


class Member(db.Model):
    __tablename__ = 'Member'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    # price = db.Column(db.Integer)


# app.before_first_requestのデコレータは最初のrequestの時だけデコレートしている関数を実行する
# https://shigeblog221.com/
#
# -sqlalchemy/
# @app.before_first_request
# def init():
#     db.create_all()


MEMBERS = []

# https://osaka-jinro-lab.com/article/osusumehaiyaku/?fbclid=IwAR3zza4CUZ20vOKWbIE1ALGaZAXkj0hEz8ZM40CzFlthUWbwkDokZwrbki4
REGURATION = {0: {'cast_menu': '', 'ranshiro': True, 'renguard': False, 'castmiss': False},
              1: {'cast_menu': '', 'ranshiro': True, 'renguard': False, 'castmiss': False},
              2: {'cast_menu': '', 'ranshiro': True, 'renguard': False, 'castmiss': False},
              3: {'cast_menu': {"人狼": 1, "狂人": 0, "占い師": 0, "騎士": 0, "霊媒師": 0, "狂信者": 0, "市民": 2},
                  'ranshiro': True, 'renguard': False, 'castmiss': False},
              4: {'cast_menu': {"人狼": 1, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 0, "狂信者": 0, "市民": 1},
                  'ranshiro': True, 'renguard': False, 'castmiss': True},
              5: {'cast_menu': {"人狼": 1, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 0, "狂信者": 0, "市民": 2},
                  'ranshiro': True, 'renguard': False, 'castmiss': True},
              6: {'cast_menu': {"人狼": 1, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 0, "狂信者": 0, "市民": 3},
                  'ranshiro': True, 'renguard': False, 'castmiss': True},
              7: {'cast_menu': {"人狼": 2, "狂人": 0, "占い師": 1, "騎士": 1, "霊媒師": 1, "狂信者": 0, "市民": 3},
                  'ranshiro': True, 'renguard': False, 'castmiss': True},
              8: {'cast_menu': {"人狼": 2, "狂人": 0, "占い師": 1, "騎士": 1, "霊媒師": 1, "狂信者": 0, "市民": 4},
                  'ranshiro': True, 'renguard': False, 'castmiss': True},
              9: {'cast_menu': {"人狼": 2, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 1, "狂信者": 0, "市民": 3},
                  'ranshiro': True, 'renguard': False, 'castmiss': False},
              10: {'cast_menu': {"人狼": 2, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 1, "狂信者": 0, "市民": 4},
                   'ranshiro': True, 'renguard': False, 'castmiss': False},
              11: {'cast_menu': {"人狼": 2, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 1, "狂信者": 0, "市民": 5},
                   'ranshiro': True, 'renguard': False, 'castmiss': False},
              12: {'cast_menu': {"人狼": 3, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 1, "狂信者": 0, "市民": 5},
                   'ranshiro': True, 'renguard': False, 'castmiss': False},
              13: {'cast_menu': {"人狼": 3, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 1, "狂信者": 0, "市民": 6},
                   'ranshiro': True, 'renguard': False, 'castmiss': False},
              14: {'cast_menu': {"人狼": 3, "狂人": 1, "占い師": 1, "騎士": 1, "霊媒師": 1, "狂信者": 0, "市民": 7},
                   'ranshiro': True, 'renguard': False, 'castmiss': False},
              15: {'cast_menu': {"人狼": 3, "狂人": 2, "占い師": 1, "騎士": 1, "霊媒師": 1, "狂信者": 0, "市民": 7},
                   'ranshiro': True, 'renguard': False, 'castmiss': False},
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
    def __init__(self):
        self.players = []
        self.casts = CASTS
        self.phase = '参加受付中'
        self.dead_players = []
        self.cast_menu = None
        self.ranshiro = None
        self.renguard = None
        self.castmiss = None  # True: 役職欠けあり
        self.wolf_target = {}
        self.wolves = []
        self.citizens = []
        self.outcast = None  # 追放者

    @property
    def players_for_player(self):  # 配布用players（castは送らない）
        send_keys = ['name','pid', 'isActive', 'isAlive', 'isGM']
        res_players = []
        for p in self.players:
            p_select = {}
            for key in send_keys:
                p_select[key] = p.get(key)
            res_players.append(p_select)
        return res_players

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
            player['last_protected'] = None
            player['opencast'].clear()

    def cast_reset(self):
        self.wolves.clear()
        self.citizens.clear()

    def adjust_citizen_num(self, submitted_menu=None):
        if submitted_menu is None:
            submitted_menu = self.cast_menu
        # 市民以外の員数を数えてcast_sumに代入
        non_villager_num = 0
        for castname, num in submitted_menu.items():
            if castname == '市民':
                continue
            non_villager_num += int(num)
        # ゲーム不成立条件（市民の数が負になる）
        if non_villager_num > len(game.players) + int(self.castmiss):
            return
        else:
            self.cast_menu = submitted_menu
            self.cast_menu['市民'] = len(game.players) - non_villager_num + int(self.castmiss)

    def suggest_cast_menu(self):
        self.cast_menu = REGURATION[len(self.players)]['cast_menu']
        self.ranshiro = REGURATION[len(self.players)]['ranshiro']
        self.renguard = REGURATION[len(self.players)]['renguard']
        self.castmiss = REGURATION[len(self.players)]['castmiss']  # True: 役職欠けあり

    def player_by_sid(self, sid):
        for p in self.players:
            if p.get('sid') == sid:
                return p
        return None

    def player_by_name(self, name):
        for p in self.players:
            if p.get('name') == name:
                return p
        return None

    def restruct_players(self, add_names, del_names):
        for i, p in enumerate(self.players):
            if p['name'] in del_names:
                self.players.remove(p)
                # 追加の参加者が居れば削除した参加者の並びに挿入
                if len(add_names) != 0:
                    new_p_name = add_names.pop(0)
                    new_player = {'name': new_p_name, 'isActive': False, 'isAlive': True, 'isGM': False, 'opencast': {}}
                    self.players.insert(i, new_player)
        for add_p_name in add_names:
            new_player = {'name': add_p_name, 'isActive': False, 'isAlive': True, 'isGM': False, 'opencast': {}}
            self.players.append(new_player)

    def get_wolf_target(self):
        target_dict = {}
        for p in self.players:
            ws = p.get('targetedby')
            if ws:
                target_dict[p['name']] = [w['name'] for w in ws]
        return target_dict

    def _get_pid(self):
        new_pid = 0
        pids = sorted([p['pid'] for p in self.players])
        print(pids)
        for i,pid in enumerate(pids):
            new_pid = i+1
            if pid != new_pid:
                return new_pid
        return new_pid+1

    def append_player(self, sid, member):
        pid=self._get_pid()
        player = {'name': member['name'],'pid':pid, 'key': member['key'], 'sid': sid, 'isActive': True, 'isAlive': True,
                  'isGM': False, 'opencast': {}}
        self.players.append(player)
        return player

    def gameout(self, sid):
        p = self.player_by_sid(sid)
        self.players.remove(p)
        return p


def append_member(name):
    # SHA224のハッシュ値
    hs = hashlib.sha224((dat + name).encode()).hexdigest()
    member = {'name': name, 'key': hs}
    MEMBERS.append(member)
    # pprint.pprint(MEMBERS)
    return member


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


game = Game()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


@socketio.on('connect')
def connect(key):
    if key is not None:
        for member in MEMBERS:
            if member['key'] == key:
                commer = member   # MEMMBERS に登録済みの常連commer が ページリクエストしてきた
                # commerは、すでにゲーム参加していなければ参加
                if commer['key'] not in [p['key'] for p in game.players]:
                    player = game.append_player(request.sid, commer)
                    emit('message', {'my_name': player['name']}, to=player['sid'])
                    game.suggest_cast_menu()
    # if commer is not None:
    #     message = commer['name'] + 'さんが参加しました'
    #     emit('message', {'message': message}, broadcast=True)
    #     message = commer['name'] + 'さん、おかえりなさい'
    #     emit('message', {'message': message}, to=commer['sid'])
    emit('message', {'phase': game.phase,
                     'players': game.players_for_player,
                     'castMenu': game.cast_menu,
                     'ranshiro': game.ranshiro,
                     'renguard': game.renguard,
                     'castmiss': game.castmiss,
                     }, broadcast=True)


@socketio.on('disconnect')
def disconnect():
    p = game.player_by_sid(request.sid)
    if p is not None:
        game.gameout(request.sid)
        game.suggest_cast_menu()
        emit('message', {
                         'players': game.players_for_player,
                         'castMenu': game.cast_menu,
                         'ranshiro': game.ranshiro,
                         'renguard': game.renguard,
                         'castmiss': game.castmiss,
                         }, broadcast=True)


@socketio.on('join')
def join(name):
    # メンバー登録
    member = append_member(name)
    message = name + 'さん、初めまして'
    emit('message', {'msg': message, 'key': member['key'], 'my_name':member['name']}, to=request.sid)
    # 試合に参加
    game.append_player(request.sid, member)
    game.suggest_cast_menu()
    emit('message', {'phase': game.phase,
                     'players': game.players_for_player,
                     'castMenu': game.cast_menu,
                     'ranshiro': game.ranshiro,
                     'renguard': game.renguard,
                     'castmiss': game.castmiss,
                     }, broadcast=True)


@socketio.on('change name')
def change_name(name):
    p = game.player_by_sid(request.sid)
    p['name'] = name
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
    game.castmiss = castmiss
    game.adjust_citizen_num()
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
             to=player['sid'])


@socketio.on('vote')
def vote(name):
    if name in [p['name'] for p in game.players]:
        game.outcast = game.player_by_name(name)
        game.outcast['isAlive'] = False
        msg = game.outcast['name'] + 'は追放されました'
    else:
        game.outcast = None
        msg = '誰も追放されませんでした'
    emit('message', {'msg': msg, 'players': game.players_for_player},
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
            elif player['cast']['name'] in ['霊媒師'] and game.outcast is not None:
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
                         'opencast': player['opencast']}, to=player['sid'])


@socketio.on('do action')
def action(object_name):
    player = game.player_by_sid(request.sid)
    object = game.player_by_name(object_name)
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
                emit('message', {'msg': wolf['message'], 'wolf_target': game.wolf_target}, to=wolf['sid'])

        elif player['cast']['name'] in ['占い師', ]:
            if object['cast']['name'] == '人狼':
                comment = '人狼'
            else:
                comment = '人狼ではない'
            player['opencast'][object['name']] = comment
            player['message'] = object['name'] + 'は' + comment
            player['doing_action'] = False
            emit('message', {'msg': player['message'], 'opencast': player['opencast'], 'objects': []},
                 to=player['sid'])

        elif player['cast']['name'] in ['騎士']:
            object['is_protected'] = True
            player['last_protect'] = object
            player['message'] = object['name'] + 'を護衛します'
            player['doing_action'] = False
            emit('message', {'msg': player['message'], 'objects': []}, to=player['sid'])

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
    player = game.player_by_name(name)
    player['isGM'] = True
    emit('message', {'players': game.players_for_player}, broadcast=True)


@socketio.on('change cast')
def change_cast(new_menu):
    game.adjust_citizen_num(new_menu)
    emit('message', {'castMenu': game.cast_menu}, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host='localhost', debug=True)
    # socketio.run(app, host='0.0.0.0', debug=True)

from flask import Flask, render_template, request, \
    redirect, session, url_for, jsonify
from flask_login import LoginManager, UserMixin, current_user, login_user, \
    logout_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_session import Session
import random

# from testapp import app, socketio

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'
app.config['SESSION_TYPE'] = 'filesystem'
login = LoginManager(app)
Session(app)
socketio = SocketIO(app, manage_session=False)

# from testapp import db
# from testapp.models.player import Player

# 起動の仕方は(venv)entry_socket 配下で python server.py とする。https://qiita.com/Bashi50/items/e3459ca2a4661ce5dac6

# https://osaka-jinro-lab.com/article/osusumehaiyaku/?fbclid=IwAR3zza4CUZ20vOKWbIE1ALGaZAXkj0hEz8ZM40CzFlthUWbwkDokZwrbki4
REGURATION = {0: {'cast_menu': {"人狼": 1, "狂人": 0, "占い師": 0, "騎士": 0, "霊媒師": 0, "狂信者": 0, "市民": 0},
                  'ranshiro': True, 'renguard': False, 'castmiss': True},
              1: {'cast_menu': {"人狼": 1, "狂人": 0, "占い師": 0, "騎士": 0, "霊媒師": 0, "狂信者": 0, "市民": 1},
                  'ranshiro': True, 'renguard': False, 'castmiss': True},
              2: {'cast_menu': {"人狼": 1, "狂人": 0, "占い師": 0, "騎士": 1, "霊媒師": 0, "狂信者": 0, "市民": 1},
                  'ranshiro': True, 'renguard': False, 'castmiss': True},
              3: {'cast_menu': {"人狼": 1, "狂人": 0, "占い師": 0, "騎士": 1, "霊媒師": 0, "狂信者": 0, "市民": 2},
                  'ranshiro': True, 'renguard': False, 'castmiss': True},
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


class User(UserMixin, object):
    def __init__(self, id=None):
        self.id = id


@login.user_loader
def load_user(id):
    return User(id)


class Game:
    def __init__(self, village_name):
        self.village_name = village_name
        self.players = []
        self.casts = CASTS
        self.phase = 'ロビー'
        self.dead_players = []
        self.cast_menu = None
        self.ranshiro = None
        self.renguard = None
        self.castmiss = None  # True: 役職欠けあり
        self.wolf_target = {}
        self.wolves = []
        self.citizens = []
        self.outcast = None  # 追放者
        self.id_bin = set()
        self.gm = {}

    @property
    def players_for_player(self):  # 配布用players（castは送らない）
        send_keys = ['name', 'pid', 'isAlive', 'is_playing', 'opencast']
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
        new_players = []
        for player in self.players:
            new_p = {'isAlive': True,
                     'name': player['name'],
                     'sid': player['sid'],
                     'pid': player['pid'],
                     'is_playing': True,
                     'opencast': {}}
            new_players.append(new_p)
        self.players = new_players

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
        if non_villager_num > len(self.players) + int(self.castmiss):
            return
        else:
            self.cast_menu = submitted_menu
            self.cast_menu['市民'] = len(self.players) - non_villager_num + int(self.castmiss)

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

    def gm_by_sid(self, sid):
        if self.gm.get('sid') == sid:
            return self.gm
        return None

    def gm_by_name(self, name):
        if self.gm.get('name') == name:
            return self.gm
        return None

    def get_wolf_target(self):
        target_dict = {}
        for p in self.players:
            ws = p.get('targetedby')
            if ws:
                target_dict[p['name']] = [w['name'] for w in ws]
        return target_dict

    def _get_pid(self):
        if len(self.id_bin) != 0:
            id = self.id_bin.pop()
        else:
            id = len(self.players) + 1
        return id

    #############################################################################

    @property
    def broadcast_info(self, msg=None):
        return {'phase': self.phase,
                'players': self.players_for_player,
                'castMenu': self.cast_menu,
                'ranshiro': self.ranshiro,
                'renguard': self.renguard,
                'castmiss': self.castmiss,
                'gm': self.gm,
                'msg': msg
                }

    def emit_broadcast(self, message=None):
        emit('message', self.broadcast_info, to=self.village_name)

    def emit_personal(self, message=None):
        emit('message', self.broadcast_info)

    def set_gm(self, sid, name):
        self.gm = {'name': name, 'sid': sid, 'is_playing': True}

    def join_game(self, sid, name):
        player = {'name': name,
                  'pid': self._get_pid(),
                  'sid': sid,
                  'isAlive': True,
                  'is_playing': True
                  }
        self.players.append(player)
        self.suggest_cast_menu()  # メンバー追加により最適なキャストを選び直し

    def leave(self, name):
        player = self.player_by_name(name)
        if player:
            self.id_bin.add(player['pid'])
            self.players.remove(player)
            self.suggest_cast_menu()


games = []
name_list = []


def on_game(village_name):
    assert village_name, '村オブジェクトがない！！'
    return next((game for game in games if game.village_name == village_name), None)


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


@app.route('/')
def index():
    return render_template('testapp/index.html')


@app.route('/session')
def session_access():
    my_name = current_user.id \
        if current_user.is_authenticated else ''
    village_name = session.get('village_name', '朝活村')
    return jsonify({'my_name': my_name, 'village_name': village_name})


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


# サーバーをリセット
# @app.route('/host', methods=['GET', 'POST'])
# def host():
#     if request.method == 'POST':
#         # global game
#         # game = Game()
#         return redirect(url_for('index'))
#     return render_template('testapp/host.html')


@socketio.on('create village')
def create_village(data):
    my_name = data.get('my_name')
    login_user(User(my_name))
    # session['my_name'] = my_name
    village_name = data.get('village_name')
    session['village_name'] = village_name
    # 同一の村の名前がすでにあるか調べる
    if village_name in [game.village_name for game in games]:
        emit('message', {'msg': 'その村はすでにあります'})
        return
    else:
        game = Game(village_name)
        game.set_gm(request.sid, my_name)
        game.phase = '参戦受付中'
        games.append(game)  # アプリに新しい村追加
        join_room(village_name)
        game.emit_broadcast()


@socketio.on('enter village')
def enter_village(data):
    village_name = data.get('village_name')
    session['village_name'] = village_name
    game = next((game for game in games if game.village_name == village_name), None)
    if game:
        join_room(village_name)
        game.emit_broadcast()
    else:
        emit('message', {'msg': '村がありません'})


@socketio.on('join game')
def join_game(my_name):
    login_user(User(my_name))
    game = on_game(session['village_name'])
    game.join_game(request.sid, my_name)
    game.emit_broadcast()


@socketio.on('leave')
def leave(name):
    village_name = session.get('village_name')
    game = on_game(village_name)
    game.leave(name)
    logout_user()
    game.emit_broadcast()


@socketio.on('logout')
def logout(name):
    village_name = session.get('village_name')
    game = on_game(village_name)
    if name != '':
        game.leave(name)
        game.emit_broadcast()
    logout_user()
    leave_room(village_name)
    emit('message', {'phase':'ロビー'})


# @app.route('/village', methods=['GET', 'POST'])
# def village():
#     global game
#     if request.method == 'POST':
#         player = Player(
#             name=request.form['player_name'],
#             is_gm=True
#         )
#         db.session.add(player)
#         db.session.commit()
#         game = Game()
#         return redirect(url_for('village'))
#     return render_template('testapp/index.html')



# @socketio.on('disconnect')
# def disconnect():
#     village_name = session.get('village_name')
#     game = on_game(village_name)
#     if game:
#         player = game.player_by_sid(request.sid)
#         if player:
#             player['is_playing'] = False
#         if game.gm['sid'] == request.sid:
#             game.gm['is_playing'] = False
#         game.emit_broadcast()


@socketio.on('submit GM')
def submit_gm(name):
    village_name = session.get('village_name')
    game = on_game(village_name)
    game.gm = {'name': name, 'sid': request.sid, 'is_playing': True}
    game.emit_broadcast()


@socketio.on('set renguard')
def set_renguard(renguard):
    village_name = session.get('village_name')
    game = on_game(village_name)
    game.renguard = renguard
    game.emit_broadcast()


@socketio.on('set ranshiro')
def set_ranshiro(ranshiro):
    village_name = session.get('village_name')
    game = on_game(village_name)
    game.ranshiro = ranshiro
    game.emit_broadcast()


@socketio.on('set castmiss')
def set_castmiss(castmiss):
    village_name = session.get('village_name')
    game = on_game(village_name)
    game.castmiss = castmiss
    game.adjust_citizen_num()
    game.emit_broadcast()


@socketio.on('assign cast')
def assign_cast(cast_menu):
    village_name = session.get('village_name')
    game = on_game(village_name)
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
        my_cast = player['cast']['name']
        player['opencast'][player['name']] = my_cast
        if my_cast in ['人狼', '狂信者']:  # 送り先が人狼または狂信者だったら
            for p in game.players:
                if p['cast']['name'] == '人狼':
                    player['opencast'][p['name']] = '人狼'

        elif my_cast == '占い師' and game.ranshiro:
            ranshiro_players = random.sample(game.citizens, 2)
            ranshiro_player = ranshiro_players[0] if ranshiro_players[0] != player else ranshiro_players[1]
            for p in game.players:
                if p == ranshiro_player:
                    player['opencast'][p['name']] = '人狼ではない'

        player['message'] = player['name'] + 'は' + player['cast']['name']
        emit('message',
             {'players': game.players_for_player, 'phase': game.phase, 'msg': player['message'],
              'opencast': player['opencast'], 'my_cast': my_cast},
             to=player['sid'])
    game.emit_broadcast()


@socketio.on('vote')
def vote(name):
    village_name = session.get('village_name')
    game = on_game(village_name)
    if name in [p['name'] for p in game.players]:
        game.outcast = game.player_by_name(name)
        game.outcast['isAlive'] = False
        msg = game.outcast['name'] + 'は追放されました'
    else:
        game.outcast = None
        msg = '誰も追放されませんでした'
    game.emit_broadcast(message=msg)


@socketio.on('judge')
def judge():
    village_name = session.get('village_name')
    game = on_game(village_name)
    message = game.win_judge()
    game.wolf_target.clear()
    emit('message', {'players': game.players_for_player, 'phase': game.phase,
                     'msg': message, 'wolf_target': game.wolf_target}, to=game.village_name)


@socketio.on('offer choices')
def offer_choices():
    village_name = session.get('village_name')
    game = on_game(village_name)
    game.phase = '深夜'
    for player in game.players:
        player['objects'] = []
        if not player.get('isAlive'):
            player['message'] = '次のゲームまでお待ちください'
            player['now_action'] = False

        else:
            if player in game.wolves:
                player['message'] = '誰を襲いますか'
                player['now_action'] = True
                player['target'] = None
                for p in game.players:
                    if p['isAlive'] and not (p in game.wolves):
                        player['objects'].append(p['name'])
            elif player['cast']['name'] in ['占い師']:
                player['message'] = '誰を占いますか'
                player['now_action'] = True
                for p in game.players:
                    if p['isAlive'] and not (p == player):
                        player['objects'].append(p['name'])
            elif player['cast']['name'] in ['騎士']:
                player['now_action'] = True
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
                player['now_action'] = False
            else:
                player['message'] = '夜明けまでお待ちください'
                player['now_action'] = False
        emit('message', {'msg': player['message'], 'phase': game.phase, 'objects': player['objects'],
                         'opencast': player['opencast'],
                         'now_action': player['now_action']
                         }, to=player['sid'])


@socketio.on('do action')
def action(object_name):
    village_name = session.get('village_name')
    game = on_game(village_name)
    player = game.player_by_sid(request.sid)
    object = game.player_by_name(object_name)
    if player['now_action']:
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
                        w['now_action'] = False
                        w['target'] = None
                    object['targetedby'] = None
            for wolf in game.wolves:
                emit('message', {'msg': wolf['message'],
                                 'wolf_target': game.wolf_target,
                                 'now_action':wolf['now_action']
                                 }, to=wolf['sid'])

        elif player['cast']['name'] in ['占い師', ]:
            if object['cast']['name'] == '人狼':
                comment = '人狼'
            else:
                comment = '人狼ではない'
            player['opencast'][object['name']] = comment
            player['message'] = object['name'] + 'は' + comment
            player['now_action'] = False
            emit('message', {'msg': player['message'],
                             'opencast': player['opencast'],
                             'objects': [],
                             'now_action': player['now_action']
                             },
                 to=player['sid'])

        elif player['cast']['name'] in ['騎士']:
            object['is_protected'] = True
            player['last_protect'] = object
            player['message'] = object['name'] + 'を護衛します'
            player['now_action'] = False
            emit('message', {'msg': player['message'],
                             'objects': [],
                             'now_action': player['now_action']},
                 to=player['sid'])

    # 全員のactionが完了した後の処理
    for player in game.players:
        if player['now_action']:
            return
    game.judge_casts_action()  # 全てのcastのアクションから全体の判定
    game.phase = '朝'
    message = '夜のアクションが終了しました'
    emit('message', {'phase': game.phase, 'msg': message}, to=game.village_name)


@socketio.on('wolf talk')
def wolf_talk(message):
    village_name = session.get('village_name')
    game = on_game(village_name)
    print(message)
    for wolf in game.wolves:
        emit('message', {'wolf_message': message},to=wolf['sid'])


@socketio.on('next game')
def next_game():
    village_name = session.get('village_name')
    game = on_game(village_name)
    game.player_reset()
    game.cast_reset()
    game.phase = '参戦受付中'
    message = '参戦受付中'
    game.emit_broadcast(message=message)
    emit('message', {'opencast': ''}, to=game.village_name)


@socketio.on('change cast')
def change_cast(new_menu):
    village_name = session.get('village_name')
    game = on_game(village_name)
    game.adjust_citizen_num(new_menu)
    game.emit_broadcast()


if __name__ == '__main__':
    socketio.run(app, debug=True)
    # socketio.run(app, host='192.168.2.36', debug=True)

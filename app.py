from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room
import random
from datetime import timedelta  #時間情報を用いるため

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
app.permanent_session_lifetime = timedelta(minutes=5) # -> 5分 #(days=5) -> 5日保存
socketio = SocketIO(app)


class Cast:

    def __init__(self, ):
        self.name = '市民'
        self.team = 'white'
        self.color = 'white'
        self.message = '夜明けまでお待ちください'
        self.done_action = True

    def __str__(self):
        return self.name

    def set_target(self, players):
        # todo 関数名をもっといい感じのものに変える。　playerのボタン操作可否を伝える関数
        return []

    def action(self, players, player_index, target_index):
        # todo return [] とreturn Noneの違いを調査
        return None


class Villager(Cast):
    pass

class Werewolf(Cast):
    def __init__(self):
        super(Werewolf, self).__init__()
        self.name = '人狼'
        self.team = 'black'
        self.color = 'black'
        self.message = '誰を襲いますか'

    def set_target(self, players):
        self.done_action = False
        target_indexes = []
        for target_index, player in enumerate(players):
            if player['cast'] == self:
                continue
            if not player['isAlive']:
                continue
            if player['cast'].name == '人狼':
                continue
            target_indexes.append(target_index)
        return target_indexes

    def action(self, players, player_index, target_index):
        players[target_index]['is_target'] = True
        self.done_action = True
        return '了解しました'


class FortuneTeller(Cast):
    def __init__(self):
        super(FortuneTeller, self).__init__()
        self.name = '占い師'
        self.team = 'white'
        self.color = 'white'
        self.message = '誰を占いますか'

    def set_target(self, players):
        self.done_action = False
        target_indexes = []
        for target_index, player in enumerate(players):
            if player['cast'] == self:
                continue
            if not player['isAlive']:
                continue
            target_indexes.append(target_index)
        return target_indexes

    def action(self, players, player_index, target_index):
        reply = '人狼' if players[target_index]['cast'].color == 'black' else'人狼ではない'
        players[player_index]['disclosed_casts'][target_index] = reply
        self.done_action = True
        message = players[target_index]['name']+'さんは '+ reply
        return message


casts = [Villager(), Werewolf(), FortuneTeller()]
players = [{'name': '浩司', 'isActive': False, 'isAlive': True, 'isGM': True},
           {'name': '恵', 'isActive': False, 'isAlive': True, 'isGM': False},
           {'name': '裕一', 'isActive': False, 'isAlive': True, 'isGM': False},
           {'name': '正輝', 'isActive': False, 'isAlive': True, 'isGM': False},
           {'name': 'ポコ', 'isActive': False, 'isAlive': True, 'isGM': False}]


class Village:
    def __init__(self, players, casts):
        self.players = players
        self.casts = casts
        self.phase = '参加受付中'
        self.dead_player_names = []

    def players_wo_cast(self):
        player_list_for_send = []
        for player in self.players:
            player_copy = player.copy()
            player_copy.pop('cast', None)
            player_list_for_send.append(player_copy)
        return player_list_for_send

    # キャスト決め
    def select_cast(self, casts: object):
        self.casts = casts
        while len(self.players) > len(self.casts):
            self.casts.append(Villager())

    # キャストの割り当て
    def assign_cast(self):
        random.shuffle(self.casts)
        for i,(player, cast) in enumerate(zip(self.players, self.casts)):
            player['cast'] = cast
            player['disclosed_casts'] = []
            for j in range(len(self.players)):
                if j == i:
                    player['disclosed_casts'].append(cast.name)
                else:
                    player['disclosed_casts'].append('')

    def expel(self, index):
        self.players[index]['isAlive'] = False

    def judge(self):
        white_num = 0
        black_num = 0
        for player in self.players:
            if player['isAlive']:
                if player['cast'].team == 'white':
                    white_num += 1
                elif player['cast'].team == 'black':
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
                return '恐ろしい夜がやってまいりました'
            else:
                self.phase = '昼'
                if not self.dead_player_names:
                    message = '昨晩、襲撃された方は、いませんでした'
                else:
                    p_names = 'さんと、'.join(self.dead_player_names)
                    message = f'昨晩、{p_names}さんが襲撃されました'
                self.dead_player_names = []
                return message

    def setplayers(self, players):
        self.players = players
        for player in self.players:
            if player['isGM']:
                return
        self.players[0]['isGM'] = True

    def night_action(self):
        messages = []
        indexes_set = []
        for player in self.players:
            if player['isAlive']:
                messages.append(player['cast'].message)
                indexes_set.append(player['cast'].set_target(self.players))
            else:  # 亡くなった方はアクション出来ない
                messages.append('次のゲームまでお待ちください')
                indexes_set.append([])
        return messages, indexes_set

    def search_player(self, sid):
        for index,player in enumerate(self.players):
            if player['sid'] == sid:
                return index, player
        return False

    def done_all_actions(self):
        for player in self.players:
            if not player['cast'].done_action:
                return False
        return True

    def cast_action(self):
        self.dead_player_names = []
        for player in self.players:
            # GJ出なければplayerは襲撃
            if player['isAlive'] and player.get('is_target') and not player.get('protected'):
                player['isAlive'] = False
                self.dead_player_names.append(player['name'])

    def player_reset(self):
        for player in self.players:
            player['isAlive'] = True


vil = Village(players, casts)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/player_list')
def show_list():
    vil.player_reset()
    return jsonify(vil.players)


@socketio.on('submit member')
def submit_member(players):
    vil.setplayers(players)
    emit('message', {'players': vil.players_wo_cast()}, broadcast=True)


@socketio.on('join')
def join(index, isActive):
    player = vil.players[index]
    player['sid'] = request.sid

    # reloadしても前の情報が残るような処理を追加
    # https://qiita.com/eee-lin/items/4e9a2a308ca52b58fd1e
    #     user = request.form["nm"]  # ユーザー情報を保存する
    #     session["user"] = user  # sessionにuser情報を保存
    # room とか　join_room(room)いるか、動作を再確認
    room = session.get('room')
    join_room(room)

    player['isActive'] = isActive
    message = player['name'] + 'さん、ようこそ' if isActive else ''
    emit('message', {'msg': message}, room=player['sid'])
    tmp_players = vil.players_wo_cast()
    emit('message', {'players': tmp_players}, broadcast=True)


@socketio.on('assign cast')
def assign_cast():
    vil.player_reset()
    vil.select_cast(casts)
    vil.assign_cast()
    vil.phase = '昼'
    for player in vil.players:
        castname = player['cast'].name
        message = player['name'] + 'さんは' + castname
        emit('message', {'players': vil.players_wo_cast(), 'phase': vil.phase,'msg': message,
                         'casts': player['disclosed_casts']}, room=player['sid'])


@socketio.on('vote')
def vote(index):
    vil.expel(index)
    emit('message', {'msg': vil.players[index]['name'] + 'さんは追放されました', 'players': vil.players_wo_cast()}, broadcast=True)


@socketio.on('judge')
def judge():
    message = vil.judge()
    emit('message', {'players': vil.players_wo_cast(), 'phase': vil.phase, 'msg': message}, broadcast=True)


@socketio.on('request action from gm')
def response_action():
    vil.phase = '深夜'
    messages, indexes_set = vil.night_action()
    for player, message, target_indexes in zip(vil.players, messages, indexes_set):
        emit('message', {'msg': message, 'phase': vil.phase, 'target_indexes': target_indexes}, room=player['sid'])


@socketio.on('do action')
def action(target_index):
    player_index, player = vil.search_player(request.sid)
    if not player['cast'].done_action:
        message = player['cast'].action(vil.players, player_index, target_index)
        emit('message', {'msg': message, 'casts':player['disclosed_casts']}, room=player['sid'])

        # 全員のactionが完了した後の処理
        if vil.done_all_actions():
            vil.cast_action()
            message = vil.judge()
            emit('message', {'players': vil.players_wo_cast(), 'phase': vil.phase, 'msg': message}, broadcast=True)


@socketio.on('next game')
def next_game():
    vil.player_reset()
    vil.phase = '参加受付中'
    message = '参加受付中'
    emit('message', {'players': vil.players_wo_cast(), 'phase': vil.phase, 'msg': message}, broadcast=True)


@socketio.on('submit GM')
def give_gm(myindex, index):
    vil.players[myindex]['isGM'] = False
    vil.players[index]['isGM'] = True
    emit('message', {'players': vil.players_wo_cast()}, broadcast=True)


@socketio.on('disconnect')
def disconnect():
    sid = request.sid
    # leave_room()
    for player in vil.players:
        if player['sid'] == sid:
            player['isActive'] = False
    emit('message', {'players': vil.players_wo_cast()}, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host='192.168.2.29', port=5000, debug=True)

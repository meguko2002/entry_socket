from flask import Flask, render_template, jsonify, session, request
from flask_socketio import SocketIO, emit, leave_room, join_room
import random
from datetime import timedelta  # 時間情報を用いるため

app = Flask(__name__)
app.secret_key = 'ABCDEFGH'
app.permanent_session_lifetime = timedelta(minutes=5)  # -> 5分 #(days=5) -> 5日保存
socketio = SocketIO(app)


class Cast:
    live_num = 0
    def __init__(self, ):
        self.id = ''
        self.name = '市民'
        self.team = 'white'
        self.color = 'white'
        self.gm_message = '夜明けまでお待ちください'
        self.done_action = True
        self.opencasts = []
        self.is_alive = True
        self.is_targeted = False
        self.is_protected = False

    def __str__(self):
        return self.name

    def offer_target(self, casts):
        # todo 関数名をもっといい感じのものに変える。　playerのボタン操作可否を伝える関数
        return ''

    def action(self, target, casts):
        # todo return [] とreturn Noneの違いを調査
        return ''


class Villager(Cast):
    pass


class Werewolf(Cast):
    group = []
    target_dict = {}

    def __init__(self):
        super(Werewolf, self).__init__()
        self.name = '人狼'
        self.team = 'black'
        self.color = 'black'
        self.gm_message = '誰を襲いますか'
        self.target_candidates = []
        Werewolf.group.append(self)

    def offer_target(self, casts):
        self.done_action = False
        self.target_candidates = []
        for terget, cast in enumerate(casts):
            if cast in self.group:
                continue
            if not cast.is_alive:
                continue
            self.target_candidates.append(terget)
        return self.target_candidates

    # def action(self, my_index, target):
    #     self.target_dict[my_index]=target
    # for wolf in self.group:
    #     if not wolf.is_alive:
    #         continue
    #     if wolf.target != self.target:
    #         # todo wolf.groupにself.targetをemitする
    #         break
    # # 人狼全員の標的が一致したら人狼全員のアクションを終了にする
    # else:
    #     casts[target].is_targeted = True
    #     for wolf in self.group:
    #         wolf.done_action = True
    # return '了解'


class FortuneTeller(Cast):
    def __init__(self):
        super(FortuneTeller, self).__init__()
        self.name = '占い師'
        self.team = 'white'
        self.color = 'white'
        self.gm_message = '誰を占いますか'
        self.target_candidates = []
        self.target = None

    def offer_target(self, casts):
        self.done_action = False
        self.target_candidates = []
        for target, cast in enumerate(casts):
            if cast == self:
                continue
            if not cast.is_alive:
                continue
            self.target_candidates.append(target)
        return self.target_candidates

    # def action(self, target, casts):
    #     reply = '人狼' if casts[target].color == 'black' else '人狼ではない'
    #     self.opencasts[target] = reply
    #     self.done_action = True
    #     return reply


# casts = [Werewolf(), Villager(),FortuneTeller(), Villager()]
casts = [Werewolf(), Werewolf(), FortuneTeller(), Villager(), Villager(), Villager(), Villager()]
players = [{'name': '浩司', 'isActive': False, 'isAlive': True, 'isGM': True},
           {'name': '恵', 'isActive': False, 'isAlive': True, 'isGM': False},
           {'name': '裕一', 'isActive': False, 'isAlive': True, 'isGM': False},
           {'name': '正輝', 'isActive': False, 'isAlive': True, 'isGM': False},
           {'name': '太郎', 'isActive': False, 'isAlive': True, 'isGM': False},
           {'name': '花子', 'isActive': False, 'isAlive': True, 'isGM': False},
           {'name': 'ポコ', 'isActive': False, 'isAlive': True, 'isGM': False}]


class Village:
    def __init__(self, players, casts):
        self.players = players
        self.casts = casts
        self.phase = '参加受付中'
        self.dead_ids = []

    # キャスト決め
    def select_cast(self, casts: object):
        self.casts = casts
        # castの方が少なかった場合は市民を補充
        while len(self.players) > len(self.casts):
            self.casts.append(Villager())
        # castの方が多かった場合は役職欠け

    # キャストの割り当て
    def assign_cast(self):
        random.shuffle(self.casts)
        for id, cast in enumerate(self.casts):
            cast.id = id
        whites = []
        wolves = []
        for index, cast in enumerate(self.casts):
            if cast.color == 'white':
                whites.append(index)
            elif cast.name == '人狼':
                wolves.append(index)
        random_white_id = random.choice(whites)

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
                return '恐ろしい夜がやってまいりました'
            else:
                self.phase = '昼'
                if not self.dead_ids:
                    message = '昨晩、襲撃された方は、いませんでした'
                else:
                    p_names = 'さんと、'.join([self.players[id]['name'] for id in self.dead_ids])
                    message = f'昨晩、{p_names}さんが襲撃されました'
                self.dead_ids = []
                return message

    def setplayers(self, players):
        self.players = players
        self.player_reset()
        self.cast_reset()
        for player in self.players:
            if player['isGM']:
                return
        self.players[0]['isGM'] = True

    def urge_casts_action(self):  # player全員にそれぞれのaction可能なidをtarget_setにまとめる(playerが占い師なら占い可能なid)
        messages = []
        target_set = []
        for cast in self.casts:
            if cast.is_alive:
                messages.append(cast.gm_message)
                targets = cast.offer_target(self.casts)
                target_set.append(targets)
            else:  # 亡くなった方はアクション出来ない
                messages.append('次のゲームまでお待ちください')
                target_set.append('')
        return messages, target_set

    def search_player(self, sid):
        for index, player in enumerate(self.players):
            if player['sid'] == sid:
                return index, player
        return False

    def done_all_actions(self):
        for cast in self.casts:
            if not cast.done_action:
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
            cast.is_protected = False

        for id in self.dead_ids:
            self.players[id]['isAlive'] = False

    def player_reset(self):
        for player in self.players:
            player['isAlive'] = True

    def cast_reset(self):
        for cast in self.casts:
            cast.is_alive = True
            cast.opencasts = []


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
    emit('message', {'players': vil.players}, broadcast=True)


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
    emit('message', {'players': vil.players}, broadcast=True)


@socketio.on('assign cast')
def assign_cast():
    vil.player_reset()
    vil.select_cast(casts)
    vil.assign_cast()
    vil.phase = '昼'
    for player, cast in zip(vil.players, vil.casts):
        message = player['name'] + 'さんは' + cast.name
        emit('message', {'players': vil.players, 'phase': vil.phase, 'msg': message,
                         'casts': cast.opencasts}, room=player['sid'])


@socketio.on('vote')
def vote(index):
    vil.expel(index)
    emit('message', {'msg': vil.players[index]['name'] + 'さんは追放されました', 'players': vil.players},
         broadcast=True)


@socketio.on('judge')
def judge():
    message = vil.judge()
    emit('message', {'players': vil.players, 'phase': vil.phase, 'msg': message}, broadcast=True)


@socketio.on('request action from gm')
def response_action():
    vil.phase = '深夜'
    messages, indexes_set = vil.urge_casts_action()
    for player, message, object_indexes in zip(vil.players, messages, indexes_set):
        emit('message', {'msg': message, 'phase': vil.phase, 'object_indexes': object_indexes}, room=player['sid'])


@socketio.on('do action')
def action(target_index):
    my_index, player = vil.search_player(request.sid)
    cast = vil.casts[my_index]
    if not cast.done_action:
        if cast.name in ['人狼', ]:
            cast.target_dict[my_index] = target_index
            # 人狼仲間の襲撃先候補が一致しているか判定
            live_num = 0    # 生存人狼数
            for cast in cast.group:
                if cast.is_alive:
                    live_num +=1
            wolves_agree = False
            if len(cast.target_dict) == live_num:
                wolves_agree = all(target == list(cast.target_dict.values())[0] for target in cast.target_dict.values())
            # 人狼仲間の襲撃先候補が一致したら人狼全員のアクションを終了する
            if wolves_agree:
                vil.casts[target_index].is_targeted = True
                cast.target_dict.clear()
                for wolf in cast.group:
                    sid = vil.players[wolf.id]['sid']
                    wolf.done_action = True
                    message = '襲撃先は' + vil.players[target_index]['name'] + 'さん'
                    emit('message', {'msg': message, 'group_target_dict': wolf.target_dict}, room=sid)
            else:
                # 人狼仲間に襲撃先候補を伝える
                for wolf in cast.group:
                    sid = vil.players[wolf.id]['sid']
                    emit('message', {'group_target_dict': wolf.target_dict}, room=sid)

        elif cast.name in ['占い師', ]:
            if vil.casts[target_index].name == '人狼':
                comment = '人狼'
            else:
                comment = '人狼ではない'
            cast.opencasts[target_index] = comment
            message = vil.players[target_index]['name'] + 'さんは' + comment
            emit('message', {'msg': message, 'casts': cast.opencasts}, room=player['sid'])
            cast.done_action = True

    # 全員のactionが完了した後の処理
    if vil.done_all_actions():
        vil.judge_casts_action()    # 全てのcastのアクションから全体の判定
        vil.phase = '朝'
        gm_sid = ''
        for player in vil.players:
            if player['isGM']:
                gm_sid = player['sid']
        message = '夜のアクションが終了しました'
        emit('message', {'phase': vil.phase}, broadcast=True)
        emit('message', {'msg': message}, room=gm_sid)


@socketio.on('next game')
def next_game():
    vil.player_reset()
    vil.cast_reset()

    vil.phase = '参加受付中'
    message = '参加受付中'
    emit('message', {'players': vil.players, 'phase': vil.phase,'casts': '', 'msg': message}, broadcast=True)


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
            vil.players.pop(player)
            break
    emit('message', {'players': vil.players}, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host='192.168.2.29', port=5000, debug=True)

from testapp import db
from datetime import datetime



class Player(db.Model):
    __tablename__ = 'player'
    id = db.Column(db.Integer, primary_key=True)  # システムで使う番号
    name = db.Column(db.String(255))
    cast = db.Column(db.String(255))
    is_gm = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)  # 作成日時
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)  # 更新日時
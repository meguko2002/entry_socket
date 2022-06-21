import login as login
from flask import Flask
from flask_login import LoginManager, UserMixin, current_user, login_user, \
    logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_session import Session
from datetime import timedelta

app = Flask(__name__)
app.config.from_object('testapp.config')
app.permanent_session_lifetime = timedelta(minutes=30)
app.config['secret_key'] ='sadfsaEFFSAefsa'
app.config['SESSION_TYPE'] = 'filesystem'
socketio = SocketIO(app, manage_session=False)

db = SQLAlchemy(app)
Session(app)
from .models import player

import testapp.views





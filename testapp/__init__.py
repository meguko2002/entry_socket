from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_session import Session
from datetime import timedelta

app = Flask(__name__)
app.config.from_object('testapp.config')
app.secret_key ='sadfsaEFFSAefsa'
app.permanent_session_lifetime = timedelta(minutes=30)
app.config['SESSION_TYPE'] = 'filesystem'
socketio = SocketIO(app, manage_session=False)

db = SQLAlchemy(app)

Session(app)
from .models import player

import testapp.views
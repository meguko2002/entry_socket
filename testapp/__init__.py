from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_object('testapp.config')
socketio = SocketIO(app, manage_session=False)

db = SQLAlchemy(app)
from .models import player

import testapp.views
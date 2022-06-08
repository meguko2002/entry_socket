from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="asvmasASFewaasdEWAF",
        SQLALCHEMY_DATABASE_URI="sqlite:///"+
                                str(Path(Path(__file__).parent.parent, 'local.sqlite')),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=True,
        WTF_CSRF_SECRET_KEY="AfaseafasFAEfsadf",
    )
    db.init_app(app)
    Migrate(app,db)
    csrf.init_app(app)

    from apps.crud import views as crud_views
    app.register_blueprint(crud_views.crud, url_prefix="/crud")

    return app

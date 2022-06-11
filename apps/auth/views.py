from flask import Blueprint, render_template, redirect, url_for, flash, request
from apps.app import db
from apps.crud.models import User
from apps.auth.forms import SignUpForm
from flask_login import login_user

auth = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    static_folder="static"
)


@auth.route('/')
def index():
    return render_template('auth/index.html')


@auth.route("/signup", methods=["POST","GET"])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )
        if user.is_duplicate_email():
            flash("指定のメールアドレスは登録済みです")
            return redirect(url_for("auth.signup"))

        db.session.add(user)
        db.session.commit()
        login_user(user)    # user情報をsessionに格納する

        next_ = request.args.get("next")
        if next_ is None or not next_.startswith("/"):
            next_ = url_for("crud.users")
        return redirect(next_)
    return render_template('auth/signup.html', form=form)
from email_validator import validate_email, EmailNotValidError
from flask import Flask, render_template, url_for, \
    current_app, g, request, redirect, flash, make_response, session
import logging
import os
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail, Message

app = Flask(__name__)
app.config["SECRET_KEY"] = "dkgorepkDRSGresgdsrREG"
app.logger.setLevel(logging.DEBUG)
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER")
app.config["MAIL_PORT"] = os.environ.get("MAIL_PORT")
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS")
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

mail = Mail(app)

toolbar = DebugToolbarExtension(app)


@app.route("/")
def index():
    return "Hello Flaskbook!"


@app.get("/hello/<name>", endpoint="hello-endpoint")
def hello(name):
    return f"Hello, {name}"


@app.get("/name/<name>")
def show_name(name):
    return render_template("index.html", name=name)


@app.get("/contact")
def contact():
    response = make_response(render_template("contact.html"))
    response.set_cookie("flaskbook key", "flaskbook value")
    session["username"] = "ichiro"
    return response


@app.route("/contact/complete", methods=["GET", "POST"])
def contact_complete():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        description = request.form.get('description')
        is_vaild = True

        if not username:
            flash('ユーザ名は必須です')
            is_vaild = False
        if not email:
            flash("メールアドレスは必須です")
            is_vaild = False
        try:
            validate_email(email)
        except EmailNotValidError:
            flash('メールアドレス形式で入力してください')
            is_vaild = False
        if not is_vaild:
            return redirect(url_for("contact"))

        # メールを送る
        send_email(
            email,
            "問い合わせありがとうございました",
            "contact_mail",
            username=username,
            description=description
        )
        flash("問い合わせ内容はメールにて送信しました。問い合わせありがとうございました。")
        return redirect(url_for('contact_complete'))
    return render_template("contact_complete.html")


def send_email(to, subject, template, **kwargs):
    msg = Message(subject, recipients=[to])
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_template(template + ".html", **kwargs)
    mail.send(msg)

# with app.test_request_context("/users?updated=false"):
#     print(request.args.get("updated"))

# with app.test_request_context():
#     print(url_for("index"))
#     print(url_for("hello-endpoint", name="world"))
#     print(url_for("show_name", name="ichiro", page="1"))

# print(current_app)

# ctx=app.app_context()
# ctx.push()
#
# print(current_app.name)
#
# g.connection="my id"
# print(g.connection)

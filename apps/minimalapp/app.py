from email_validator import validate_email, EmailNotValidError
from flask import Flask,render_template, url_for,\
    current_app, g,request,redirect, flash
import logging

app=Flask(__name__)
app.config["SECRET_KEY"]= "dkgorepkDRSGresgdsrREG"
app.logger.setLevel(logging.DEBUG)

@app.route("/")
def index():
    return "Hello Flaskbook!"

@app.get("/hello/<name>",endpoint="hello-endpoint")
def hello(name):
    return f"Hello, {name}"

@app.get("/name/<name>")
def show_name(name):
    return render_template("index.html", name=name)

@app.get("/contact")
def contact():
    return render_template("contact.html")

@app.route("/contact/complete", methods=["GET","POST"])
def contact_complete():
    if request.method == "POST":
        username=request.form.get('username')
        email = request.form.get('email')
        description =request.form.get('description')
        is_vaild=True

        if not username:
            flash('ユーザ名は必須です')
            is_vaild=False
        if not email:
            flash("メールアドレスは必須です")
            is_vaild=False
        try:
            validate_email(email)
        except EmailNotValidError:
            flash('メールアドレス形式で入力してください')
            is_vaild=False
        if not is_vaild:
            return redirect(url_for("contact"))
        # todo メールを送る
        flash("問い合わせ内容はメールにて送信しました。問い合わせありがとうございました。")
        return redirect(url_for('contact_complete'))
    return render_template("contact_complete.html")


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

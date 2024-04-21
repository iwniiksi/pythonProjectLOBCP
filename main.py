from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = ('sqlite:///films.db')

app.config['SQLALCHEMY_DATABASE_URI'] = ('sqlite:///user.db')

app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
db = SQLAlchemy(app)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(300), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return '<Article %r>' % self.id


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    key = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return '<User %r>' % self.id


@app.route('/')
@app.route('/home')
def index():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/create-article', methods=['POST', "GET"])
def create_article():
    if request.method == "POST":
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']

        article = Article(title=title, intro=intro, text=text)

        try:
            db.session.add(article)
            db.session.commit()
            return redirect('/')

        except:
            return "При добавлении статьи произошла ошибка"
    else:
        return render_template("create-article.html")


@app.route('/sign_up', methods=['POST', "GET"])
def register():
    if request.method == "POST":
        nickname = request.form['nickname']
        password = request.form['password']
        key = request.form['key']

        user = User(nickname=nickname, password=password, key=key)

        try:
            db.session.add(user)
            db.session.commit()
            return redirect('/')

        except:
            return "При добавлении статьи произошла ошибка"
    else:
        return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)

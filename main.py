from flask import Flask, render_template, request, redirect
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy import orm
from sqlalchemy.orm import Session
from flask_login import UserMixin
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError

ADMIN_KEY = '123abc456def'


SqlAlchemyBase = orm.declarative_base()

__factory = None


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
db = SQLAlchemy(app)


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    engine = sqlalchemy.create_engine(conn_str, echo=True)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()


class Article(SqlAlchemyBase):
    __tablename__ = 'articles'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    intro = sqlalchemy.Column(sqlalchemy.String(300), nullable=False)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return '<Article %r>' % self.id


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    nickname = sqlalchemy.Column(sqlalchemy.String(20), nullable=False, unique=True)
    password = sqlalchemy.Column(sqlalchemy.String(20), nullable=False)
    is_admin = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.id


@app.route('/')
@app.route('/home')
def index():
    return render_template("index.html")


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/FAQ')
def faq():
    return render_template('faq.html')


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

        is_admin = True if key == ADMIN_KEY else False

        user = User(nickname=nickname, password=password, is_admin=is_admin)

        try:
            db.session.add(user)
            db.session.commit()
            return redirect('/')

        except:
            return "При регистрации произошла ошибка"
    else:
        return render_template("register.html")


if __name__ == "__main__":
    global_init('instance/main.db')
    app.run(debug=True)

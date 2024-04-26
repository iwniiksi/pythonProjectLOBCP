from datetime import datetime, timezone

import sqlalchemy
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import orm
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField, IntegerField
from wtforms.validators import DataRequired

ADMIN_KEY = '123abc456def'  # !!!!!!

SqlAlchemyBase = orm.declarative_base()

__factory = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'key'  # !!!!!!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception('Необходимо указать файл базы данных.')

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    engine = sqlalchemy.create_engine(conn_str, echo=True)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    secret_key = TextAreaField('Секретный ключ (для администраторов)')
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомните меня')
    submit = SubmitField('Войти')


class CardForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    released_year = IntegerField('Год выхода')
    runtime = IntegerField('Продолжительность (в мин)')
    genre = StringField('Жанр/ы')
    director = StringField('Режиссёр')
    submit = SubmitField('Добавить')


class AddScore(FlaskForm):
    score = IntegerField('Целое число от 1 до 10', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class Card(SqlAlchemyBase):
    __tablename__ = 'cards'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    released_year = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    runtime = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    genre = sqlalchemy.Column(sqlalchemy.String(100), nullable=True)
    director = sqlalchemy.Column(sqlalchemy.String(100), nullable=True)
    user_rating = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    list_of_user_ratings = sqlalchemy.Column(sqlalchemy.PickleType(), nullable=True)
    # rating = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    # list_of_ratings = sqlalchemy.Column(sqlalchemy.PickleType, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return '<Card %r>' % self.id

    def update_rating(self):
        summ, amount = 0, 0
        for score, value in self.list_of_user_ratings.items():
            summ += int(score) * value
            amount += value
        rating = summ / amount
        self.user_rating = round(rating, 2)

    def add_score(self, score: int):
        if 1 <= score <= 10:
            lst = self.list_of_user_ratings.copy()
            lst[str(score)] += 1
            self.list_of_user_ratings = lst
            self.update_rating()
        else:
            raise ValueError


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(20), nullable=False, unique=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    image_file = sqlalchemy.Column(sqlalchemy.String(20), nullable=False,
                                   default='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRJx9X1j4gDIYI6mbjf2iO_x3DVLNg2CCvFgmlqIorCsA&s%22')
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now(timezone.utc))
    is_admin = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.image_file}')"


@app.route('/')
@app.route('/home')
def index():
    list_of_last_cards = db.session.query(Card).order_by(Card.created_date).limit(15).all()
    return render_template('index.html', list_of_last_cards=list_of_last_cards)


@app.route('/profile')
def profile():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html')


@app.route('/FAQ')
def faq():
    return render_template('faq.html')


@app.route('/for_admins')
def for_admins():
    return render_template('for_admins.html')


@app.route('/create-article', methods=['POST', 'GET'])
def create_card():
    form = CardForm()
    if current_user.is_authenticated and current_user.is_admin:
        if form.validate_on_submit():
            card = Card(title=form.title.data, released_year=form.released_year.data, runtime=form.runtime.data,
                        genre=form.genre.data, director=form.director.data,
                        list_of_user_ratings={'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0,
                                              '10': 0})
            db.session.add(card)
            db.session.commit()
            return redirect('/')
        else:
            return render_template('create-card.html', form=form)
    else:
        return render_template('create-card.html')


@app.route('/card/<int:card_id>', methods=['GET', 'POST'])
def card(card_id):
    card = db.session.query(Card).filter(Card.id == card_id).first()
    if card:
        return render_template('card.html', card=card)
    else:
        return render_template('messages.html', message='Такого фильма или сериала не найдено')


@app.route('/add-score/<int:card_id>', methods=['GET', 'POST'])
def add_score(card_id):
    card = db.session.query(Card).filter(Card.id == card_id).first()
    if card:
        if current_user.is_authenticated:
            form = AddScore()
            if form.validate_on_submit():
                score = form.score.data
                card.add_score(score)
                db.session.commit()
                return redirect(f'/card/{card_id}')
            return render_template('add-score.html', form=form)
        return render_template('add-score.hrml', message='Вы не авторизованы', form=form)
    return render_template('messages.html', message='Такого фильма или сериала не найдено')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/sign_up', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message='Пароли не совпадают')
        if db.session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message='Такой пользователь уже есть')
        is_admin = True if form.secret_key.data == ADMIN_KEY else False
        user = User(name=form.name.data, email=form.email.data, is_admin=is_admin)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect('/')
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    global_init('instance/main.db')
    # app.run(debug=True)
    app.run()

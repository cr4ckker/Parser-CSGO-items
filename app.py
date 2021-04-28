import sys, datetime  

from flask import Flask, render_template, request, redirect, url_for, abort, session
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

from markupsafe import escape
from typing import List

from models import db, Item_Data, User
from Funcs import ParseService, Theme_session
# from forms import ArticleForm, RegistrationForm, LoginForm

app = Flask(__name__)
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Items.db'
app.config['SECRET_KEY'] = 'Super_secret'
app.permanent_session_lifetime = datetime.timedelta(days=365)
db.app = app
db.init_app(app)
migrate = Migrate(app, db)
Bootstrap(app)
login_manager = LoginManager(app)
db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
def Main():
    return render_template('/index.html', theme = Theme_session(session))

@app.route('/items', methods=["GET", "POST"])
@login_required
def parser():
    if request.method == 'GET':
        Items: List[Item_Data] = Item_Data.query.filter(Item_Data.steamtm_csgotm_mp >= 0.4).filter(Item_Data.steamtm_csgotm_mp <= 1.6).order_by(Item_Data.value.asc()).limit(10).all()
        return render_template('/check.html', theme = Theme_session(session), Items = Items)
    else:
        Items = Item_Data.query.filter(Item_Data.steamtm_csgotm_mp >= 0.4).filter(Item_Data.steamtm_csgotm_mp <= 1.6)
        
        if request.args.get('entries'):
            entries = int(request.args.get('entries'))
        else:
            entries = 10
        if request.args.get('name'):
            Items = Items.filter(Item_Data.name.like(f"%{request.args.get('name')}%"))
        if request.args.get('csgo500'):
            Items = Items.filter(Item_Data.cost.like(f"%{request.args.get('csgo500')}%")) if request.args.get('csgo500')[0] not in ['>', '<'] else Items.filter(Item_Data.cost < int(request.args.get('csgo500')[1::])) if request.args.get('csgo500')[0] == '<' else Items.filter(Item_Data.cost > int(request.args.get('csgo500')[1::]))
        if request.args.get('csgotm'):
            Items = Items.filter(Item_Data.csgotm_value.like(f"%{request.args.get('csgotm')}%")) if request.args.get('csgotm')[0] not in ['>', '<'] else Items.filter(Item_Data.csgotm_value < int(request.args.get('csgotm')[1::])) if request.args.get('csgotm')[0] == '<' else Items.filter(Item_Data.csgotm_value > int(request.args.get('csgotm')[1::]))
        if request.args.get('csgotmv'):
            Items = Items.filter(Item_Data.csgotm_volume.like(f"%{request.args.get('csgotmv')}%")) if request.args.get('csgotmv')[0] not in ['>', '<'] else Items.filter(Item_Data.csgotm_volume < int(request.args.get('csgotmv')[1::])) if request.args.get('csgotmv')[0] == '<' else Items.filter(Item_Data.csgotm_volume > int(request.args.get('csgotmv')[1::]))
        if request.args.get('steamtm'):
            Items = Items.filter(Item_Data.steamtm_value.like(f"%{request.args.get('steamtm')}%")) if request.args.get('steamtm')[0] not in ['>', '<'] else Items.filter(Item_Data.steamtm_value < int(request.args.get('steamtm')[1::])) if request.args.get('steamtm')[0] == '<' else Items.filter(Item_Data.steamtm_value > int(request.args.get('steamtm')[1::])) 
        if request.args.get('steamtmv'):
            Items = Items.filter(Item_Data.steamtm_volume.like(f"%{request.args.get('steamtmv')}%")) if request.args.get('steamtmv')[0] not in ['>', '<'] else Items.filter(Item_Data.steamtm_volume < int(request.args.get('steamtmv')[1::])) if request.args.get('steamtmv')[0] == '<' else Items.filter(Item_Data.steamtm_volume > int(request.args.get('steamtmv')[1::]))
        if request.args.get('last_check'):
            Items = Items.filter(Item_Data.last_check.like(f"%{request.args.get('last_check')}%")) 
        items: List[Item_Data] = Items.limit(entries).all() 
        return render_template('/DB_table.html', Items = items)

@app.route('/about')
def about():
    return render_template('/about.html', theme = Theme_session(session))
                           
@app.route('/auth', methods=["GET", "POST"])
def auth():
    if not current_user.is_authenticated:
        if request.method == 'POST':
            if request.args.get('mode') == 'login':
                login = request.args.get('login')
                password = request.args.get('password')
                user: User = User.query.filter_by(username=login).first()
                if user is None or not user.check_password(password):
                    return {'success':False, 'error':'Неверный логин или пароль!'}
                login_user(user)
                return {'success':True, 'error':None}
            elif request.args.get('mode') == 'register':
                login = request.args.get('login')
                password = request.args.get('password')
                user = User.query.filter(User.username.like(login)).first()
                if user is not None:
                    return {'success':False, 'error':'Пользователь с данным логином уже существует!'}
                user = User(username=login)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return {'success':True, 'error':None}
            else:
                return {'success':False, 'error':'Неизвестный режим'}
        return render_template('login.html', theme = Theme_session(session))
    else:
        return redirect(url_for('Main'))

@app.route('/ThemeSave', methods=["POST"])
def ThemeSave():
    session['Theme'] = request.args.get('theme')
    session.modified = True
    return ''

@app.route('/logout', methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("Main"))

@app.errorhandler(401)
def Unauthorized(error):
    return redirect(url_for("Main"))

@app.after_request
def add_header(r):
    r.headers['Cache-Control'] = 'public, max-age=3600'
    r.headers['Expires'] = '3600'
    r.headers['Access-Control-Allow-Origin'] = '*'
    r.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
    return r

if __name__ == '__main__':
    app.run()

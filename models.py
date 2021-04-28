from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from hashlib import sha256

db = SQLAlchemy()

class Item_Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cost = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(60), nullable=False, unique=True)
    vanilla = db.Column(db.Boolean, nullable=False)
    st = db.Column(db.Boolean, nullable=False)
    souvenir = db.Column(db.Boolean, nullable=False)
    item_name = db.Column(db.String(60), nullable=False)
    skin = db.Column(db.String(60), nullable=False)
    float_type = db.Column(db.String(60), nullable=False)
    last_check = db.Column(db.Integer)
    csgotm_volume = db.Column(db.Integer)
    csgotm_value = db.Column(db.Float)
    csgotm_lastbuy = db.Column(db.Integer)
    csgotm_in_mp = db.Column(db.Float)
    csgotm_out_mp = db.Column(db.Float)
    steamtm_volume = db.Column(db.Integer)
    steamtm_value = db.Column(db.Float)
    steamtm_csgotm_mp = db.Column(db.Float)
    steamtm_in_mp = db.Column(db.Float)
    steamtm_out_mp = db.Column(db.Float)

    def __repr__(self):
        return f"Item_Data({self.id}, {self.cost}, {self.value}, {self.name}, {self.vanilla}, {self.st}, {self.souvenir}, {self.item_name}, {self.skin}, {self.float_type}, {self.last_check}, {self.csgotm_volume}, {self.csgotm_value}, {self.csgotm_lastbuy}, {self.csgotm_in_mp}, {self.csgotm_out_mp}, {self.steamtm_volume}, {self.steamtm_value}, {self.steamtm_csgotm_mp}, {self.steamtm_in_mp}, {self.steamtm_out_mp})"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)

    def __repr__(self):
        return f"User({self.id}, {self.login}, {self.password})"

    def set_password(self, password):
        self.password = sha256(password.encode("utf-8")).hexdigest()

    def check_password(self, password):
        if self.password == sha256(password.encode("utf-8")).hexdigest():
            return True
        return False


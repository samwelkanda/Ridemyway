from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from flask_login import UserMixin
from app import login
from hashlib import md5


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    car_details = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    rides = db.relationship('Ride', backref='driver', lazy='dynamic')
    requests = db.relationship('Request', backref='requester', lazy='dynamic')


    def __repr__(self):
        return '<User {}>'.format(self.username) 
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.String(40))
    destination = db.Column(db.String(40))
    time = db.Column(db.String(40))
    seats = db.Column(db.Integer)
    cost = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    requests = db.relationship('Request', backref='ride', lazy='dynamic')


    def __repr__(self):
        return '<Ride {}>'

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pickup = db.Column(db.String(40))
    time = db.Column(db.String(40))
    seats = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'))


    def __repr__(self):
        return '<Request {}>'

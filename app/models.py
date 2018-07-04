from datetime import datetime
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    rides = db.relationship('Ride', backref='driver', lazy='dynamic')
    requests = db.relationship('Request', backref='requester', lazy='dynamic')


    def __repr__(self):
        return '<User {}>'.format(self.username)  

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

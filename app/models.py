from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login
import json
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt
from flask import current_app
from app.search import add_to_index, remove_from_index, query_index

class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    car_details = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    rides = db.relationship('Ride', backref='driver', lazy='dynamic')
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='driver', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='message_recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    messagenotifications = db.relationship('MessageNotification', backref='user',
                                    lazy='dynamic')
    requests_sent = db.relationship('Request',
                                    foreign_keys='Request.sender_id',
                                    backref='driver', lazy='dynamic')
    requests_received = db.relationship('Request',
                                        foreign_keys='Request.recipient_id',
                                        backref='request_recipient', lazy='dynamic')
    last_request_read_time = db.Column(db.DateTime)
    requestnotifications = db.relationship('RequestNotification', backref='user',
                                    lazy='dynamic')


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

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_rides(self):
        followed = Ride.query.join(
            followers, (followers.c.followed_id == Ride.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Ride.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Ride.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
    
    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(message_recipient=self).filter(
            Message.timestamp > last_read_time).count()

    def add_messagenotification(self, name, data):
        self.messagenotifications.filter_by(name=name).delete()
        n = MessageNotification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def new_requests(self):
        last_read_time = self.last_request_read_time or datetime(1900, 1, 1)
        return Request.query.filter_by(request_recipient=self).filter(
            Request.timestamp > last_read_time).count()

    def add_requestnotification(self, name, data):
        self.requestnotifications.filter_by(name=name).delete()
        r = RequestNotification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(r)
        return r

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Ride(SearchableMixin, db.Model):
    __searchable__ = ['start','destination']
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.String(40))
    destination = db.Column(db.String(40))
    time = db.Column(db.String(40))
    seats = db.Column(db.Integer)
    cost = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


    def __repr__(self):
        return '<Ride {}>'

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pickup = db.Column(db.String(40))
    time = db.Column(db.String(40))
    seats = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Request {}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)

class MessageNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))

class RequestNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


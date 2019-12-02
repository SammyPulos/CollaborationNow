from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from app import db
from app import login
from hashlib import md5
import json
from time import time

listing_user_assoc = db.Table('listing_user_assoc',
	db.Column('listing_id', db.Integer, db.ForeignKey('listing.id')),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

listing_interested_user_assoc = db.Table('listing_interested_user_assoc',
	db.Column('listing_id', db.Integer, db.ForeignKey('listing.id')),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	major = db.Column(db.String(64), default='')
	listings = db.relationship('Listing', backref='owner', lazy='dynamic')
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)
	messages_sent = db.relationship('Message',
									foreign_keys='Message.sender_id',
									backref='sender', lazy='dynamic')
	messages_received = db.relationship('Message',
										foreign_keys='Message.recipient_id',
										backref='recipient', lazy='dynamic')
	last_message_read_time = db.Column(db.DateTime)
	notifications = db.relationship('Notification', backref='user',
									lazy='dynamic')

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def avatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

	def new_messages(self):
		last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
		return Message.query.filter_by(recipient=self).filter(
			Message.timestamp > last_read_time).count()

	def add_notification(self, name, data):
		self.notifications.filter_by(name=name).delete()
		n = Notification(name=name, payload_json=json.dumps(data), user=self)
		db.session.add(n)
		return n

	def __repr__(self):
		return '<User {}>'.format(self.email)

listing_tag_assoc = db.Table('listing_tag_assoc',
	db.Column('listing_id', db.Integer, db.ForeignKey('listing.id')),
	db.Column('tag_id', db.Integer, db.ForeignKey('listing_tag.id'))
)

class Listing(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(64))
	body = db.Column(db.String(1024))
	desired_size = db.Column(db.Integer, default=2) 
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	is_complete = db.Column(db.Boolean, default=False)
	tags = db.relationship("ListingTag", secondary=listing_tag_assoc, backref="tagged_listing")
	members = db.relationship("User", secondary=listing_user_assoc, backref="joined_listing")
	interested_users = db.relationship("User", secondary=listing_interested_user_assoc, backref="interesting_listing")
	def __repr__(self):
		return '<Listing {}>'.format(self.title)

class ListingTag(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	tag = db.Column(db.String(32), unique=True)

	def __repr__(self):
		return '<ListingTag {}>'.format(self.tag)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

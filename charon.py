from flask import Flask, make_response, flash, request, render_template, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound #, MultipleResultsFound
import json, datetime, sys

from flask.ext.uploads import UploadSet, IMAGES, AUDIO, configure_uploads  #http://pythonhosted.org/Flask-Uploads/

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/charon.db'  #change to postgres database
app.config['SECRET_KEY'] = '123charon456'
db = SQLAlchemy(app)

#
# Models
#

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(64))

    def __init__(self, email, password):
        self.email = email
        self.password = make_hash(password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.email

    def __unicode__(self):
        return unicode(self.email)


class Parent(db.Model):
    __tablename__ = 'parents'
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(80))
    l_name = db.Column(db.String(80))
    street = db.Column(db.String(80))
    city = db.Column(db.String(80))
    zip = db.Column(db.Integer) #better fix width type?
    user = db.Column(db.Integer) #relationship??
    phone = db.Column(db.String(14))
    children = db.relationship('Student', back_populates="parents") # backref=db.backref('parents')


    def __init__(self, f_name, l_name, street, city, zip, user, phone, children):
        self.f_name = f_name
        self.l_name = l_name
        self.street = street
        self.city = city
        self.zip = zip
        self.user = user
        self.phone = phone
        self.children = children
        
    def __repr__(self):
        return '<Parent %r %r>' % self.f_name, self.l_name

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(80))
    l_name = db.Column(db.String(80))
    siblings = db.relationship('Student', 
    parents = db.relationship('Parent', backref='children')
    probability = db.Column(db.Float)
    gender = db.Column(db.Integer) #0-Female, 1-Male; Use Enum in Postgres??
    dob = db.Column(db.Date)
    finaid = 
    state
    classroom = 
    friends = relationship("Student",
                    secondary=friends_table,
                    backref="friends")
    good_influences
    stretches
    intellectual_peers

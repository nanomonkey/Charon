from flask import Flask, make_response, flash, request, render_template, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound #, MultipleResultsFound
import json, datetime, sys

from flask.ext.login import LoginManager, login_user, logout_user, login_required
import hashlib
from os import urandom, path
from base64 import b64encode, b64decode
from itertools import izip

from flask.ext.uploads import UploadSet, IMAGES, AUDIO, configure_uploads  #http://pythonhosted.org/Flask-Uploads/

# From https://github.com/mitsuhiko/python-pbkdf2
from pbkdf2 import pbkdf2_bin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/charon.db'  #change to postgres database
app.config['SECRET_KEY'] = '123charon456'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

#
# Password Hashing and Login
#

# Parameters to PBKDF2. Only affect new passwords.
SALT_LENGTH = 12
KEY_LENGTH = 24
HASH_FUNCTION = 'sha256'  # Must be in hashlib.
# Linear to the hashing time. Adjust to be high but take a reasonable
# amount of time on your server. Measure with:
# python -m timeit -s 'import passwords as p' 'p.make_hash("something")'
COST_FACTOR = 10000


def make_hash(password):
    """Generate a random salt and return a new hash for the password."""
    if isinstance(password, unicode):
        password = password.encode('utf-8')
    salt = b64encode(urandom(SALT_LENGTH))
    return 'PBKDF2${}${}${}${}'.format(
        HASH_FUNCTION,
        COST_FACTOR,
        salt,
        b64encode(pbkdf2_bin(password, salt, COST_FACTOR, KEY_LENGTH,
                             getattr(hashlib, HASH_FUNCTION))))

def check_hash(password, hash_):
    """Check a password against an existing hash."""
    if isinstance(password, unicode):
        password = password.encode('utf-8')
    algorithm, hash_function, cost_factor, salt, hash_a = hash_.split('$')
    assert algorithm == 'PBKDF2'
    hash_a = b64decode(hash_a)
    hash_b = pbkdf2_bin(password, salt, int(cost_factor), len(hash_a),
                        getattr(hashlib, hash_function))
    assert len(hash_a) == len(hash_b)  # we requested this from pbkdf2_bin()
    # Same as "return hash_a == hash_b" but takes a constant time.
    # See http://carlos.bueno.org/2011/10/timing.html
    diff = 0
    for char_a, char_b in izip(hash_a, hash_b):
        diff |= ord(char_a) ^ ord(char_b)
    return diff == 0

def try_login_user(email, password):
    if not password:
        return None
    try:
        user = User.query.filter_by(email=email).one()
    except NoResultFound:
        return None
    if not check_hash(password, user.password):
        return None
    login_user(user)
    return user


@login_manager.user_loader
def load_user(userid):
    return User.query.get(int(userid))

login_manager.login_view = "login"

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
    email = db.Column(db.String(120))
    password = db.Column(db.String(64))
    oath = db.Column(db.String(64)) # to be determined
    phone = db.Column(db.String(14))
    children = db.relationship('Student', back_populates="parents") # backref=db.backref('parents')


    def __init__(self, f_name, l_name, street, city, zip, email, password, oath, phone, children):
        self.f_name = f_name
        self.l_name = l_name
        self.street = street
        self.city = city
        self.zip = zip
        self.email = email
        self.password = password
        self.oath = oath
        self.phone = phone
        self.children = children
        
    def __repr__(self):
        return '<Parent %r %r>' % self.f_name, self.l_name


#
# Views
#

@app.route('/')
@app.route('/index')
def index():
    """Return the main view."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = try_login_user(email, password)
        if user is None:
            error = u'Login failed'
            flash(error)
        else:
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    logout_user()
    flash(u'You were logged out')
    return redirect(url_for('index'))


from flask import Flask, make_response, flash, request, render_template, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound #, MultipleResultsFound
import json, datetime, sys
from flask.ext.uploads import UploadSet, IMAGES, AUDIO, configure_uploads  #http://pythonhosted.org/Flask-Uploads/

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/charon'  
app.config['SECRET_KEY'] = '123charon456'
db = SQLAlchemy(app)

#
# Models
#

PARENT = 0
TEACHER = 1
ADMIN = 2

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)  #use email as primary key instead??
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String(64))
    access = db.Column(db.SmallInteger, default = PARENT)

    @validates('email')
    def validate_email(self, key, address):
        assert '@' in address
        assert '.' in address
        return address
        
    def __init__(self, email, password, access):
        self.email = email
        self.password = make_hash(password)
        self.level = access
    
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

children = db.Table('children',
    db.Column('parent_id', db.Integer, db.ForeignKey('parents.id')),
    db.Column('child_id', db.Integer, db.ForeignKey('students.id'))
)

class Parent(db.Model):
    __tablename__ = 'parents'
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(80))
    l_name = db.Column(db.String(80))
    street = db.Column(db.String(80))
    city = db.Column(db.String(80))
    zip = db.Column(db.Integer) #fix width type?
    email = db.Column(db.Integer, ForeignKey("user.email"), nullable=False) 
    phone = db.Column(db.String(14))
    children = db.relationship('Student', 
        secondary = children, 
        primaryjoin = (children.c.parent_id == id), 
        secondaryjoin = (children.c.child_id == student.id), 
        backref = db.backref('children', lazy = 'dynamic'), 
        lazy = 'dynamic')

    def __init__(self, f_name, l_name, street, city, zip, user, phone):
        self.f_name = f_name
        self.l_name = l_name
        self.street = street
        self.city = city
        self.zip = zip
        self.user = user
        self.phone = phone
    
    def add_child(self, student):
        if not self.is_child(parent):
            self.children.append(student)
            return self

    def remove_child(self, student):
        if self.is_child(student):
            self.children.remove(student)
            return self
            
    def is_child(self, student):
        return self.children.filter(children.c.child_id == student.id).count() > 0
        
    def __repr__(self):
        return '<Parent %r %r>' % self.f_name, self.l_name


friends = db.Table('friends',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id')),
    db.Column('friend_id', db.Integer, db.ForeignKey('students.id'))
)


good_influences = db.Table('good_influences',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id')),
    db.Column('good_id', db.Integer, db.ForeignKey('students.id'))
)


stretches = db.Table('stretches',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id')),
    db.Column('stretch_id', db.Integer, db.ForeignKey('students.id'))
)


intellectual_peers = db.Table('intellectual_peers',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id')),
    db.Column('peers_id', db.Integer, db.ForeignKey('students.id'))
)


class ClassComposition(Base):
    __tablename__ = 'class_composition'
    student_id = Column(db.Integer, ForeignKey('students.id'), primary_key=True)
    classroom_id = Column(db.Integer, ForeignKey('classrooms.id'), primary_key=True)
    start_date = db.Column(db.Date, default=(classrooms.c.start_date))
    end_date = db.Column(db.Date, default=(classrooms.c.end_date))
    student = relationship("Student", backref="classroom")
    classroom = relationship("Classroom", backref="student")
    
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
    

class Location(Base):
    __tablename__ = 'locations'
    name = Column(db.String)
    address = Column(db.String)
    city = Column(db.String)
    zipcode = Column(db.String)
    classrooms = relationship("Classroom", backref = "location")
    
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return '<Location %r>' % self.name
    
    
class Classroom(Base):
    __tablename__ = 'classrooms'
    name = Column(db.String, nullable=False, unique=True)
    description = Column(db.Text)
    tuition = Column(db.Decimal, precision=2)
    grade_levels = Column(db.String) # comma separated list of grades?  endpoints (k-8)?
    program = Column(db.SmallInt) #0:K1, 1:2-5, 2:6-8
    capacity = Column(db.Integer) 
    start_date = Column(db.Date)
    end_date = Column(db.Date)
    status = Column(db.SmallInt) #0:Active, 1:Canceled
    location = relationship("Location", backref="classrooms")
    teachers = relationship("Teacher", backref="classrooms")
    students = relationship("Students", backref="classrooms")
    waitlist = relationship("Students", backref="waitlist")
    
    def __init__(self, name, description="", tuition, capacity, start_date, end_date, status=0):
        self.name = name
        self.description = description
        self.tuition = tuition
        self.capacity = capacity
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
    
    def __repr__(self):
        return '<Classroom %r>' % self.name
     

ACTIVE = 0
WAIT_LIST = 1
ICE_BOX = 2

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(80))
    l_name = db.Column(db.String(80)) 
    parents = db.relationship('Parent', backref='children')
    gender = db.Column(db.Integer) # 0-Female, 1-Male; Use Enum in Postgres??
    dob = db.Column(db.Date)
    state = db.Column(db.SmallInteger, default=ACTIVE)  #ACTIVE, WAIT_LIST, ICE_BOX
    classroom = db.relationship('Classroom',
        secondary = class_composition,
        primaryjoin = (class_composition.c.student_id == id),
        secondaryjoin = (class_composition.c.class_id == classes.id)
        backref = db.backref('students', lazy = 'dynamic')
        lazy = 'dynamic')
    friends = db.relationship('Student', 
        secondary = friends, 
        primaryjoin = (friends.c.student_id == id), 
        secondaryjoin = (friends.c.friend_id == id), 
        backref = db.backref('friends', lazy = 'dynamic'), 
        lazy = 'dynamic')
    good_influences= db.relationship('Student', 
        secondary = good_influences, 
        primaryjoin = (good_influences.c.student_id == id), 
        secondaryjoin = (good_influences.c.good_id == id), 
        backref = db.backref('good_influences', lazy = 'dynamic'), 
        lazy = 'dynamic')
    stretches = db.relationship('Student',
        secondary = stretches,
        primaryjoin = (stretches.c.student_id == id),
        secondaryjoin = (stretches.c.stretch_id == id),
        backref = db.backref('stretches', lazy = 'dynamic'),
        lazy = 'dynamic')
    intellectual_peers = db.relationship('Student',
        secondary = intellectual_peers,
        primaryjoin = (intellectual_peers.c.student_id == id),
        secondaryjoin = (intellectual_peers.c.peers_id == id),
        backref = db.backref('intellectual_peers', lazy = 'dynamic'),
        lazy = 'dynamic')

    def __init__(self, f_name, l_name, gender, dob, state=ACTIVE):
        self.f_name = f_name
        self.l_name = l_name
        self.gender = gender
        self.dob = dob
        self.state = state
    
    def add_parent(self, parent):
        parent.add_child(self)
        
    def remove_parent(self, parent):
        parent.remove_child(self)
    
    def add_friend(self, student):
        if not self.is_friend(student):
            self.friends.append(student)
            return self

    def remove_friend(self, student):
        if self.is_friend(student):
            self.friends.remove(student)
            return self
            
    def is_friend(self, student):
        return self.friends.filter(friends.c.friend_id == student.id).count() > 0
            
    def add_to_class(classroom, start, end):
        if not self.in_class(classroom, start, end):
            pass
        return self
    
    def in_class(classroom, start, end):
        return self.classroom.filter(class_composition.c.student == self.id, class_composition.c.start_date > start, class_compostion.end_date < end).count()>0   
    
    def __repr__(self):
        return '<Student %r %r>' % self.f_name, self.l_name
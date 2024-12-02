from datetime import datetime
from flask_login import UserMixin
import random
import string
from flask_sqlalchemy import SQLAlchemy
from extensions import db


# Association table for many-to-many relationship between User and Role
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id', ondelete='CASCADE'), primary_key=True)
)

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    org_type = db.Column(db.String(150), nullable=False)
    users = db.relationship('User', backref='organization', lazy=True)

    org_code = db.Column(db.String(10), unique=True)
    admin_access_code = db.Column(db.String(10), unique=True)
    teacher_access_code = db.Column(db.String(10), unique=True)
    student_access_code = db.Column(db.String(10), unique=True)
    user_access_code = db.Column(db.String(10), unique=True)

    def generate_access_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def __init__(self, name, org_type):
        self.name = name
        self.org_type = org_type
        self.org_code = self.generate_access_code()
        self.admin_access_code = self.generate_access_code()

        if org_type == "School":
            self.teacher_access_code = self.generate_access_code()
            self.student_access_code = self.generate_access_code()

        elif org_type == "General Org":
            self.user_access_code = self.generate_access_code()

    def __repr__(self):
        return f"Organization ('{self.name}','{self.org_type}')"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('user', lazy=True))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    role = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"Role('{self.name}')"

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    entry_code = db.Column(db.String(8), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)

    teacher = db.relationship('User', backref='classes')
    students = db.relationship('User', secondary='class_students', backref='enrolled_classes')

    def __init__(self, name, subject, teacher_id):
        self.name = name
        self.subject = subject
        self.teacher_id = teacher_id
        self.entry_code = self.generate_entry_code()

    def generate_entry_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class_students = db.Table('class_students',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class SightingReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(120), nullable=True)
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('sightings', lazy=True))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    feedback = db.Column(db.Text, nullable = True)
    is_public = db.Column(db.Boolean, default=True)  # Privacy toggle

    def __repr__(self):
        return f"SightingReport('{self.description}', '{self.location}', '{self.date_reported}')"

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('activities', lazy=True))

    def __repr__(self):
        return f"Activity('{self.name}', '{self.date_uploaded}')"

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    is_closed = db.Column(db.Boolean, default=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)


    class_ = db.relationship('Class', backref='assignments')

    # Use a unique backref name to avoid conflicts
    submissions = db.relationship('Submission', backref='related_assignment', lazy=True)

    def __repr__(self):
        return f"Assignment('{self.title}', due {self.deadline}, closed={self.is_closed})"

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)  
    file_path = db.Column(db.String(120), nullable=True) 
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feedback = db.Column(db.Text, nullable = True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)

    # Establish relationship with User and Assignment
    student = db.relationship('User', backref=db.backref('submissions', lazy=True))

    def __repr__(self):
        return f"Submission('Assignment ID: {self.assignment_id}', 'Submitted by: {self.student_id}')"

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='recieved_messages')

    def __repr__(self):
        return f"<Message {self.message_text[:20]} from {self.sender_id} to {self.recipient_id}>"
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(300), nullable=True)  # For uploaded documents
    photo = db.Column(db.String(300), nullable=True)  # For uploaded images
    link = db.Column(db.String(300), nullable=True)  # For external links
    is_public = db.Column(db.Boolean, default=True)  # Privacy toggle
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='posts')
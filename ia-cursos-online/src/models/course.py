from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    courses = db.relationship('Course', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    level = db.Column(db.String(50), nullable=False)  # iniciante, intermediário, avançado
    duration = db.Column(db.Integer, nullable=False)  # duração em minutos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    modules = db.relationship('Module', backref='course', lazy=True, cascade="all, delete-orphan")
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    reviews = db.relationship('Review', backref='course', lazy=True)
    
    def average_rating(self):
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)
    
    def student_count(self):
        return len(self.enrollments)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subtitle': self.subtitle,
            'description': self.description,
            'price': self.price,
            'discount_price': self.discount_price,
            'image_url': self.image_url,
            'level': self.level,
            'duration': self.duration,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'category': self.category.to_dict(),
            'instructor_id': self.instructor_id,
            'average_rating': self.average_rating(),
            'student_count': self.student_count()
        }

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=False)
    
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    lessons = db.relationship('Lesson', backref='module', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'order': self.order,
            'course_id': self.course_id,
            'lessons': [lesson.to_dict() for lesson in self.lessons]
        }

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # duração em minutos
    order = db.Column(db.Integer, nullable=False)
    
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    
    materials = db.relationship('Material', backref='lesson', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'video_url': self.video_url,
            'duration': self.duration,
            'order': self.order,
            'module_id': self.module_id,
            'materials': [material.to_dict() for material in self.materials]
        }

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # pdf, link, template
    url = db.Column(db.String(255), nullable=False)
    
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type,
            'url': self.url,
            'lesson_id': self.lesson_id
        }

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    progress = db.relationship('Progress', backref='enrollment', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'completed': self.completed,
            'user_id': self.user_id,
            'course_id': self.course_id
        }

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    last_watched = db.Column(db.DateTime, default=datetime.utcnow)
    
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollment.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'lesson_id': self.lesson_id,
            'completed': self.completed,
            'last_watched': self.last_watched.isoformat(),
            'enrollment_id': self.enrollment_id
        }

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'comment': self.comment,
            'date': self.date.isoformat(),
            'user_id': self.user_id,
            'course_id': self.course_id
        }

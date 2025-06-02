from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='BRL', nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pending, completed, failed, refunded
    payment_method = db.Column(db.String(20), nullable=False)  # credit_card, pix, boleto
    payment_id = db.Column(db.String(255), nullable=True)  # ID externo do gateway de pagamento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_id': self.payment_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_id': self.user_id,
            'course_id': self.course_id
        }

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")
    
    def total(self):
        return sum(item.price for item in self.items)
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_id': self.user_id,
            'items': [item.to_dict() for item in self.items],
            'total': self.total()
        }

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    course = db.relationship('Course')
    
    def to_dict(self):
        return {
            'id': self.id,
            'price': self.price,
            'cart_id': self.cart_id,
            'course_id': self.course_id,
            'course': self.course.to_dict()
        }

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount_percent = db.Column(db.Integer, nullable=False)
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)
    max_uses = db.Column(db.Integer, nullable=True)
    current_uses = db.Column(db.Integer, default=0)
    
    def is_valid(self):
        now = datetime.utcnow()
        return (self.valid_from <= now <= self.valid_until and 
                (self.max_uses is None or self.current_uses < self.max_uses))
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'discount_percent': self.discount_percent,
            'valid_from': self.valid_from.isoformat(),
            'valid_until': self.valid_until.isoformat(),
            'max_uses': self.max_uses,
            'current_uses': self.current_uses,
            'is_valid': self.is_valid()
        }

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    certificate_url = db.Column(db.String(255), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'issue_date': self.issue_date.isoformat(),
            'certificate_url': self.certificate_url,
            'user_id': self.user_id,
            'course_id': self.course_id
        }

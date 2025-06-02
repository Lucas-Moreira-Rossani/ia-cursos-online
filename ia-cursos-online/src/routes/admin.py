from flask import Blueprint, request, jsonify, current_app
from src.models.user import db, User
from src.routes.auth import token_required
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@token_required
def admin_dashboard(current_user):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    # Estatísticas gerais (simuladas)
    from src.models.course import Course, Enrollment, Review
    from src.models.payment import Payment
    
    total_users = User.query.count()
    total_courses = Course.query.count()
    total_enrollments = Enrollment.query.count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter_by(status='completed').scalar() or 0
    
    # Usuários recentes
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Matrículas recentes
    recent_enrollments = db.session.query(
        Enrollment, User, Course
    ).join(
        User, User.id == Enrollment.user_id
    ).join(
        Course, Course.id == Enrollment.course_id
    ).order_by(
        Enrollment.date.desc()
    ).limit(5).all()
    
    recent_enrollments_data = []
    for enrollment, user, course in recent_enrollments:
        recent_enrollments_data.append({
            'id': enrollment.id,
            'date': enrollment.date.isoformat(),
            'user': {
                'id': user.id,
                'username': user.username
            },
            'course': {
                'id': course.id,
                'title': course.title
            }
        })
    
    # Pagamentos recentes
    recent_payments = db.session.query(
        Payment, User, Course
    ).join(
        User, User.id == Payment.user_id
    ).join(
        Course, Course.id == Payment.course_id
    ).order_by(
        Payment.created_at.desc()
    ).limit(5).all()
    
    recent_payments_data = []
    for payment, user, course in recent_payments:
        recent_payments_data.append({
            'id': payment.id,
            'amount': payment.amount,
            'status': payment.status,
            'payment_method': payment.payment_method,
            'created_at': payment.created_at.isoformat(),
            'user': {
                'id': user.id,
                'username': user.username
            },
            'course': {
                'id': course.id,
                'title': course.title
            }
        })
    
    return jsonify({
        'statistics': {
            'total_users': total_users,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'total_revenue': total_revenue
        },
        'recent_users': [user.to_dict() for user in recent_users],
        'recent_enrollments': recent_enrollments_data,
        'recent_payments': recent_payments_data
    }), 200

@admin_bp.route('/users', methods=['GET'])
@token_required
def admin_users(current_user):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
def admin_user_detail(current_user, user_id):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuário não encontrado!'}), 404
    
    from src.models.course import Enrollment
    from src.models.payment import Payment
    
    enrollments = Enrollment.query.filter_by(user_id=user_id).all()
    payments = Payment.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'user': user.to_dict(),
        'enrollments': [enrollment.to_dict() for enrollment in enrollments],
        'payments': [payment.to_dict() for payment in payments]
    }), 200

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@token_required
def update_user_role(current_user, user_id):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuário não encontrado!'}), 404
    
    data = request.get_json()
    if not data or not data.get('role'):
        return jsonify({'message': 'Função não fornecida!'}), 400
    
    role = data['role']
    if role not in ['student', 'instructor', 'admin']:
        return jsonify({'message': 'Função inválida!'}), 400
    
    user.role = role
    db.session.commit()
    
    return jsonify({
        'message': 'Função do usuário atualizada com sucesso!',
        'user': user.to_dict()
    }), 200

@admin_bp.route('/courses', methods=['GET'])
@token_required
def admin_courses(current_user):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    from src.models.course import Course
    
    courses = Course.query.all()
    return jsonify([course.to_dict() for course in courses]), 200

@admin_bp.route('/courses', methods=['POST'])
@token_required
def create_course(current_user):
    if not current_user.is_admin() and not current_user.is_instructor():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('description') or not data.get('price') or not data.get('level') or not data.get('category_id'):
        return jsonify({'message': 'Dados incompletos!'}), 400
    
    from src.models.course import Course, Category
    
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({'message': 'Categoria não encontrada!'}), 404
    
    course = Course(
        title=data['title'],
        subtitle=data.get('subtitle'),
        description=data['description'],
        price=data['price'],
        discount_price=data.get('discount_price'),
        image_url=data.get('image_url'),
        level=data['level'],
        duration=data.get('duration', 0),
        category_id=data['category_id'],
        instructor_id=current_user.id
    )
    
    db.session.add(course)
    db.session.commit()
    
    return jsonify({
        'message': 'Curso criado com sucesso!',
        'course': course.to_dict()
    }), 201

@admin_bp.route('/courses/<int:course_id>', methods=['PUT'])
@token_required
def update_course(current_user, course_id):
    from src.models.course import Course
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': 'Curso não encontrado!'}), 404
    
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': 'Você não tem permissão para editar este curso!'}), 403
    
    data = request.get_json()
    
    if data.get('title'):
        course.title = data['title']
    
    if data.get('subtitle'):
        course.subtitle = data['subtitle']
    
    if data.get('description'):
        course.description = data['description']
    
    if data.get('price'):
        course.price = data['price']
    
    if 'discount_price' in data:
        course.discount_price = data['discount_price']
    
    if data.get('image_url'):
        course.image_url = data['image_url']
    
    if data.get('level'):
        course.level = data['level']
    
    if data.get('duration'):
        course.duration = data['duration']
    
    if data.get('category_id'):
        from src.models.course import Category
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'message': 'Categoria não encontrada!'}), 404
        course.category_id = data['category_id']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Curso atualizado com sucesso!',
        'course': course.to_dict()
    }), 200

@admin_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@token_required
def delete_course(current_user, course_id):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    from src.models.course import Course
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'message': 'Curso não encontrado!'}), 404
    
    db.session.delete(course)
    db.session.commit()
    
    return jsonify({'message': 'Curso excluído com sucesso!'}), 200

@admin_bp.route('/categories', methods=['POST'])
@token_required
def create_category(current_user):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'message': 'Nome da categoria não fornecido!'}), 400
    
    from src.models.course import Category
    
    category = Category(
        name=data['name'],
        description=data.get('description')
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify({
        'message': 'Categoria criada com sucesso!',
        'category': category.to_dict()
    }), 201

@admin_bp.route('/coupons', methods=['GET'])
@token_required
def get_coupons(current_user):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    from src.models.payment import Coupon
    
    coupons = Coupon.query.all()
    return jsonify([coupon.to_dict() for coupon in coupons]), 200

@admin_bp.route('/coupons', methods=['POST'])
@token_required
def create_coupon(current_user):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    data = request.get_json()
    
    if not data or not data.get('code') or not data.get('discount_percent') or not data.get('valid_from') or not data.get('valid_until'):
        return jsonify({'message': 'Dados incompletos!'}), 400
    
    from src.models.payment import Coupon
    from datetime import datetime
    
    try:
        valid_from = datetime.fromisoformat(data['valid_from'])
        valid_until = datetime.fromisoformat(data['valid_until'])
    except ValueError:
        return jsonify({'message': 'Formato de data inválido!'}), 400
    
    coupon = Coupon(
        code=data['code'],
        discount_percent=data['discount_percent'],
        valid_from=valid_from,
        valid_until=valid_until,
        max_uses=data.get('max_uses')
    )
    
    db.session.add(coupon)
    db.session.commit()
    
    return jsonify({
        'message': 'Cupom criado com sucesso!',
        'coupon': coupon.to_dict()
    }), 201

@admin_bp.route('/reports/sales', methods=['GET'])
@token_required
def sales_report(current_user):
    if not current_user.is_admin():
        return jsonify({'message': 'Acesso negado!'}), 403
    
    from src.models.payment import Payment
    from datetime import datetime, timedelta
    
    # Parâmetros de filtro
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    try:
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str)
        else:
            end_date = datetime.utcnow()
    except ValueError:
        return jsonify({'message': 'Formato de data inválido!'}), 400
    
    # Consulta de pagamentos no período
    payments = Payment.query.filter(
        Payment.created_at >= start_date,
        Payment.created_at <= end_date,
        Payment.status == 'completed'
    ).all()
    
    # Calcular total de vendas
    total_sales = sum(payment.amount for payment in payments)
    
    # Agrupar por método de pagamento
    payment_methods = {}
    for payment in payments:
        method = payment.payment_method
        if method not in payment_methods:
            payment_methods[method] = 0
        payment_methods[method] += payment.amount
    
    # Agrupar por curso
    from src.models.course import Course
    
    course_sales = {}
    for payment in payments:
        course = Course.query.get(payment.course_id)
        if course:
            course_id = str(course.id)
            if course_id not in course_sales:
                course_sales[course_id] = {
                    'id': course.id,
                    'title': course.title,
                    'count': 0,
                    'amount': 0
                }
            course_sales[course_id]['count'] += 1
            course_sales[course_id]['amount'] += payment.amount
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'total_sales': total_sales,
        'payment_methods': payment_methods,
        'course_sales': list(course_sales.values())
    }), 200

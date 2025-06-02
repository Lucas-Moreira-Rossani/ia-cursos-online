from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.course import Course, Category, Module, Lesson, Material, Review, Enrollment, Progress
from src.routes.auth import token_required
from datetime import datetime

course_bp = Blueprint('course', __name__)

@course_bp.route('/courses', methods=['GET'])
def get_courses():
    # Parâmetros de filtro
    category_id = request.args.get('category_id', type=int)
    level = request.args.get('level')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    
    # Consulta base
    query = Course.query
    
    # Aplicar filtros
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if level:
        query = query.filter_by(level=level)
    
    if min_price is not None:
        query = query.filter(Course.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Course.price <= max_price)
    
    # Filtro de avaliação é aplicado após buscar os cursos
    courses = query.all()
    
    # Filtrar por avaliação média
    if min_rating is not None:
        courses = [course for course in courses if course.average_rating() >= min_rating]
    
    return jsonify([course.to_dict() for course in courses]), 200

@course_bp.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    course = Course.query.get(course_id)
    
    if not course:
        return jsonify({'message': 'Curso não encontrado!'}), 404
    
    return jsonify(course.to_dict()), 200

@course_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories]), 200

@course_bp.route('/courses/<int:course_id>/modules', methods=['GET'])
def get_course_modules(course_id):
    course = Course.query.get(course_id)
    
    if not course:
        return jsonify({'message': 'Curso não encontrado!'}), 404
    
    modules = Module.query.filter_by(course_id=course_id).order_by(Module.order).all()
    return jsonify([module.to_dict() for module in modules]), 200

@course_bp.route('/modules/<int:module_id>/lessons', methods=['GET'])
def get_module_lessons(module_id):
    module = Module.query.get(module_id)
    
    if not module:
        return jsonify({'message': 'Módulo não encontrado!'}), 404
    
    lessons = Lesson.query.filter_by(module_id=module_id).order_by(Lesson.order).all()
    return jsonify([lesson.to_dict() for lesson in lessons]), 200

@course_bp.route('/lessons/<int:lesson_id>/materials', methods=['GET'])
@token_required
def get_lesson_materials(current_user, lesson_id):
    lesson = Lesson.query.get(lesson_id)
    
    if not lesson:
        return jsonify({'message': 'Aula não encontrada!'}), 404
    
    # Verificar se o usuário está matriculado no curso
    module = Module.query.get(lesson.module_id)
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=module.course_id
    ).first()
    
    if not enrollment:
        return jsonify({'message': 'Você não está matriculado neste curso!'}), 403
    
    materials = Material.query.filter_by(lesson_id=lesson_id).all()
    return jsonify([material.to_dict() for material in materials]), 200

@course_bp.route('/courses/<int:course_id>/reviews', methods=['GET'])
def get_course_reviews(course_id):
    course = Course.query.get(course_id)
    
    if not course:
        return jsonify({'message': 'Curso não encontrado!'}), 404
    
    reviews = Review.query.filter_by(course_id=course_id).all()
    
    result = []
    for review in reviews:
        review_dict = review.to_dict()
        user = User.query.get(review.user_id)
        if user:
            review_dict['user'] = {
                'username': user.username,
                'profile_image': user.profile_image
            }
        result.append(review_dict)
    
    return jsonify(result), 200

@course_bp.route('/courses/<int:course_id>/reviews', methods=['POST'])
@token_required
def add_course_review(current_user, course_id):
    course = Course.query.get(course_id)
    
    if not course:
        return jsonify({'message': 'Curso não encontrado!'}), 404
    
    # Verificar se o usuário está matriculado no curso
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        return jsonify({'message': 'Você não está matriculado neste curso!'}), 403
    
    # Verificar se o usuário já avaliou este curso
    existing_review = Review.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_review:
        return jsonify({'message': 'Você já avaliou este curso!'}), 400
    
    data = request.get_json()
    
    if not data or 'rating' not in data:
        return jsonify({'message': 'Avaliação não fornecida!'}), 400
    
    rating = data['rating']
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'message': 'Avaliação deve ser um número entre 1 e 5!'}), 400
    
    review = Review(
        rating=rating,
        comment=data.get('comment'),
        user_id=current_user.id,
        course_id=course_id
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        'message': 'Avaliação adicionada com sucesso!',
        'review': review.to_dict()
    }), 201

@course_bp.route('/my-courses', methods=['GET'])
@token_required
def get_my_courses(current_user):
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    
    result = []
    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        if course:
            course_dict = course.to_dict()
            course_dict['enrollment'] = enrollment.to_dict()
            
            # Calcular progresso
            total_lessons = 0
            completed_lessons = 0
            
            for module in course.modules:
                module_lessons = Lesson.query.filter_by(module_id=module.id).all()
                total_lessons += len(module_lessons)
                
                for lesson in module_lessons:
                    progress = Progress.query.filter_by(
                        enrollment_id=enrollment.id,
                        lesson_id=lesson.id,
                        completed=True
                    ).first()
                    
                    if progress:
                        completed_lessons += 1
            
            progress_percent = 0
            if total_lessons > 0:
                progress_percent = (completed_lessons / total_lessons) * 100
            
            course_dict['progress'] = {
                'completed_lessons': completed_lessons,
                'total_lessons': total_lessons,
                'percent': progress_percent
            }
            
            result.append(course_dict)
    
    return jsonify(result), 200

@course_bp.route('/lessons/<int:lesson_id>/progress', methods=['POST'])
@token_required
def update_lesson_progress(current_user, lesson_id):
    lesson = Lesson.query.get(lesson_id)
    
    if not lesson:
        return jsonify({'message': 'Aula não encontrada!'}), 404
    
    module = Module.query.get(lesson.module_id)
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=module.course_id
    ).first()
    
    if not enrollment:
        return jsonify({'message': 'Você não está matriculado neste curso!'}), 403
    
    data = request.get_json()
    completed = data.get('completed', False) if data else False
    
    progress = Progress.query.filter_by(
        enrollment_id=enrollment.id,
        lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = Progress(
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            completed=completed
        )
        db.session.add(progress)
    else:
        progress.completed = completed
        progress.last_watched = datetime.utcnow()
    
    db.session.commit()
    
    # Verificar se todas as aulas foram concluídas
    all_lessons_completed = True
    for module in Course.query.get(module.course_id).modules:
        for lesson in module.lessons:
            lesson_progress = Progress.query.filter_by(
                enrollment_id=enrollment.id,
                lesson_id=lesson.id
            ).first()
            
            if not lesson_progress or not lesson_progress.completed:
                all_lessons_completed = False
                break
        
        if not all_lessons_completed:
            break
    
    if all_lessons_completed and not enrollment.completed:
        enrollment.completed = True
        db.session.commit()
    
    return jsonify({
        'message': 'Progresso atualizado com sucesso!',
        'progress': progress.to_dict()
    }), 200

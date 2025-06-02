from flask import Blueprint, request, jsonify, current_app
from src.models.user import db, User
from src.models.course import Course, Module, Lesson, Material
from src.models.payment import Certificate
from src.routes.auth import token_required
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

content_bp = Blueprint('content', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xlsx', 'csv', 'txt', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@content_bp.route('/materials/upload', methods=['POST'])
@token_required
def upload_material(current_user):
    if not current_user.is_instructor():
        return jsonify({'message': 'Permissão negada!'}), 403
    
    if 'file' not in request.files:
        return jsonify({'message': 'Nenhum arquivo enviado!'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'message': 'Nenhum arquivo selecionado!'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'message': 'Tipo de arquivo não permitido!'}), 400
    
    lesson_id = request.form.get('lesson_id')
    if not lesson_id:
        return jsonify({'message': 'ID da aula não fornecido!'}), 400
    
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({'message': 'Aula não encontrada!'}), 404
    
    module = Module.query.get(lesson.module_id)
    course = Course.query.get(module.course_id)
    
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'message': 'Você não tem permissão para adicionar materiais a este curso!'}), 403
    
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    
    # Criar diretório para materiais se não existir
    upload_dir = os.path.join(current_app.static_folder, 'materials')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    
    # URL relativa para acesso ao arquivo
    file_url = f"/static/materials/{unique_filename}"
    
    # Determinar o tipo de material com base na extensão
    file_ext = filename.rsplit('.', 1)[1].lower()
    if file_ext in ['pdf', 'doc', 'docx', 'txt']:
        material_type = 'document'
    elif file_ext in ['ppt', 'pptx']:
        material_type = 'presentation'
    elif file_ext in ['xlsx', 'csv']:
        material_type = 'spreadsheet'
    elif file_ext == 'zip':
        material_type = 'archive'
    else:
        material_type = 'other'
    
    # Criar registro do material no banco de dados
    material = Material(
        title=request.form.get('title', filename),
        type=material_type,
        url=file_url,
        lesson_id=lesson_id
    )
    
    db.session.add(material)
    db.session.commit()
    
    return jsonify({
        'message': 'Material adicionado com sucesso!',
        'material': material.to_dict()
    }), 201

@content_bp.route('/certificates/generate', methods=['POST'])
@token_required
def generate_certificate(current_user):
    data = request.get_json()
    
    if not data or not data.get('course_id'):
        return jsonify({'message': 'ID do curso não fornecido!'}), 400
    
    course_id = data['course_id']
    course = Course.query.get(course_id)
    
    if not course:
        return jsonify({'message': 'Curso não encontrado!'}), 404
    
    # Verificar se o usuário concluiu o curso
    enrollment = db.session.query(Enrollment).filter_by(
        user_id=current_user.id,
        course_id=course_id,
        completed=True
    ).first()
    
    if not enrollment:
        return jsonify({'message': 'Você ainda não concluiu este curso!'}), 400
    
    # Verificar se já existe um certificado
    existing_certificate = Certificate.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_certificate:
        return jsonify({
            'message': 'Certificado já emitido!',
            'certificate': existing_certificate.to_dict()
        }), 200
    
    # Gerar certificado (simulado)
    certificate_filename = f"certificate_{current_user.id}_{course_id}_{uuid.uuid4()}.pdf"
    certificate_url = f"/static/certificates/{certificate_filename}"
    
    # Em uma implementação real, geraria o PDF do certificado aqui
    
    # Criar registro do certificado
    certificate = Certificate(
        user_id=current_user.id,
        course_id=course_id,
        certificate_url=certificate_url
    )
    
    db.session.add(certificate)
    db.session.commit()
    
    return jsonify({
        'message': 'Certificado gerado com sucesso!',
        'certificate': certificate.to_dict()
    }), 201

@content_bp.route('/certificates', methods=['GET'])
@token_required
def get_certificates(current_user):
    certificates = Certificate.query.filter_by(user_id=current_user.id).all()
    
    result = []
    for certificate in certificates:
        cert_dict = certificate.to_dict()
        course = Course.query.get(certificate.course_id)
        if course:
            cert_dict['course'] = {
                'id': course.id,
                'title': course.title
            }
        result.append(cert_dict)
    
    return jsonify(result), 200

@content_bp.route('/quiz/<int:lesson_id>', methods=['GET'])
@token_required
def get_quiz(current_user, lesson_id):
    # Simulação de quiz para uma aula
    # Em uma implementação real, teríamos um modelo de Quiz no banco de dados
    
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({'message': 'Aula não encontrada!'}), 404
    
    # Verificar se o usuário está matriculado no curso
    module = Module.query.get(lesson.module_id)
    course = Course.query.get(module.course_id)
    
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course.id
    ).first()
    
    if not enrollment:
        return jsonify({'message': 'Você não está matriculado neste curso!'}), 403
    
    # Quiz simulado
    quiz = {
        'lesson_id': lesson_id,
        'title': f'Quiz sobre {lesson.title}',
        'questions': [
            {
                'id': 1,
                'text': 'Qual é o principal benefício da IA no mercado de trabalho?',
                'options': [
                    'Substituir completamente os trabalhadores humanos',
                    'Automatizar tarefas repetitivas e aumentar a produtividade',
                    'Eliminar a necessidade de treinamento profissional',
                    'Reduzir a necessidade de comunicação entre equipes'
                ],
                'correct_option': 1
            },
            {
                'id': 2,
                'text': 'O que é prompt engineering?',
                'options': [
                    'Programação de robôs industriais',
                    'Criação de hardware para IA',
                    'Arte de criar instruções eficazes para modelos de IA',
                    'Técnica de marketing digital'
                ],
                'correct_option': 2
            },
            {
                'id': 3,
                'text': 'Qual destas não é uma aplicação comum de IA generativa?',
                'options': [
                    'Geração de textos e artigos',
                    'Criação de imagens e arte digital',
                    'Substituição completa de programadores humanos',
                    'Assistência na criação de conteúdo de marketing'
                ],
                'correct_option': 2
            }
        ]
    }
    
    # Remover as respostas corretas antes de enviar ao cliente
    for question in quiz['questions']:
        question.pop('correct_option', None)
    
    return jsonify(quiz), 200

@content_bp.route('/quiz/<int:lesson_id>/submit', methods=['POST'])
@token_required
def submit_quiz(current_user, lesson_id):
    data = request.get_json()
    
    if not data or not data.get('answers'):
        return jsonify({'message': 'Respostas não fornecidas!'}), 400
    
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({'message': 'Aula não encontrada!'}), 404
    
    # Verificar se o usuário está matriculado no curso
    module = Module.query.get(lesson.module_id)
    course = Course.query.get(module.course_id)
    
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course.id
    ).first()
    
    if not enrollment:
        return jsonify({'message': 'Você não está matriculado neste curso!'}), 403
    
    # Respostas corretas simuladas
    correct_answers = {
        1: 1,  # ID da questão: índice da opção correta
        2: 2,
        3: 2
    }
    
    # Verificar respostas
    user_answers = data['answers']
    correct_count = 0
    total_questions = len(correct_answers)
    
    for question_id, answer_index in user_answers.items():
        if int(question_id) in correct_answers and correct_answers[int(question_id)] == answer_index:
            correct_count += 1
    
    score = (correct_count / total_questions) * 100
    passed = score >= 70  # Considerando 70% como nota de aprovação
    
    # Em uma implementação real, salvaríamos o resultado no banco de dados
    
    return jsonify({
        'message': 'Quiz enviado com sucesso!',
        'score': score,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'passed': passed
    }), 200

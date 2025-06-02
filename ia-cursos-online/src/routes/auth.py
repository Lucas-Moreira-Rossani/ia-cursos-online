from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import db, User
import jwt
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token de autenticação ausente!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token inválido ou expirado!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('username'):
        return jsonify({'message': 'Dados incompletos!'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email já cadastrado!'}), 409
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Nome de usuário já existe!'}), 409
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        role='student'
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Usuário registrado com sucesso!'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Dados incompletos!'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Credenciais inválidas!'}), 401
    
    # Atualiza último login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Gera token JWT
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    # Implementação futura para login via Google OAuth
    return jsonify({'message': 'Funcionalidade em desenvolvimento'}), 501

@auth_bp.route('/reset-password-request', methods=['POST'])
def reset_password_request():
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'message': 'Email não fornecido!'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        # Por segurança, não informamos se o email existe ou não
        return jsonify({'message': 'Se o email estiver cadastrado, você receberá instruções para redefinir sua senha.'}), 200
    
    # Aqui implementaríamos o envio de email com token para redefinição
    # Por enquanto, apenas simulamos o processo
    
    return jsonify({'message': 'Se o email estiver cadastrado, você receberá instruções para redefinir sua senha.'}), 200

@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    # Implementação futura para redefinição de senha
    return jsonify({'message': 'Funcionalidade em desenvolvimento'}), 501

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify(current_user.to_dict()), 200

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    
    if data.get('first_name'):
        current_user.first_name = data['first_name']
    
    if data.get('last_name'):
        current_user.last_name = data['last_name']
    
    if data.get('bio'):
        current_user.bio = data['bio']
    
    if data.get('profile_image'):
        current_user.profile_image = data['profile_image']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Perfil atualizado com sucesso!',
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'message': 'Dados incompletos!'}), 400
    
    if not current_user.check_password(data['current_password']):
        return jsonify({'message': 'Senha atual incorreta!'}), 401
    
    current_user.set_password(data['new_password'])
    db.session.commit()
    
    return jsonify({'message': 'Senha alterada com sucesso!'}), 200

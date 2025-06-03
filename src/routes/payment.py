from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.course import Course, Category, Review, Enrollment
from src.models.payment import Payment, Cart, CartItem, Coupon
from src.routes.auth import token_required
from datetime import datetime
import stripe
import os

payment_bp = Blueprint('payment', __name__)

# Configuração do Stripe (simulada)
stripe.api_key = os.getenv('STRIPE_API_KEY', 'sk_test_example')

@payment_bp.route('/cart', methods=['GET'])
@token_required
def get_cart(current_user):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    return jsonify(cart.to_dict()), 200

@payment_bp.route('/cart/add', methods=['POST'])
@token_required
def add_to_cart(current_user):
    data = request.get_json()
    
    if not data or not data.get('course_id'):
        return jsonify({'message': 'ID do curso não fornecido!'}), 400
    
    course = Course.query.get(data['course_id'])
    if not course:
        return jsonify({'message': 'Curso não encontrado!'}), 404
    
    # Verifica se o usuário já está matriculado no curso
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id, 
        course_id=course.id
    ).first()
    
    if enrollment:
        return jsonify({'message': 'Você já está matriculado neste curso!'}), 400
    
    # Busca ou cria o carrinho do usuário
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    # Verifica se o curso já está no carrinho
    existing_item = CartItem.query.filter_by(
        cart_id=cart.id,
        course_id=course.id
    ).first()
    
    if existing_item:
        return jsonify({'message': 'Este curso já está no seu carrinho!'}), 400
    
    # Adiciona o curso ao carrinho
    price = course.discount_price if course.discount_price else course.price
    cart_item = CartItem(
        cart_id=cart.id,
        course_id=course.id,
        price=price
    )
    
    db.session.add(cart_item)
    db.session.commit()
    
    return jsonify({
        'message': 'Curso adicionado ao carrinho!',
        'cart': cart.to_dict()
    }), 201

@payment_bp.route('/cart/remove/<int:item_id>', methods=['DELETE'])
@token_required
def remove_from_cart(current_user, item_id):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        return jsonify({'message': 'Carrinho não encontrado!'}), 404
    
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    
    if not cart_item:
        return jsonify({'message': 'Item não encontrado no carrinho!'}), 404
    
    db.session.delete(cart_item)
    db.session.commit()
    
    return jsonify({
        'message': 'Item removido do carrinho!',
        'cart': cart.to_dict()
    }), 200

@payment_bp.route('/apply-coupon', methods=['POST'])
@token_required
def apply_coupon(current_user):
    data = request.get_json()
    
    if not data or not data.get('code'):
        return jsonify({'message': 'Código do cupom não fornecido!'}), 400
    
    coupon = Coupon.query.filter_by(code=data['code']).first()
    
    if not coupon:
        return jsonify({'message': 'Cupom não encontrado!'}), 404
    
    if not coupon.is_valid():
        return jsonify({'message': 'Cupom expirado ou limite de uso atingido!'}), 400
    
    # Aqui implementaríamos a lógica para aplicar o cupom ao carrinho
    # Por enquanto, apenas retornamos os detalhes do cupom
    
    return jsonify({
        'message': 'Cupom aplicado com sucesso!',
        'coupon': coupon.to_dict()
    }), 200

@payment_bp.route('/checkout/stripe', methods=['POST'])
@token_required
def stripe_checkout(current_user):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart or not cart.items:
        return jsonify({'message': 'Carrinho vazio!'}), 400
    
    try:
        # Criação do checkout do Stripe (simulado)
        checkout_session = {
            'id': 'cs_test_' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'payment_status': 'unpaid',
            'url': 'https://checkout.stripe.com/example',
            'amount_total': int(cart.total() * 100)  # Stripe usa centavos
        }
        
        # Em uma implementação real, usaríamos:
        # checkout_session = stripe.checkout.Session.create(
        #     payment_method_types=['card'],
        #     line_items=[...],
        #     mode='payment',
        #     success_url='...',
        #     cancel_url='...'
        # )
        
        return jsonify({
            'checkout_url': checkout_session['url'],
            'session_id': checkout_session['id']
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erro ao processar pagamento: {str(e)}'}), 500

@payment_bp.route('/checkout/pagseguro', methods=['POST'])
@token_required
def pagseguro_checkout(current_user):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart or not cart.items:
        return jsonify({'message': 'Carrinho vazio!'}), 400
    
    payment_method = request.json.get('payment_method')
    if not payment_method or payment_method not in ['pix', 'boleto', 'credit_card']:
        return jsonify({'message': 'Método de pagamento inválido!'}), 400
    
    try:
        # Simulação de integração com PagSeguro
        payment_info = {
            'id': 'PAG' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'status': 'pending',
            'payment_method': payment_method,
            'amount': cart.total(),
            'currency': 'BRL'
        }
        
        # Cria registro de pagamento no banco
        for item in cart.items:
            payment = Payment(
                amount=item.price,
                status='pending',
                payment_method=payment_method,
                payment_id=payment_info['id'],
                user_id=current_user.id,
                course_id=item.course_id
            )
            db.session.add(payment)
        
        db.session.commit()
        
        # Retorna informações de pagamento simuladas
        if payment_method == 'pix':
            return jsonify({
                'payment_id': payment_info['id'],
                'qr_code': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
                'expiration': '30 minutos'
            }), 200
        elif payment_method == 'boleto':
            return jsonify({
                'payment_id': payment_info['id'],
                'boleto_url': 'https://exemplo.com/boleto',
                'barcode': '23790123456789012345678901234567890123456789'
            }), 200
        else:  # credit_card
            return jsonify({
                'payment_id': payment_info['id'],
                'redirect_url': 'https://exemplo.com/pagamento'
            }), 200
            
    except Exception as e:
        return jsonify({'message': f'Erro ao processar pagamento: {str(e)}'}), 500

@payment_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    # Implementação futura para webhook do Stripe
    return jsonify({'received': True}), 200

@payment_bp.route('/webhook/pagseguro', methods=['POST'])
def pagseguro_webhook():
    # Implementação futura para webhook do PagSeguro
    return jsonify({'received': True}), 200

@payment_bp.route('/payment-history', methods=['GET'])
@token_required
def payment_history(current_user):
    payments = Payment.query.filter_by(user_id=current_user.id).all()
    return jsonify([payment.to_dict() for payment in payments]), 200

@payment_bp.route('/payment/<payment_id>', methods=['GET'])
@token_required
def payment_details(current_user, payment_id):
    payment = Payment.query.filter_by(
        payment_id=payment_id, 
        user_id=current_user.id
    ).first()
    
    if not payment:
        return jsonify({'message': 'Pagamento não encontrado!'}), 404
    
    return jsonify(payment.to_dict()), 200

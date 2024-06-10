from flask import render_template, url_for, flash, redirect, request, Blueprint, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from app.models import User, Expense, Category
from app import db
from datetime import datetime

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    return redirect(url_for('routes.login'))

@routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        user.add_default_categories()  # Ajouter des catégories par défaut
        return jsonify({'message': 'User registered successfully!'})
    return render_template('register.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if user and user.check_password(data['password']):
            token = create_access_token(identity=user.id)
            response = jsonify({'login': True})
            set_access_cookies(response, token)
            return response
        return jsonify({'message': 'Login failed!'}), 401
    return render_template('login.html')

@routes.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    category_filter = request.args.get('category', None)
    if category_filter:
        expenses = Expense.query.filter_by(user_id=user_id, category=category_filter).all()
    else:
        expenses = Expense.query.filter_by(user_id=user_id).all()
    total_expenses = sum(expense.amount for expense in expenses)
    expense_count = len(expenses)
    categories = Category.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', expenses=expenses, total_expenses=total_expenses, expense_count=expense_count, categories=categories)

@routes.route('/add_expense', methods=['GET', 'POST'])
@jwt_required()
def add_expense():
    user_id = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        expense = Expense(amount=data['amount'], category=data['category'], description=data.get('description'), date=datetime.strptime(data['date'], '%Y-%m-%d'), user_id=user_id)
        db.session.add(expense)
        db.session.commit()
        return jsonify({'message': 'Expense added successfully!'})
    categories = Category.query.filter_by(user_id=user_id).all()
    return render_template('add_expense.html', categories=categories)

@routes.route('/categories', methods=['GET', 'POST'])
@jwt_required()
def manage_categories():
    user_id = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        category = Category(name=data['name'], color=data.get('color', '#ffffff'), user_id=user_id)
        db.session.add(category)
        db.session.commit()
        return jsonify({'message': 'Category added successfully!'}), 201
    
    categories = Category.query.filter_by(user_id=user_id).all()
    return render_template('categories.html', categories=categories)

@routes.route('/categories/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def update_delete_category(id):
    user_id = get_jwt_identity()
    category = Category.query.get_or_404(id)
    if category.user_id != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        category.name = data['name']
        category.color = data.get('color', category.color)
        db.session.commit()
        return jsonify({'message': 'Category updated successfully!'})
    
    if request.method == 'DELETE':
        db.session.delete(category)
        db.session.commit()
        return jsonify({'message': 'Category deleted successfully!'})

@routes.route('/logout')
def logout():
    response = jsonify({'logout': True})
    unset_jwt_cookies(response)
    return redirect(url_for('routes.login'))

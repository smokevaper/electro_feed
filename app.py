from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
from datetime import datetime

{% if current_user.is_authenticated %}
<h2>Ваши заказы:</h2>
<!-- Добавьте код для отображения заказов -->
{% for order in orders %}
    <div>
        <p>Заказ ID: {{ order.id }}</p>
        <p>Сумма: {{ order.total_price }}₸</p>
    </div>
{% endfor %}
{% endif %}

order_text = f"Ник: {current_user.username}, Заказ: {order.id}, Сумма: {order.total_price}₸"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модели базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price_tenge = db.Column(db.Float, nullable=False)
    price_rub = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    specs = db.Column(db.Text)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship('Product', backref='cart_items')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(50), default='новый')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Декоратор для проверки админских прав
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Доступ запрещен. Нужны права администратора.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Функция отправки в Telegram
def send_telegram_message(message):
    bot_token = "7474534895:AAEdMCuLAQx8sel53we8lGyh9N_GrhiEMDY"
    chat_id = "@e_f_zakazi"  # Публичный канал

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Уведомление отправлено в Telegram")
        else:
            print(f"❌ Ошибка отправки в Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка при отправке в Telegram: {e}")

# Функция отправки в WhatsApp (через API)
def send_whatsapp_message(message):
    # Здесь нужен API ключ от сервиса WhatsApp API
    # Это примерный код, замените на реальный API
    pass

# Маршруты
@app.route('/')
def index():
    products = Product.query.all()
    categories = Category.query.all()
    cart_count = 0
    if current_user.is_authenticated:
        cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    return render_template('index.html', products=products, categories=categories, cart_count=cart_count)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    existing_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if existing_item:
        existing_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    flash('Товар добавлен в корзину!')
    return redirect(url_for('index'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price_tenge * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Корзина пуста!')
        return redirect(url_for('cart'))

    if request.method == 'POST':
        country = request.form['country']
        city = request.form['city']
        address = request.form['address']
        phone = request.form['phone']

        total_price = sum(item.product.price_tenge * item.quantity for item in cart_items)

        # Создаем заказ
        order = Order(
            user_id=current_user.id,
            total_price=total_price,
            country=country,
            city=city,
            address=address,
            phone=phone
        )
        db.session.add(order)
        db.session.flush()  # Чтобы получить ID заказа

        # Добавляем товары к заказу
        order_text = f"🛒 <b>НОВЫЙ ЗАКАЗ #{order.id}</b>\n\n"
        order_text += f"👤 <b>Покупатель:</b> {current_user.username}\n"
        order_text += f"📧 <b>Email:</b> {current_user.email}\n"
        order_text += f"📱 <b>Телефон:</b> {phone}\n\n"
        order_text += f"📍 <b>Адрес доставки:</b>\n"
        order_text += f"🌍 Страна: {country}\n"
        order_text += f"🏙 Город: {city}\n"
        order_text += f"📮 Адрес СДЭК: {address}\n\n"
        order_text += "📦 <b>Товары:</b>\n"

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price_tenge
            )
            db.session.add(order_item)

            order_text += f"• {item.product.name} x{item.quantity} = {item.product.price_tenge * item.quantity}₸\n"

        order_text += f"\n💰 <b>Итого:</b> {total_price}₸\n"
        order_text += f"🕐 <b>Время заказа:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"

        # Очищаем корзину
        for item in cart_items:
            db.session.delete(item)

        db.session.commit()

        # Отправляем уведомления
        send_telegram_message(order_text)
        send_whatsapp_message(order_text.replace('<b>', '').replace('</b>', ''))

        flash('Заказ успешно оформлен! Мы свяжемся с вами в ближайшее время.')
        return redirect(url_for('order_success', order_id=order.id))

    total = sum(item.product.price_tenge * item.quantity for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/order_success/<int:order_id>')
@login_required
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return redirect(url_for('index'))
    return render_template('order_success.html', order=order)

@app.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

# Админские маршруты
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_panel.html', products=products, orders=orders)

@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price_tenge = float(request.form['price_tenge'])
        price_rub = float(request.form['price_rub'])
        category = request.form['category']
        description = request.form['description']
        specs = request.form['specs']
        
        product = Product(
            name=name,
            price_tenge=price_tenge,
            price_rub=price_rub,
            category=category,
            description=description,
            specs=specs
        )
        db.session.add(product)
        db.session.commit()
        
        flash('Товар успешно добавлен!')
        return redirect(url_for('admin_panel'))
    
    categories = Category.query.all()
    return render_template('add_product.html', categories=categories)

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.price_tenge = float(request.form['price_tenge'])
        product.price_rub = float(request.form['price_rub'])
        product.category = request.form['category']
        product.description = request.form['description']
        product.specs = request.form['specs']
        
        db.session.commit()
        flash('Товар успешно обновлен!')
        return redirect(url_for('admin_panel'))
    
    categories = Category.query.all()
    return render_template('edit_product.html', product=product, categories=categories)

@app.route('/admin/delete_product/<int:product_id>')
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Товар удален!')
    return redirect(url_for('admin_panel'))

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form['status']
    order.status = new_status
    db.session.commit()
    flash(f'Статус заказа #{order_id} изменен на "{new_status}"')
    return redirect(url_for('admin_orders'))

@app.route('/admin/categories')
@login_required
@admin_required
def manage_categories():
    categories = Category.query.all()
    return render_template('manage_categories.html', categories=categories)

@app.route('/admin/add_category', methods=['POST'])
@login_required
@admin_required
def add_category():
    name = request.form['name']
    display_name = request.form['display_name']
    
    if Category.query.filter_by(name=name).first():
        flash('Категория с таким именем уже существует!')
        return redirect(url_for('manage_categories'))
    
    category = Category(name=name, display_name=display_name)
    db.session.add(category)
    db.session.commit()
    flash('Категория успешно добавлена!')
    return redirect(url_for('manage_categories'))

@app.route('/admin/delete_category/<int:category_id>')
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Категория удалена!')
    return redirect(url_for('manage_categories'))

def create_admin_account():
    """Создает аккаунт администратора"""
    admin = User.query.filter_by(username='admin1').first()
    if not admin:
        admin = User(
            username='admin1',
            email='admin@electrofeed.com',
            password_hash=generate_password_hash('satzazamaga228gladiator19'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Администратор создан: admin1")

def init_categories():
    if Category.query.count() == 0:
        categories_data = [
            {'name': 'pod-systems', 'display_name': 'Под системы'},
            {'name': 'coils', 'display_name': 'Испарители/Картриджи'},
            {'name': 'batteries', 'display_name': 'Аккумуляторы'},
            {'name': 'tanks', 'display_name': 'Баки/RTA'},
            {'name': 'electronics', 'display_name': 'Электро товары'},
            {'name': 'hookah', 'display_name': 'Кальяны'},
            {'name': 'plates', 'display_name': 'Плитки'},
            {'name': 'accessories', 'display_name': 'Комплектующие'},
        ]
        
        for category_data in categories_data:
            category = Category(**category_data)
            db.session.add(category)
        
        db.session.commit()

def init_products():
    if Product.query.count() == 0:
        products_data = [
            # Картриджи
            {'name': 'Картриджи XROS 0.6Ω-1.2Ω', 'price_tenge': 2500, 'price_rub': 470, 'category': 'coils', 'description': 'Сопротивление: 0.6Ω, 0.8Ω, 1.0Ω, 1.2Ω', 'specs': 'Совместимость: Vaporesso XROS серия, Объем: 2ml, Материал: PCTG'},
            {'name': 'Картриджи Xlim 0.4Ω-1.0Ω', 'price_tenge': 2500, 'price_rub': 470, 'category': 'coils', 'description': 'Сопротивление: 0.4Ω, 0.6Ω, 0.8Ω, 1.0Ω', 'specs': 'Совместимость: OXva Xlim серия, Объем: 2ml, Материал: PCTG'},

            # Испарители
            {'name': 'Испаритель Drag S/X', 'price_tenge': 2000, 'price_rub': 380, 'category': 'coils', 'description': 'Испаритель для Drag S/X', 'specs': 'Совместимость: Voopoo Drag S/X, Высокое качество пара'},
            {'name': 'Испаритель Pasito 2', 'price_tenge': 2000, 'price_rub': 380, 'category': 'coils', 'description': 'Испаритель для Pasito 2', 'specs': 'Совместимость: Smok Pasito 2, Отличная передача вкуса'},
            {'name': 'Испаритель Manto AIO', 'price_tenge': 2000, 'price_rub': 380, 'category': 'coils', 'description': 'Испаритель для Manto AIO', 'specs': 'Совместимость: Rincoe Manto AIO, Долгий срок службы'},
            {'name': 'Испаритель Aegis (все серии)', 'price_tenge': 2000, 'price_rub': 380, 'category': 'coils', 'description': 'Испаритель для Aegis', 'specs': 'Совместимость: GeekVape Aegis все серии, Универсальный'},

            # Вейпы
            {'name': 'Voopoo Drag 2', 'price_tenge': 25000, 'price_rub': 5000, 'category': 'pod-systems', 'description': 'Мощность: до 177W', 'specs': 'Размер: 90×54×25mm, АКБ: 2х18650 (не входят), Зарядка: USB Type-C, Чип: GENE.FIT'},
            {'name': 'GeekVape Aegis Legend 2', 'price_tenge': 25000, 'price_rub': 5000, 'category': 'pod-systems', 'description': 'Мощность: до 200W', 'specs': 'Размер: 90×54×27mm, АКБ: 2х18650, Защита: IP68, Чип: AS-200'},
            {'name': 'Voopoo Drag X Pro', 'price_tenge': 28000, 'price_rub': 5600, 'category': 'pod-systems', 'description': 'Мощность: до 100W', 'specs': 'АКБ: 1х18650/21700, Зарядка: USB Type-C, Чип: GENE.TT 2.0'},
            {'name': 'Voopoo Drag S Pro', 'price_tenge': 22000, 'price_rub': 4400, 'category': 'pod-systems', 'description': 'Мощность: до 80W', 'specs': 'Встроенная батарея: 3200mAh, Зарядка: USB Type-C, Компактный дизайн'},
            {'name': 'Eleaf Jelly Box 228W', 'price_tenge': 27900, 'price_rub': 5290, 'category': 'pod-systems', 'description': 'Мощность: до 228W', 'specs': 'АКБ: 2х18650, Материал: сплав цинка, Защита от перегрева'},
            {'name': 'Eleaf iStick Pico Mega 80W', 'price_tenge': 22500, 'price_rub': 4250, 'category': 'pod-systems', 'description': 'Мощность: до 80W', 'specs': 'АКБ: 1х18650/26650, Компактный размер, TC режим'},
            {'name': 'Voopoo Argus MT', 'price_tenge': 19900, 'price_rub': 3990, 'category': 'pod-systems', 'description': 'Мощность: до 40W', 'specs': 'Встроенная батарея: 1500mAh, Под система, MTL/DTL'},
            {'name': 'Voopoo Argus GT II', 'price_tenge': 21490, 'price_rub': 4290, 'category': 'pod-systems', 'description': 'Мощность: до 200W', 'specs': 'АКБ: 2х18650, Водонепроницаемый, Ударопрочный'},
            {'name': 'Eleaf V-Grip 220W', 'price_tenge': 16900, 'price_rub': 3390, 'category': 'pod-systems', 'description': 'Мощность: до 220W', 'specs': 'АКБ: 2х18650, Эргономичный дизайн, TC режим'},
            {'name': 'Voopoo Musket', 'price_tenge': 17890, 'price_rub': 3590, 'category': 'pod-systems', 'description': 'Мощность: до 120W', 'specs': 'АКБ: 1х18650/20700/21700, Механический стиль, Прочный корпус'},

            # Аккумуляторы
            {'name': 'YLAID 18650 40A / 2200 mAh', 'price_tenge': 1190, 'price_rub': 230, 'category': 'batteries', 'description': 'Емкость: 2200 mAh', 'specs': 'Ток разряда: 40A, Размер: 18650, Тип: Li-ion'},
            {'name': 'YLAID 18650 60A / 3100 mAh', 'price_tenge': 1690, 'price_rub': 330, 'category': 'batteries', 'description': 'Емкость: 3100 mAh', 'specs': 'Ток разряда: 60A, Размер: 18650, Высокая емкость'},
            {'name': 'Sony VTC5A (оригинал)', 'price_tenge': 2190, 'price_rub': 420, 'category': 'batteries', 'description': 'Емкость: 2600 mAh (оригинал)', 'specs': 'Ток разряда: 35A, Размер: 18650, Производитель: Sony'},
            {'name': 'Sony VTC6 (оригинал)', 'price_tenge': 2490, 'price_rub': 480, 'category': 'batteries', 'description': 'Емкость: 3000 mAh (оригинал)', 'specs': 'Ток разряда: 30A, Размер: 18650, Производитель: Sony'},
            {'name': 'Зарядка на 4x 18650', 'price_tenge': 2900, 'price_rub': 560, 'category': 'batteries', 'description': 'Зарядное устройство', 'specs': 'На 4 аккумулятора 18650, LCD дисплей, Защита от перезаряда'},

            # Насадки (RTA)
            {'name': 'Zeus Z RTA', 'price_tenge': 9500, 'price_rub': 1900, 'category': 'tanks', 'description': 'Объем: 5.5ml', 'specs': 'Диаметр: 26mm, Материал: нержавеющая сталь, Обдув: Side airflow'},
            {'name': 'Zeus 2 RTA', 'price_tenge': 11000, 'price_rub': 2200, 'category': 'tanks', 'description': 'Объем: 5.5ml', 'specs': 'Диаметр: 26mm, Улучшенная версия, Двойной обдув'},
            {'name': 'Zeus X Mesh RTA', 'price_tenge': 10000, 'price_rub': 2000, 'category': 'tanks', 'description': 'Объем: 4.5ml', 'specs': 'Диаметр: 25mm, Mesh совместимость, Отличная передача вкуса'},

            # Комплектующие
            {'name': 'Вата Cotton Bacon', 'price_tenge': 1500, 'price_rub': 300, 'category': 'accessories', 'description': 'Органическая вата', 'specs': 'Высокое качество, Органический хлопок, Отличное впитывание'},
            {'name': 'Койлы (набор 48 шт)', 'price_tenge': 4000, 'price_rub': 800, 'category': 'accessories', 'description': 'Набор готовых койлов', 'specs': '48 штук в наборе, Различные сопротивления, Кантал A1'},

            # Кальяны
            {'name': 'Кальян 50 см / 2 трубки', 'price_tenge': 21900, 'price_rub': 4190, 'category': 'hookah', 'description': 'Полный комплект', 'specs': 'Высота: 50 см, 2 трубки, табак, уголь, мундштуки в комплекте'},
            {'name': 'Кальян 29 см / 2 трубки', 'price_tenge': 12990, 'price_rub': 2490, 'category': 'hookah', 'description': 'Компактный комплект', 'specs': 'Высота: 29 см, 2 трубки, табак, уголь, мундштуки в комплекте'},
            {'name': 'Авто-кальян (портативный)', 'price_tenge': 14500, 'price_rub': 2790, 'category': 'hookah', 'description': 'Портативный кальян', 'specs': 'Для автомобиля, табак, уголь, фольга в комплекте'},
            {'name': 'Плоский кальян-бокс', 'price_tenge': 15900, 'price_rub': 3090, 'category': 'hookah', 'description': 'Кальян в боксе', 'specs': 'Плоский дизайн, табак, щипцы, уголь, пульт подсветки, мундштуки'},
            {'name': 'Электроплитка для углей', 'price_tenge': 7500, 'price_rub': 1450, 'category': 'plates', 'description': 'Мощность: 1000W', 'specs': 'Диаметр: 155 мм, Регулировка температуры, Время нагрева: 3-5 минут'},
        ]

        for product_data in products_data:
            product = Product(**product_data)
            db.session.add(product)

        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_account()
        init_categories()
        init_products()
    app.run(host='0.0.0.0', port=5000, debug=True)

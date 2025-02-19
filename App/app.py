from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

# =========================================
# Konfigurasi Aplikasi
# =========================================
app = Flask(__name__)

# Konfigurasi MySQL Database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'motor'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.secret_key = 'your_secret_key_here'

# Inisialisasi MySQL
mysql = MySQL(app)

# =========================================
# Middleware & Decorators
# =========================================
def login_required(f):
    """Decorator untuk memastikan user sudah login sebelum mengakses halaman tertentu"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# =========================================
# Halaman Utama & Pencarian
# =========================================
@app.route('/')
@login_required
def home():
    """Menampilkan halaman utama dengan daftar produk terbaru dan kategori"""
    cur = mysql.connection.cursor()
    
    # Ambil kategori
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    
    # Ambil produk terbaru
    cur.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        ORDER BY p.created_at DESC 
        LIMIT 10
    """)
    products = cur.fetchall()
    
    cur.close()
    return render_template('home.html', categories=categories, products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login user"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login berhasil!', 'success')
            return redirect(url_for('home'))
            
        flash('Email atau password salah!', 'error')
    return render_template('login.html', hide_navbar=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Halaman registrasi user baru"""
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            if password != confirm_password:
                flash('Password tidak cocok!', 'error')
                return redirect(url_for('register'))
            
            # Generate password hash dengan method spesifik
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            
            cur = mysql.connection.cursor()
            
            # Cek apakah email sudah terdaftar
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cur.fetchone()
            
            if user:
                flash('Email sudah terdaftar!', 'error')
                return redirect(url_for('register'))
            
            # Insert user baru
            cur.execute("""
                INSERT INTO users (username, email, password) 
                VALUES (%s, %s, %s)
            """, (username, email, hashed_password))
            
            mysql.connection.commit()
            cur.close()
            
            flash('Registrasi berhasil! Silakan login', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Error during registration: {str(e)}")
            flash('Terjadi kesalahan saat registrasi', 'error')
            return redirect(url_for('register'))
            
    return render_template('register.html', hide_navbar=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/product/<int:id>')
@login_required
def product_detail(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE id = %s", (id,))
    product = cur.fetchone()
    cur.close()
    
    if not product:
        return redirect(url_for('home'))
        
    return render_template('product_detail.html', product=product)

@app.route('/cart')
@login_required
def cart():
    """Menampilkan keranjang belanja user"""
    cur = mysql.connection.cursor()
    
    # Ambil item keranjang beserta detail produknya
    cur.execute("""
        SELECT c.*, p.name, p.price, p.image_url, p.part_number, 
               p.discount_percentage,
               (p.price * (100 - p.discount_percentage) / 100) as discounted_price
        FROM carts c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (session['user_id'],))
    
    cart_items = cur.fetchall()
    
    # Hitung subtotal (harga sebelum diskon)
    subtotal = sum(item['quantity'] * item['price'] for item in cart_items)
    
    # Hitung total diskon
    total_discount = sum(
        item['quantity'] * (
            item['price'] - item['discounted_price']
        ) if item['discount_percentage'] > 0 else 0
        for item in cart_items
    )
    
    # Hitung total akhir (setelah diskon)
    final_total = subtotal - total_discount
    
    cur.close()
    
    return render_template('cart.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         total_discount=total_discount,
                         final_total=final_total)

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    
    # Ambil item keranjang untuk memastikan ada produk
    cur.execute("""
        SELECT c.*, p.name, p.price, p.image_url, p.part_number, 
               p.discount_percentage,
               (p.price * (100 - p.discount_percentage) / 100) as discounted_price
        FROM carts c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (session['user_id'],))
    
    cart_items = cur.fetchall()
    
    if not cart_items:
        flash('Keranjang belanja kosong', 'error')
        return redirect(url_for('cart'))
    
    # Hitung total belanja
    subtotal = sum(item['quantity'] * item['price'] for item in cart_items)
    total_discount = sum(
        item['quantity'] * (
            item['price'] - item['discounted_price']
        ) if item['discount_percentage'] > 0 else 0
        for item in cart_items
    )
    final_total = subtotal - total_discount
    
    # Ambil alamat user jika ada
    cur.execute("SELECT * FROM addresses WHERE user_id = %s AND is_default = 1", 
                (session['user_id'],))
    address = cur.fetchone()
    
    cur.close()
    
    return render_template('checkout.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         total_discount=total_discount,
                         final_total=final_total,
                         address=address)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        # Logika untuk mengirim email reset password
        flash('Link reset password telah dikirim ke email Anda', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html', hide_navbar=True)

@app.route('/search')
def search():
    """Mencari produk berdasarkan kata kunci"""
    query = request.args.get('q', '')
    
    cur = mysql.connection.cursor()
    
    # Cari produk berdasarkan nama atau deskripsi
    cur.execute("""
        SELECT * FROM products 
        WHERE name LIKE %s 
        OR description LIKE %s
        OR part_number LIKE %s
        OR compatible_vehicles LIKE %s
    """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
    
    products = cur.fetchall()
    
    # Ambil kategori untuk sidebar
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    
    cur.close()
    
    return render_template('search.html', 
                         products=products, 
                         categories=categories,
                         query=query)

@app.route('/category/<int:id>')
def category(id):
    cur = mysql.connection.cursor()
    
    # Ambil detail kategori
    cur.execute("SELECT * FROM categories WHERE id = %s", (id,))
    category = cur.fetchone()
    
    if not category:
        return redirect(url_for('home'))
    
    # Jika kategori adalah "All", ambil semua produk
    if category['name'] == 'All':
        cur.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            ORDER BY p.created_at DESC
        """)
    else:
        # Ambil produk dalam kategori spesifik
        cur.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE category_id = %s
        """, (id,))
    
    products = cur.fetchall()
    
    # Ambil semua kategori untuk sidebar
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    
    cur.close()
    
    return render_template('category.html', 
                         category=category,
                         products=products,
                         categories=categories)

@app.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    """Menambahkan produk ke keranjang belanja"""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    cur = mysql.connection.cursor()
    try:
        # Cek apakah produk ada
        cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        
        if not product:
            cur.close()
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Cek apakah produk sudah ada di keranjang
        cur.execute("SELECT * FROM carts WHERE user_id = %s AND product_id = %s",
                    (session['user_id'], product_id))
        cart_item = cur.fetchone()
        
        if cart_item:
            # Update quantity jika sudah ada
            cur.execute("""
                UPDATE carts 
                SET quantity = quantity + %s 
                WHERE user_id = %s AND product_id = %s
            """, (quantity, session['user_id'], product_id))
        else:
            # Tambah item baru jika belum ada
            cur.execute("""
                INSERT INTO carts (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (session['user_id'], product_id, quantity))
        
        mysql.connection.commit()
        return jsonify({'success': True, 'message': 'Product added to cart'})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': 'Gagal menambahkan ke keranjang'})
        
    finally:
        cur.close()

@app.route('/update-cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    cart_id = data.get('cart_id')
    quantity = data.get('quantity')
    
    cur = mysql.connection.cursor()
    
    try:
        # Update quantity
        cur.execute("""
            UPDATE carts 
            SET quantity = %s 
            WHERE id = %s AND user_id = %s
        """, (quantity, cart_id, session['user_id']))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
    except Exception as e:
        cur.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete-cart-item', methods=['POST'])
def delete_cart_item():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    cart_id = data.get('cart_id')
    
    cur = mysql.connection.cursor()
    
    try:
        # Hapus item dari keranjang
        cur.execute("""
            DELETE FROM carts 
            WHERE id = %s AND user_id = %s
        """, (cart_id, session['user_id']))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
    except Exception as e:
        cur.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/process-payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    payment_method = data.get('payment_method')
    
    cur = mysql.connection.cursor()
    
    try:
        print(f"Processing payment for user_id: {session['user_id']}")  # Debug log
        
        # Ambil items dari keranjang
        cur.execute("""
            SELECT c.*, p.price, p.discount_percentage,
                   (p.price * (100 - p.discount_percentage) / 100) as discounted_price
            FROM carts c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
        """, (session['user_id'],))
        
        cart_items = cur.fetchall()
        print(f"Found {len(cart_items)} items in cart")  # Debug log
        
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'})
        
        # Hitung total
        total_amount = sum(
            item['quantity'] * (
                item['discounted_price'] if item['discount_percentage'] > 0 
                else item['price']
            )
            for item in cart_items
        )
        
        shipping_cost = 0
        final_amount = total_amount + shipping_cost
        
        print(f"Creating order with total_amount: {total_amount}")  # Debug log
        
        # Buat order baru
        cur.execute("""
            INSERT INTO orders (
                user_id, 
                total_amount, 
                shipping_cost,
                payment_method, 
                payment_status,
                final_amount
            )
            VALUES (%s, %s, %s, %s, 'pending', %s)
        """, (session['user_id'], total_amount, shipping_cost, payment_method, final_amount))
        
        order_id = cur.lastrowid
        print(f"Created order with ID: {order_id}")  # Debug log
        
        # Pindahkan items dari cart ke order_items
        for item in cart_items:
            item_price = item['discounted_price'] if item['discount_percentage'] > 0 else item['price']
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['product_id'], item['quantity'], item_price))
            print(f"Added item {item['product_id']} to order")  # Debug log
        
        # Kosongkan cart
        cur.execute("DELETE FROM carts WHERE user_id = %s", (session['user_id'],))
        
        mysql.connection.commit()
        print("Payment process completed successfully")  # Debug log
        
        return jsonify({
            'success': True,
            'redirect_url': url_for('order_success', order_id=order_id)
        })
        
    except Exception as e:
        print(f"Error in payment process: {str(e)}")  # Error log
        return jsonify({'success': False, 'message': str(e)})
        
    finally:
        cur.close()

@app.route('/add-address', methods=['GET', 'POST'])
def add_address():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        address = request.form['address']
        city = request.form['city']
        province = request.form['province']
        postal_code = request.form['postal_code']
        
        cur = mysql.connection.cursor()
        
        try:
            # Set semua alamat menjadi non-default
            cur.execute("""
                UPDATE addresses 
                SET is_default = 0 
                WHERE user_id = %s
            """, (session['user_id'],))
            
            # Tambah alamat baru sebagai default
            cur.execute("""
                INSERT INTO addresses 
                (user_id, address, city, province, postal_code, is_default)
                VALUES (%s, %s, %s, %s, %s, 1)
            """, (session['user_id'], address, city, province, postal_code))
            
            mysql.connection.commit()
            cur.close()
            
            flash('Alamat berhasil ditambahkan', 'success')
            return redirect(url_for('checkout'))
            
        except Exception as e:
            cur.close()
            flash('Gagal menambahkan alamat', 'error')
            return redirect(url_for('add_address'))
            
    return render_template('add_address.html')

@app.route('/order-success/<int:order_id>')
@login_required
def order_success(order_id):
    """Menampilkan halaman sukses setelah checkout"""
    cur = mysql.connection.cursor()
    
    # Ambil detail order
    cur.execute("""
        SELECT o.*, a.address, a.city, a.province, a.postal_code
        FROM orders o
        LEFT JOIN addresses a ON a.user_id = o.user_id AND a.is_default = 1
        WHERE o.id = %s AND o.user_id = %s
    """, (order_id, session['user_id']))
    
    order = cur.fetchone()
    
    if not order:
        return redirect(url_for('home'))
    
    # Ambil items dalam order
    cur.execute("""
        SELECT oi.*, p.name, p.part_number
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = %s
    """, (order_id,))
    
    order_items = cur.fetchall()
    
    cur.close()
    
    return render_template('order_success.html', 
                         order=order,
                         order_items=order_items)

@app.route('/order-history')
@login_required
def order_history():
    """Menampilkan riwayat pesanan user"""
    cur = mysql.connection.cursor()
    filter_type = request.args.get('filter', 'all')
    
    try:
        base_query = """
            SELECT 
                o.id,
                o.created_at,
                o.payment_status,
                o.final_amount,
                DATE_FORMAT(o.created_at, '%%d-%%m-%%Y') as order_date,
                COUNT(DISTINCT oi.product_id) as total_items,
                SUM(oi.quantity) as total_quantity,
                GROUP_CONCAT(DISTINCT p.name) as product_names,
                MIN(p.image_url) as preview_image,
                MIN(p.name) as preview_name
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            JOIN products p ON p.id = oi.product_id
            WHERE o.user_id = %s
        """
        
        params = [session['user_id']]
        
        if filter_type == 'today':
            base_query += " AND DATE(o.created_at) = CURDATE()"
        elif filter_type == 'week':
            base_query += " AND o.created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif filter_type == 'month':
            base_query += " AND o.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
            
        base_query += " GROUP BY o.id ORDER BY o.created_at DESC"
        
        cur.execute(base_query, params)
        orders = cur.fetchall()
        
        if orders:
            for order in orders:
                order['status_label'] = {
                    'pending': 'Menunggu Pembayaran',
                    'paid': 'Sudah Dibayar',
                    'cancelled': 'Dibatalkan'
                }.get(order['payment_status'], order['payment_status'])
                
                product_names = order['product_names'].split(',')
                order['preview_name'] = product_names[0]
                order['other_items'] = len(product_names) - 1 if len(product_names) > 1 else 0
                
                # Set image URL berdasarkan nama produk
                if order['preview_name'] == 'Paket Bore Up MX':
                    order['image_url'] = url_for('static', filename='images/products/bore-up-mx.png')
                elif order['preview_name'] == 'Paket Bore Up PCX 160':
                    order['image_url'] = url_for('static', filename='images/products/bore-up-pcx.png')
                elif order['preview_name'] == 'Busi NGK Iridium':
                    order['image_url'] = url_for('static', filename='images/products/busi-ngk.png')
                elif order['preview_name'] == 'Oli Motul 5100':
                    order['image_url'] = url_for('static', filename='images/products/oli-motul.png')
                elif order['preview_name'] == 'Shock YSS Twin':
                    order['image_url'] = url_for('static', filename='images/products/shock-yss.png')
                else:
                    order['image_url'] = order['preview_image']
                
        return render_template('order_history.html', 
                             orders=orders,
                             active_filter=filter_type)
                             
    except Exception as e:
        print(f"Error: {str(e)}")
        flash('Terjadi kesalahan', 'error')
        return render_template('order_history.html', 
                             orders=[],
                             active_filter=filter_type)
    finally:
        cur.close()

@app.route('/test-orders')
def test_orders():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'})
        
    cur = mysql.connection.cursor()
    
    try:
        # Test query orders
        cur.execute("""
            SELECT * FROM orders WHERE user_id = %s
        """, (session['user_id'],))
        orders = cur.fetchall()
        
        result = {
            'user_id': session['user_id'],
            'orders_count': len(orders),
            'orders': orders
        }
        
        # Test query order items
        if orders:
            cur.execute("""
                SELECT oi.*, p.name 
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                WHERE oi.order_id = %s
            """, (orders[0]['id'],))
            items = cur.fetchall()
            result['first_order_items'] = items
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cur.close()

# =========================================
# Helper Functions
# =========================================
def format_currency(amount):
    """Format angka ke format mata uang Rupiah"""
    return f"Rp {amount:,.0f}"

def calculate_discount(price, discount_percentage):
    """Menghitung harga setelah diskon"""
    return price * (100 - discount_percentage) / 100

if __name__ == '__main__':
    app.run(debug=True)

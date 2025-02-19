/* =========================================
            Database Configuration
   ========================================= */

DROP DATABASE IF EXISTS motor;
CREATE DATABASE motor;
USE motor;

/* =========================================
             User Management Tables
   ========================================= */

-- Tabel users untuk menyimpan data pengguna
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    profile_image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

/* =========================================
             Product Management Tables
   ========================================= */

-- Tabel categories untuk pengelompokan produk
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    icon_url VARCHAR(255)
);

-- Tabel products untuk data produk
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    image_url VARCHAR(255),
    category_id INT,
    part_number VARCHAR(50),
    compatible_vehicles TEXT,
    discount_percentage INT DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

/* =========================================
            Order Management Tables
   ========================================= */

-- Tabel addresses untuk alamat pengiriman
CREATE TABLE addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    address TEXT NOT NULL,
    city VARCHAR(100),
    province VARCHAR(100),
    postal_code VARCHAR(10),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Tabel orders untuk pesanan
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    shipping_cost DECIMAL(10,2) NOT NULL DEFAULT 0,
    payment_method VARCHAR(50) NOT NULL,
    payment_status ENUM('pending', 'paid', 'cancelled') DEFAULT 'pending',
    final_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Tabel order_items untuk detail item dalam pesanan
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabel carts untuk keranjang belanja
CREATE TABLE carts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE KEY user_product (user_id, product_id)
);

/* =========================================
                Initial Data
   ========================================= */

-- Data kategori default
INSERT INTO categories (name, icon_url) VALUES 
('Piston', '/static/images/categories/piston.png'),
('Oil', '/static/images/categories/oil.png'),
('Shock', '/static/images/categories/shock.png'),
('Electronic', '/static/images/categories/electronic.png'),
('All', '/static/images/categories/all.png');

-- Data produk 
INSERT INTO products (name, description, price, stock, image_url, category_id, part_number, compatible_vehicles, discount_percentage) VALUES 
('Paket Bore Up MX', 'Paket lengkap bore up untuk motor MX', 888000, 50, '/static/images/products/bore-up-mx.png', 1, 'BU-MX-001', 'Yamaha MX', 0),
('Paket Bore Up PCX 160', 'Paket bore up khusus PCX 160', 1090000, 30, '/static/images/products/bore-up-pcx.png', 1, 'BU-PCX160-001', 'Honda PCX 160', 0),
('Busi NGK Iridium', 'Busi NGK Iridium premium', 350000, 100, '/static/images/products/busi-ngk.png', 4, 'NGK-IR-001', 'Universal', 60),
('Oli Motul 5100', 'Oli mesin full synthetic', 255000, 200, '/static/images/products/oli-motul.png', 2, 'MTL-5100-001', 'Universal', 0),
('Shock YSS Twin', 'Shock absorber premium', 1850000, 20, '/static/images/products/shock-yss.png', 3, 'YSS-TW-001', 'Yamaha R15, R25', 0);

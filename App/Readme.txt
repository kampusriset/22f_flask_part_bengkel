CARA INSTALASI:
1. Install Python
2. pip install flask
3. pip install Flask-mysqldb
4. pip install flask flask-mysqldb werkzeug 
5. Masukkan Querry motor.sql ke Querry MySQL lalu Run

FITUR:
1. Login
2. Lupa Password
3. Sign Up / Daftar
4. Home
5. Keranjang
6. Riwayat
7. Keluar
8. Pencarian
9. Banner
10. Kategori
11. Checkout
12. Pembayaran
13. Penambahan Alamat
14. Detail Pemesanan

Alur Kerja Sistem: 
1. Tampilan Login akan diarahkan ke Home
2. Home dapat mengakses berbagai macam fitur antara lain:
    a. Keranjang
    b. Riwayat
    c. Keluar
    d. Pencarian
    e. Kategori
    f. Checkout Produk
3. Tampilan Keranjang menampilkan Keranjang Pemesanan yang akan di beli yang akan diarahkan ke menu Pembayaran
4. Menu Pembayaran menampilkan berbagai metode pembayaran dan input alamat dan Bayar
5. Pada menu Riwayat menampilkan Tampilan pembelian apa yang sudah dilakukan dengan fitur filter all, hari ini, minggu ini, bulan ini dan dapat menampilkan menu lihat Detail
6. Pada menu lihat Detail menampilkan Tampilan Riwayat pembelian secara lengkap dari nama produk hingga total harga, status pesanan dan metode pembayaran 
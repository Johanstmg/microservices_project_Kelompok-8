# Microservices E-Commerce System

Sistem ini terdiri dari beberapa layanan mikro yang terpisah (microservices) untuk membangun aplikasi e-commerce sederhana. Komunikasi antar layanan menggunakan protokol HTTP dengan data dalam format JSON.

## Struktur Proyek

```
microservices_project/
├── user_service/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   └── .env
├── inventory_service/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   └── .env
├── order_service/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   └── .env
├── payment_service/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   └── .env
└── frontend/
    ├── customer/
    │   ├── customerdashboard.html
    └── admin/
        └── dashboard.html
```

## Prasyarat

- Python 3.7+
- MySQL/MariaDB
- phpMyAdmin (opsional, untuk manajemen database visual)
- pip (Python package manager)

## Konfigurasi Database

1. Buatlah database untuk masing-masing service di MySQL:
   - `user_service`
   - `inventory_service`
   - `order_service`
   - `payment_service`

2. Setiap service membutuhkan file `.env` dengan konfigurasi sebagai berikut:
```
DATABASE_URL=mysql+pymysql://username:password@localhost/nama_database
```

Contoh untuk user_service:
```
DATABASE_URL=mysql+pymysql://root:@localhost/user_service
```

## Instalasi Dependensi

Di setiap folder service, jalankan perintah:

```bash
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv requests
```

## Menjalankan Services

Jalankan setiap service pada port yang berbeda. Buka 4 terminal terpisah dan jalankan:

1. User Service (port 8001):
```bash
cd user_service
uvicorn main:app --reload --port 8001
```

2. Inventory Service (port 8002):
```bash
cd inventory_service
uvicorn main:app --reload --port 8002
```

3. Order Service (port 8003):
```bash
cd order_service
uvicorn main:app --reload --port 8003
```

4. Payment Service (port 8004):
```bash
cd payment_service
uvicorn main:app --reload --port 8004
```

## Front-End

### Customer Pages

Frontend customer dapat diakses dengan membuka file `frontend/customer/index.html` pada browser. Pastikan semua service backend sudah berjalan terlebih dahulu.

Untuk menguji alur checkout:
1. Buka `index.html` di browser
2. Isi data pembeli (nama dan nomor HP)
3. Pilih produk dan jumlah yang diinginkan
4. Klik "Pesan" untuk melakukan checkout
5. Di halaman order, pilih metode pembayaran
6. Klik "Bayar Sekarang" dalam waktu 10 detik untuk menyelesaikan pembayaran

### Admin Dashboard

Dashboard admin dapat diakses dengan membuka file `frontend/admin/dashboard.html` pada browser. Pastikan semua service backend sudah berjalan terlebih dahulu.

Fitur dashboard admin:
1. Melihat pesanan yang sudah dibayar tetapi belum dikonfirmasi
2. Mengkonfirmasi pesanan untuk update stok dan menandainya sebagai selesai
3. Melihat riwayat pesanan yang sudah dikonfirmasi

## Alur Aplikasi

1. Customer mengakses landing page (`index.html`)
2. Customer mengisi data diri (nama dan nomor HP) yang disimpan di User Service
3. Customer memilih produk dan jumlah dari Inventory Service
4. Order dibuat dan disimpan di Order Service
5. Customer diarahkan ke halaman pembayaran (`order.html`) 
6. Customer memilih metode pembayaran dan menyelesaikan pembayaran dalam 10 detik
7. Payment Service memproses pembayaran dan memperbarui status pembayaran di Order Service
8. Admin dapat melihat pesanan yang dibayar di dashboard
9. Admin mengkonfirmasi pesanan yang mengupdate stok di Inventory Service
10. Order Service menandai pesanan sebagai terkonfirmasi

## API Endpoints

### User Service (`localhost:8001`)
- `POST /users` - Membuat user baru
- `GET /users` - Mendapatkan semua user
- `GET /users/{user_id}` - Mendapatkan data user berdasarkan ID

### Inventory Service (`localhost:8002`)
- `POST /products` - Membuat produk baru 
- `GET /products` - Mendapatkan semua produk
- `GET /products/{product_id}` - Mendapatkan detail produk
- `PUT /products/{product_id}` - Mengupdate produk
- `PUT /products/{product_id}/stock` - Mengupdate stok produk
- `GET /products/1/check-stock?quantity={yang ingin dicek}` - Memeriksa ketersediaan stok
- `DELETE /products/{product_id}` - Menghapus produk

### Order Service (`localhost:8003`)
- `POST /orders` - Membuat pesanan baru
- `GET /orders` - Mendapatkan semua pesanan
- `GET /orders/{order_id}` - Mendapatkan detail pesanan
- `GET /orders/{order_id}/detail` - Mendapatkan detail lengkap pesanan dengan info user dan produk
- `GET /orders/user/{user_id}` - Mendapatkan pesanan berdasarkan user ID
- `PUT /orders/{order_id}/confirm` - Mengkonfirmasi pesanan
- `PUT /orders/{order_id}/payment` - Mengupdate status pembayaran pesanan

### Payment Service (`localhost:8004`)
- `POST /payments` - Membuat pembayaran baru
- `POST /payments/confirm` - Mengkonfirmasi pembayaran
- `GET /payments` - Mendapatkan semua pembayaran
- `GET /payments/{payment_id}` - Mendapatkan detail pembayaran
- `GET /payments/order/{order_id}` - Mendapatkan pembayaran berdasarkan order ID

## Pengisian Data Awal

Sebelum menggunakan aplikasi, tambahkan beberapa produk melalui endpoint Inventory Service:

```
POST http://localhost:8002/products
{
    "name": "Sepatu Sport",
    "price": 250000,
    "stock": 10
}
```

```
POST http://localhost:8002/products
{
    "name": "Tas Ransel",
    "price": 150000,
    "stock": 15
}
```

## Troubleshooting

1. Pastikan semua service berjalan pada port yang ditentukan
2. Periksa konfigurasi database di file `.env` masing-masing service
3. Periksa bahwa MySQL/MariaDB sudah berjalan
4. Jika terjadi error CORS, pastikan middleware CORS sudah dikonfigurasi dengan benar
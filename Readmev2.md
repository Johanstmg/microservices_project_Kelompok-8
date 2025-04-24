# E-Commerce Microservices Project

A microservices-based e-commerce system built with FastAPI, Vue.js, and MySQL. The system consists of 4 main services that handle different aspects of the e-commerce flow.

## Architecture Overview

### Services
1. **User Service** (Port 8001)
   - Handles user management and authentication
   - Database: `user_service`

2. **Inventory Service** (Port 8002) 
   - Manages product inventory and stock
   - Database: `inventory_service`

3. **Order Service** (Port 8003)
   - Handles order processing and management
   - Database: `order_service`

4. **Payment Service** (Port 8004)
   - Manages payment processing and status
   - Database: `payment_service`

### Service Communication Flow
```
[Frontend (Customer/Admin)] 
         ↓
[User Service] → [Inventory Service]
         ↓              ↓
  [Order Service] ← [Payment Service]
```

## API Endpoints & Methods

### User Service (8001)
- `POST /users` - Create new user
- `GET /users` - Get all users
- `GET /users/{user_id}` - Get specific user

### Inventory Service (8002)
- `POST /products` - Add new product
- `GET /products` - Get all products
- `GET /products/{product_id}` - Get specific product
- `PUT /products/{product_id}` - Update product
- `PUT /products/{product_id}/stock` - Update product stock
- `GET /products/{product_id}/check-stock` - Check product stock
- `DELETE /products/{product_id}` - Delete product

### Order Service (8003)
- `POST /orders` - Create new order
- `GET /orders` - Get all orders
- `GET /orders/{order_id}` - Get specific order
- `GET /orders/{order_id}/detail` - Get order details with user and product info
- `GET /orders/user/{user_id}` - Get user's orders
- `PUT /orders/{order_id}/confirm` - Confirm order

### Payment Service (8004)
- `POST /payments` - Create new payment
- `POST /payments/confirm` - Confirm payment
- `GET /payments` - Get all payments
- `GET /payments/{payment_id}` - Get specific payment
- `GET /payments/order/{order_id}` - Get payment by order ID

## Setup & Installation

### Prerequisites
- Python 3.8+
- MySQL
- Node.js (for frontend)

### Database Setup
1. Create MySQL databases:
```sql
CREATE DATABASE user_service;
CREATE DATABASE inventory_service;
CREATE DATABASE order_service;
CREATE DATABASE payment_service;
```

2. Configure database connection in each service's `.env` file:
```env
DATABASE_URL=mysql+pymysql://root:@localhost/service_name
```

### Installing Dependencies
```bash
# Install Python dependencies for each service
cd user_service
pip install -r requirements.txt
# Repeat for other services
```

### Running the Services
1. Start each service:
```bash
# Start User Service
cd user_service
uvicorn main:app --reload --port 8001

# Start Inventory Service
cd inventory_service
uvicorn main:app --reload --port 8002

# Start Order Service
cd order_service
uvicorn main:app --reload --port 8003

# Start Payment Service
cd payment_service
uvicorn main:app --reload --port 8004
```

2. Access the frontend:
- Customer: Open `frontend/customer/index.html`
- Admin: Open `frontend/admin/dashboard.html`

## Important Information

### Payment Flow
1. Customer adds products to cart
2. Creates order(s)
3. Payment created with 15-second timeout
4. If payment confirmed, order status updated
5. Admin confirms order and updates inventory

### Stock Management
- Stock checked before order creation
- Stock updated after order confirmation
- Supports both increment and decrement

### Error Handling
- Stock validation
- Payment timeout
- Order confirmation rules
- Data consistency checks

### Security Notes
- CORS enabled for development
- Basic input validation implemented
- No authentication system (can be added)

## Frontend Features

### Customer Dashboard
- User registration
- Product browsing
- Cart management
- Order creation
- Payment processing

### Admin Dashboard
- Inventory management
- Order confirmation
- Stock adjustment
- Order history
- Real-time updates (15s polling)

## Development Notes

### Database Models
- Each service has its own database
- Models defined in `models.py`
- SQLAlchemy ORM used

### API Response Formats
- Consistent error responses
- Structured success responses
- Data validation with Pydantic


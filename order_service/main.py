from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import models
from database import engine, get_db
import requests
import time
from datetime import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int = 1

class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    total_price: int
    payment_status: bool
    confirmed: bool
    created_at: datetime

    class Config:
        orm_mode = True

class OrderDetail(BaseModel):
    id: int
    user: dict
    product: dict
    quantity: int
    total_price: int
    payment_status: bool
    confirmed: bool
    created_at: datetime

@app.post("/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # Check if user exists
    try:
        user_response = requests.get(f"http://localhost:8001/users/{order.user_id}")
        user_response.raise_for_status()
        user = user_response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check product and stock
    try:
        product_response = requests.get(f"http://localhost:8002/products/{order.product_id}")
        product_response.raise_for_status()
        product = product_response.json()
        
        # Check stock
        stock_response = requests.get(
            f"http://localhost:8002/products/{order.product_id}/check-stock",
            params={"quantity": order.quantity}
        )
        stock_info = stock_response.json()
        
        if not stock_info["available"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough stock. Available: {stock_info['stock']}"
            )
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=404, detail="Product not found or stock check failed")
    
    # Calculate total price
    total_price = product["price"] * order.quantity
    
    # Create order
    db_order = models.Order(
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity,
        total_price=total_price,
        payment_status=False,
        confirmed=False
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Return order with payment token
    return db_order

@app.get("/orders", response_model=List[OrderResponse])
def get_all_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).all()
    return orders

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/orders/{order_id}/detail")
def get_order_detail(order_id: int, db: Session = Depends(get_db)):
    # Get basic order info
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get user info
    try:
        user_response = requests.get(f"http://localhost:8001/users/{order.user_id}")
        user_response.raise_for_status()
        user = user_response.json()
    except:
        user = {"id": order.user_id, "name": "Unknown User", "phone": "Unknown"}
    
    # Get product info
    try:
        product_response = requests.get(f"http://localhost:8002/products/{order.product_id}")
        product_response.raise_for_status()
        product = product_response.json()
    except:
        product = {"id": order.product_id, "name": "Unknown Product", "price": 0}
    
    # Return detailed order
    return {
        "id": order.id,
        "user": user,
        "product": product,
        "quantity": order.quantity,
        "total_price": order.total_price,
        "payment_status": order.payment_status,
        "confirmed": order.confirmed,
        "created_at": order.created_at
    }

@app.get("/orders/user/{user_id}", response_model=List[OrderDetail])
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    
    if not orders:
        return []
    
    # Get user info once
    try:
        user_response = requests.get(f"http://localhost:8001/users/{user_id}")
        user_response.raise_for_status()
        user = user_response.json()
    except:
        user = {"id": user_id, "name": "Unknown User", "phone": "Unknown"}
    
    detailed_orders = []
    
    for order in orders:
        # Get product info
        try:
            product_response = requests.get(f"http://localhost:8002/products/{order.product_id}")
            product_response.raise_for_status()
            product = product_response.json()
        except:
            product = {"id": order.product_id, "name": "Unknown Product", "price": 0}
        
        detailed_orders.append({
            "id": order.id,
            "user": user,
            "product": product,
            "quantity": order.quantity,
            "total_price": order.total_price,
            "payment_status": order.payment_status,
            "confirmed": order.confirmed,
            "created_at": order.created_at
        })
    
    return detailed_orders

@app.put("/orders/{order_id}/confirm")
def confirm_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if not order.payment_status:
        raise HTTPException(status_code=400, detail="Order not paid yet")
    
    # Update stock
    try:
        requests.put(
            f"http://localhost:8002/products/{order.product_id}/stock",
            json={"quantity": -order.quantity}
        )
    except:
        raise HTTPException(status_code=500, detail="Failed to update inventory")
    
    # Confirm order
    order.confirmed = True
    db.commit()
    db.refresh(order)
    
    return {"message": "Order confirmed successfully"}

# ... (kode import dan lainnya) ...

@app.get("/orders/unconfirmed/list") # Endpoint yang digunakan dashboard admin
def get_unconfirmed_paid_orders(db: Session = Depends(get_db)):
    # Get orders that are paid but not confirmed
    orders = db.query(models.Order).filter(
        models.Order.payment_status == True, # Hanya ambil yang sudah bayar
        models.Order.confirmed == False     # Hanya ambil yang belum dikonfirmasi
    ).order_by(models.Order.created_at.asc()).all() # Urutkan berdasarkan waktu dibuat

    if not orders:
        return []

    detailed_orders = []

    for order in orders:
        # Get user info
        try:
            user_response = requests.get(f"http://localhost:8001/users/{order.user_id}")
            user_response.raise_for_status()
            user = user_response.json()
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to get user {order.user_id}: {e}") # Log warning
            user = {"id": order.user_id, "name": "N/A", "phone": "N/A"}

        # Get product info
        try:
            product_response = requests.get(f"http://localhost:8002/products/{order.product_id}")
            product_response.raise_for_status()
            product = product_response.json()
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to get product {order.product_id}: {e}") # Log warning
            product = {"id": order.product_id, "name": "N/A", "price": 0}

        # !!! PERBAIKAN DI SINI !!!
        # Tambahkan 'payment_status' ke dictionary yang dikirim ke frontend
        detailed_orders.append({
            "id": order.id,
            "user": user,
            "product": product,
            "quantity": order.quantity,
            "total_price": order.total_price,
            "created_at": order.created_at,
            "payment_status": "COMPLETED" # Tambahkan baris ini
            # Anda juga bisa menambahkan 'confirmed': order.confirmed (yaitu False) jika diperlukan frontend
        })

    return detailed_orders

# ... (sisa kode di main.py) ...
class OrderPaymentUpdate(BaseModel):
    payment_status: bool

@app.put("/orders/{order_id}/payment")
def update_payment_status(order_id: int, payment_update: OrderPaymentUpdate, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.payment_status = payment_update.payment_status
    db.commit()
    db.refresh(order)
    
    return {"message": "Payment status updated successfully"}
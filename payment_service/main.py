from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import models
from database import engine, get_db
import requests
from datetime import datetime
import asyncio
from sqlalchemy import update

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
class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str = "CASH"  # Default payment method

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: int
    payment_method: str
    status: bool
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class PaymentConfirm(BaseModel):
    payment_id: int

# Function to cancel payment if not completed in time
async def cancel_payment_after_timeout(payment_id: int, order_id: int, db: Session):
    await asyncio.sleep(100)  # Wait for 10 seconds
    
    # Get a fresh db session (since the original one might be closed)
    db = next(get_db())
    
    # Check if payment is completed
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    
    if payment and not payment.status:
        # Mark payment as expired
        db.query(models.Payment).filter(models.Payment.id == payment_id).delete()
        db.commit()
        print(f"Payment {payment_id} has expired and been deleted")

@app.post("/payments", response_model=PaymentResponse)
async def create_payment(
    payment: PaymentCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    # Get order details to get amount
    try:
        order_response = requests.get(f"http://localhost:8003/orders/{payment.order_id}")
        order_response.raise_for_status()
        order = order_response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if payment for this order already exists
    existing_payment = db.query(models.Payment).filter(
        models.Payment.order_id == payment.order_id,
        models.Payment.status == True
    ).first()
    
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment for this order already exists")
    
    # Create new payment
    db_payment = models.Payment(
        order_id=payment.order_id,
        amount=order["total_price"],
        payment_method=payment.payment_method,
        status=False
    )
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # Start background task to cancel payment if not completed in time
    background_tasks.add_task(
        cancel_payment_after_timeout, 
        db_payment.id, 
        payment.order_id, 
        db
    )
    
    return db_payment

@app.post("/payments/confirm", response_model=PaymentResponse)
def confirm_payment(payment_confirm: PaymentConfirm, db: Session = Depends(get_db)):
    # Get payment
    payment = db.query(models.Payment).filter(models.Payment.id == payment_confirm.payment_id).first()
    
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment expired or not found")
    
    # Update payment status
    payment.status = True
    payment.completed_at = datetime.now()
    db.commit()
    db.refresh(payment)
    
    # Update order payment status
    try:
        requests.put(
            f"http://localhost:8003/orders/{payment.order_id}/payment",
            json={"payment_status": True}
        )
    except:
        # Revert payment if order update fails
        payment.status = False
        payment.completed_at = None
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to update order payment status")
    
    return payment

@app.get("/payments", response_model=List[PaymentResponse])
def get_all_payments(db: Session = Depends(get_db)):
    payments = db.query(models.Payment).all()
    return payments

@app.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@app.get("/payments/order/{order_id}", response_model=Optional[PaymentResponse])
def get_payment_by_order(order_id: int, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(
        models.Payment.order_id == order_id,
        models.Payment.status == True
    ).first()
    return payment
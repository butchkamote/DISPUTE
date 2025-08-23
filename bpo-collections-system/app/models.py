from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'team_leader' or 'data_analyst'

class PaymentRecord(db.Model):
    __tablename__ = 'payment_record'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign = db.Column(db.String(50), nullable=False)
    dpd = db.Column(db.Integer, nullable=False)
    loan_id = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date_paid = db.Column(db.Date, nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship using back_populates instead of backref
    proofs = db.relationship('PaymentProof', back_populates='payment', lazy=True, cascade='all, delete-orphan')
    disputes = db.relationship('Dispute', backref='payment_record', lazy=True)

class PaymentProof(db.Model):
    __tablename__ = 'payment_proof'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment_record.id', ondelete='CASCADE'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'receipt', 'email', 'screenshot', etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define the relationship from this side using back_populates
    payment = db.relationship('PaymentRecord', back_populates='proofs')

class Dispute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('payment_record.id'), nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    corrected_details = db.Column(db.Text, nullable=False)
    # Update status options to include pending_da_review
    status = db.Column(db.String(20), default='pending')  # pending, pending_da_review, approved, rejected
    created_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_by = db.Column(db.String(100))
    validated_at = db.Column(db.DateTime)
    validation_comments = db.Column(db.Text)
    # Add fields for DA review
    da_verified_by = db.Column(db.String(100))
    da_verified_at = db.Column(db.DateTime)
    da_comments = db.Column(db.Text)

class ExportHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    export_type = db.Column(db.String(20), nullable=False)  # 'campaign' or 'dispute'
    campaign = db.Column(db.String(50))  # Only for campaign exports
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    record_count = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    created_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
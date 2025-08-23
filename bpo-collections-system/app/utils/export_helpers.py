import os
import pandas as pd
from flask import current_app
from datetime import datetime

def export_to_csv(df, filename, include_headers=True):
    """Export DataFrame to CSV file"""
    # Create exports directory if it doesn't exist
    export_dir = os.path.join(current_app.root_path, '..', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # Full path to save the CSV file
    file_path = os.path.join(export_dir, filename)
    
    # Export to CSV
    df.to_csv(file_path, index=False, header=include_headers)
    
    return file_path

def export_campaign_data(campaign=None, start_date=None, end_date=None, include_headers=True):
    """Export campaign data to CSV file"""
    from app.models import PaymentRecord
    from app import db
    
    # Build query
    query = PaymentRecord.query
    
    if campaign:
        query = query.filter_by(campaign=campaign)
    if start_date:
        query = query.filter(PaymentRecord.date_paid >= start_date)
    if end_date:
        query = query.filter(PaymentRecord.date_paid <= end_date)
        
    records = query.all()
    
    # Create DataFrame
    columns = ['Loan ID', 'Campaign', 'DPD', 'Amount', 'Date Paid', 'Operator Name', 'Customer Name']
    data = [(r.loan_id, r.campaign, r.dpd, r.amount, r.date_paid, 
            r.operator_name, r.customer_name) for r in records]
    
    df = pd.DataFrame(data, columns=columns)
    
    # Generate filename
    filename = f"{campaign or 'all'}_records_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    
    # Export to CSV
    return export_to_csv(df, filename, include_headers), filename, len(records)

def export_dispute_data(start_date=None, end_date=None, include_headers=True):
    """Export approved dispute data to CSV file"""
    from app.models import Dispute
    from app import db
    
    # Build query
    query = Dispute.query.filter_by(status='approved')
    
    if start_date or end_date:
        query = query.join(Dispute.payment_record)
        
        if start_date:
            query = query.filter(PaymentRecord.date_paid >= start_date)
        if end_date:
            query = query.filter(PaymentRecord.date_paid <= end_date)
    
    records = query.all()
    
    # Create DataFrame
    columns = ['ID', 'Entry ID', 'Reason', 'Corrected Details', 'Validated By', 'Validation Date']
    data = [(d.id, d.entry_id, d.reason, d.corrected_details,
            d.validated_by, d.validated_at) for d in records]
    
    df = pd.DataFrame(data, columns=columns)
    
    # Generate filename
    filename = f"validated_disputes_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    
    # Export to CSV
    return export_to_csv(df, filename, include_headers), filename, len(records)
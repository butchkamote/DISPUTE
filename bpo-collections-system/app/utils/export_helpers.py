import os
import pandas as pd
from datetime import datetime
from flask import current_app

def export_to_excel(data_dict, filename):
    """
    Export data dictionary to Excel file with multiple sheets
    
    Args:
        data_dict: Dictionary where keys are sheet names and values are DataFrames
        filename: Name of the Excel file to create
    
    Returns:
        Path to the created Excel file
    """
    # Create exports directory if it doesn't exist
    export_dir = os.path.join(current_app.root_path, '..', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # Full path for the export file
    export_path = os.path.join(export_dir, filename)
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter(export_path, engine='xlsxwriter') as writer:
        for sheet_name, df in data_dict.items():
            # Clean sheet name (Excel has 31 character limit and no special chars)
            safe_sheet_name = str(sheet_name)[:31]
            safe_sheet_name = ''.join(c if c.isalnum() or c in [' ', '_'] else '_' for c in safe_sheet_name)
            if not safe_sheet_name:
                safe_sheet_name = "Sheet1"
            
            # Write dataframe to sheet
            df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            
            # Auto-adjust columns width
            worksheet = writer.sheets[safe_sheet_name]
            for i, col in enumerate(df.columns):
                max_width = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2  # Add a little extra space
                worksheet.set_column(i, i, max_width)
    
    return export_path

def export_campaign_data(campaign=None, start_date=None, end_date=None, include_headers=True):
    """
    Export campaign data to Excel file with multiple sheets by campaign
    """
    from app.models import PaymentRecord
    from sqlalchemy import func
    
    # Build base query
    query = PaymentRecord.query
    
    # Apply filters
    if campaign:
        query = query.filter_by(campaign=campaign)
    if start_date:
        query = query.filter(PaymentRecord.date_paid >= start_date)
    if end_date:
        query = query.filter(PaymentRecord.date_paid <= end_date)
    
    # Get all records
    records = query.all()
    
    # Group records by campaign
    campaigns = {}
    for record in records:
        campaign_name = record.campaign or "No Campaign"
        if campaign_name not in campaigns:
            campaigns[campaign_name] = []
        
        campaigns[campaign_name].append({
            'Loan ID': record.loan_id,
            'Customer Name': record.customer_name,
            'Amount': record.amount,
            'Date Paid': record.date_paid,
            'Operator': record.operator_name,
            'Campaign': record.campaign,
            'DPD': record.dpd,
            'Entry Date': record.created_at
        })
    
    # Create a dictionary of DataFrames by campaign
    data_dict = {}
    record_count = 0
    
    # Create a summary sheet
    summary_data = []
    
    for campaign_name, campaign_records in campaigns.items():
        # Convert records to DataFrame
        df = pd.DataFrame(campaign_records)
        data_dict[campaign_name] = df
        count = len(campaign_records)
        record_count += count
        
        # Add to summary
        summary_data.append({
            'Campaign': campaign_name,
            'Record Count': count,
            'Total Amount': sum(r['Amount'] for r in campaign_records)
        })
    
    # Add summary sheet
    summary_df = pd.DataFrame(summary_data)
    data_dict['Summary'] = summary_df
    
    # Generate filename
    if campaign:
        filename = f"{campaign}_records_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    else:
        filename = f"all_records_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    
    # Export to Excel with multiple sheets
    export_path = export_to_excel(data_dict, filename)
    
    return export_path, filename, record_count

def export_dispute_data(start_date=None, end_date=None, include_headers=True):
    """Export approved dispute data to Excel file"""
    from app.models import Dispute, PaymentRecord
    
    # Build query
    query = Dispute.query.filter_by(status='approved')
    
    if start_date or end_date:
        query = query.join(Dispute.payment_record)
        
        if start_date:
            query = query.filter(PaymentRecord.date_paid >= start_date)
        if end_date:
            query = query.filter(PaymentRecord.date_paid <= end_date)
    
    records = query.all()
    
    # Group disputes by campaign
    campaigns = {}
    for dispute in records:
        campaign_name = dispute.payment_record.campaign or "No Campaign"
        if campaign_name not in campaigns:
            campaigns[campaign_name] = []
        
        campaigns[campaign_name].append({
            'Dispute ID': dispute.id,
            'Loan ID': dispute.payment_record.loan_id,
            'Customer Name': dispute.payment_record.customer_name,
            'Amount': dispute.payment_record.amount,
            'Original Operator': dispute.payment_record.operator_name,
            'Reason': dispute.reason,
            'Corrected Details': dispute.corrected_details,
            'Validated By': dispute.validated_by,
            'Validation Date': dispute.validated_at,
            'DA Verified By': dispute.da_verified_by,
            'DA Verification Date': dispute.da_verified_at
        })
    
    # Create DataFrames by campaign
    data_dict = {}
    record_count = 0
    
    # Create summary sheet data
    summary_data = []
    
    for campaign_name, campaign_disputes in campaigns.items():
        df = pd.DataFrame(campaign_disputes)
        data_dict[campaign_name] = df
        count = len(campaign_disputes)
        record_count += count
        
        # Add to summary
        summary_data.append({
            'Campaign': campaign_name,
            'Dispute Count': count
        })
    
    # Add summary sheet
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        data_dict['Summary'] = summary_df
    
    # Generate filename
    filename = f"validated_disputes_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    
    # Export to Excel with multiple sheets
    export_path = export_to_excel(data_dict, filename)
    
    return export_path, filename, record_count
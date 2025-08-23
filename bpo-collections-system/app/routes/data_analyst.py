from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import PaymentRecord, Dispute, ExportHistory
from app.forms import CampaignFilterForm, ExportForm
from app.utils.export_helpers import export_to_csv
import pandas as pd
from datetime import datetime
import os

# Single blueprint definition with a url_prefix
bp = Blueprint('data_analyst', __name__, url_prefix='/data-analyst')

@bp.route('/campaign-filter', methods=['GET'])
@login_required
def campaign_filter():
    if current_user.role != 'data_analyst':
        flash('Access denied: Data Analyst role required', 'danger')
        return redirect(url_for('main.index'))
    
    form = CampaignFilterForm()
    
    # Get filter parameters
    campaign = request.args.get('campaign', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    operator = request.args.get('operator', '')
    min_amount = request.args.get('min_amount', '')
    max_amount = request.args.get('max_amount', '')
    
    # Build query
    query = PaymentRecord.query
    
    if campaign:
        query = query.filter_by(campaign=campaign)
    if start_date:
        query = query.filter(PaymentRecord.date_paid >= start_date)
    if end_date:
        query = query.filter(PaymentRecord.date_paid <= end_date)
    if operator:
        query = query.filter(PaymentRecord.operator_name.like(f'%{operator}%'))
    if min_amount:
        query = query.filter(PaymentRecord.amount >= float(min_amount))
    if max_amount:
        query = query.filter(PaymentRecord.amount <= float(max_amount))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.order_by(PaymentRecord.date_paid.desc()).paginate(page=page, per_page=per_page)
    entries = pagination.items
    total_pages = pagination.pages
    
    # Get unique campaigns for the dropdown
    all_campaigns = db.session.query(PaymentRecord.campaign).distinct().all()
    campaigns = [c[0] for c in all_campaigns]
    
    # Build filter parameters dict for pagination links
    filter_params = {}
    if campaign:
        filter_params['campaign'] = campaign
    if start_date:
        filter_params['start_date'] = start_date
    if end_date:
        filter_params['end_date'] = end_date
    if operator:
        filter_params['operator'] = operator
    if min_amount:
        filter_params['min_amount'] = min_amount
    if max_amount:
        filter_params['max_amount'] = max_amount
    
    return render_template(
        'data_analyst/campaign_filter.html',
        form=form,
        entries=entries,
        campaigns=campaigns,
        selected_campaign=campaign,
        start_date=start_date,
        end_date=end_date,
        operator=operator,
        min_amount=min_amount,
        max_amount=max_amount,
        page=page,
        total_pages=total_pages,
        filter_params=filter_params
    )

@bp.route('/export-data', methods=['GET', 'POST'])
@login_required
def export_data():
    if current_user.role != 'data_analyst':
        flash('Access denied: Data Analyst role required', 'danger')
        return redirect(url_for('main.index'))
    
    form = ExportForm()
    
    # Get all campaigns for the dropdown
    all_campaigns = db.session.query(PaymentRecord.campaign).distinct().all()
    form.campaign.choices = [('', 'All Campaigns')] + [(c[0], c[0]) for c in all_campaigns]
    
    if form.validate_on_submit():
        export_type = form.export_type.data
        campaign = form.campaign.data if export_type == 'campaign' else None
        start_date = form.start_date.data
        end_date = form.end_date.data
        include_headers = form.include_headers.data
        
        try:
            # Build query based on export type
            if export_type == 'campaign':
                records = PaymentRecord.query
                if campaign:
                    records = records.filter_by(campaign=campaign)
                filename = f"{campaign or 'all'}_records_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                columns = ['Loan ID', 'Campaign', 'DPD', 'Amount', 'Date Paid', 'Operator Name', 'Customer Name']
            else:  # disputes
                records = Dispute.query.filter_by(status='approved')
                filename = f"validated_disputes_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                columns = ['ID', 'Entry ID', 'Reason', 'Corrected Details', 'Validated By', 'Validation Date']
            
            # Apply date filters
            if start_date:
                records = records.filter(PaymentRecord.date_paid >= start_date)
            if end_date:
                records = records.filter(PaymentRecord.date_paid <= end_date)
            
            records = records.all()
            record_count = len(records)
            
            if export_type == 'campaign':
                data = [(r.loan_id, r.campaign, r.dpd, r.amount, r.date_paid, 
                        r.operator_name, r.customer_name) for r in records]
            else:
                data = [(d.id, d.entry_id, d.reason, d.corrected_details,
                        d.validated_by, d.validated_at) for d in records]
            
            df = pd.DataFrame(data, columns=columns)
            csv_path = export_to_csv(df, filename, include_headers)
            
            # Record the export
            export_history = ExportHistory(
                export_type=export_type,
                campaign=campaign if export_type == 'campaign' else None,
                start_date=start_date,
                end_date=end_date,
                record_count=record_count,
                filename=filename,
                created_by=current_user.username
            )
            db.session.add(export_history)
            db.session.commit()
            
            return send_file(csv_path, as_attachment=True, download_name=filename)
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error exporting data: {str(e)}', 'danger')
    
    # Get export history
    export_history = ExportHistory.query.order_by(ExportHistory.created_at.desc()).limit(10).all()
    
    return render_template('data_analyst/export.html', form=form, export_history=export_history)

@bp.route('/download-export/<int:export_id>')
@login_required
def download_export(export_id):
    if current_user.role != 'data_analyst':
        flash('Access denied: Data Analyst role required', 'danger')
        return redirect(url_for('main.index'))
    
    export_record = ExportHistory.query.get_or_404(export_id)
    
    # Check if file exists
    export_dir = os.path.join(current_app.root_path, '..', 'exports')
    file_path = os.path.join(export_dir, export_record.filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=export_record.filename)
    else:
        flash('Export file not found. It may have been deleted.', 'danger')
        return redirect(url_for('data_analyst.export_data'))
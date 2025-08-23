from flask import Blueprint, request, render_template, redirect, url_for, flash, send_file, send_from_directory
from flask_login import login_required, current_user
from app.models import PaymentRecord, Dispute, ExportHistory
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload  # Add this import
from app.utils.export_helpers import export_campaign_data, export_dispute_data
from app.forms import CampaignFilterForm, ExportForm

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
    
    # Import necessary modules
    import pandas as pd
    import os
    from flask import current_app
    from app.utils.export_helpers import export_campaign_data, export_dispute_data
    from app.forms import ExportForm  # Add this import
    
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
            # Use helper functions for export
            if export_type == 'campaign':
                csv_path, filename, record_count = export_campaign_data(
                    campaign, start_date, end_date, include_headers
                )
            else:  # disputes
                csv_path, filename, record_count = export_dispute_data(
                    start_date, end_date, include_headers
                )
            
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

@bp.route('/download-export/<filename>')
@login_required
def download_export(filename):
    if current_user.role != 'data_analyst':
        flash('Access denied: Data Analyst role required', 'danger')
        return redirect(url_for('main.index'))
    
    # Security check - validate filename to prevent path traversal
    if not filename or '..' in filename or filename.startswith('/'):
        flash('Invalid filename', 'danger')
        return redirect(url_for('data_analyst.export_data'))
    
    # Path to the export file
    export_dir = os.path.join(current_app.root_path, '..', 'exports')
    return send_from_directory(export_dir, filename, as_attachment=True)

@bp.route('/dispute-review', methods=['GET', 'POST'])
@login_required
def dispute_review():
    if current_user.role != 'data_analyst':
        flash('Access denied: Data Analyst role required', 'danger')
        return redirect(url_for('auth.login'))
    
    # Load disputes that have been approved by Team Leaders but need DA verification
    disputes = Dispute.query.filter_by(status='pending_da_review')\
        .join(PaymentRecord, Dispute.entry_id == PaymentRecord.id)\
        .options(joinedload(Dispute.payment_record))\
        .order_by(Dispute.validated_at.desc())\
        .all()
    
    # Handle form submission if this is a POST request
    if request.method == 'POST':
        dispute_id = request.form.get('dispute_id')
        action = request.form.get('action')
        comments = request.form.get('comments', '')
        
        dispute = Dispute.query.get_or_404(dispute_id)
        
        try:
            if action == 'approve':
                dispute.status = 'approved'
                dispute.da_verified_by = current_user.username
                dispute.da_comments = comments
                dispute.da_verified_at = datetime.utcnow()
                flash('Dispute verified and finalized', 'success')
            elif action == 'reject':
                # Sending back to Team Leader for reconsideration
                dispute.status = 'pending'
                dispute.da_verified_by = current_user.username
                dispute.da_comments = comments
                dispute.da_verified_at = datetime.utcnow()
                flash('Dispute returned to Team Leader for reconsideration', 'warning')
            
            db.session.commit()
            return redirect(url_for('data_analyst.dispute_review'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing dispute: {str(e)}', 'danger')
    
    return render_template('data_analyst/dispute_review.html', disputes=disputes)
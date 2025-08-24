from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user
from app.models import PaymentRecord, Dispute, PaymentProof
from app.forms import PaymentEntryForm, PaymentRecordSearchForm  # Add this import
from app import db
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload  # Add this import at the top
from app.utils.file_helpers import save_payment_proofs
import os
from flask import current_app

# Single blueprint definition
bp = Blueprint('team_leader', __name__, url_prefix='/team-leader')

@bp.route('/data-entry', methods=['GET', 'POST'])
@login_required
def data_entry():
    if current_user.role != 'team_leader':
        flash('Access denied: Team Leader role required', 'danger')
        return redirect(url_for('auth.login'))
        
    form = PaymentEntryForm()
    
    if form.validate_on_submit():
        # Check if proof files were provided
        if not form.proof_images.data or not form.proof_images.data[0]:
            flash('At least one proof of payment is required', 'danger')
            return render_template('team_leader/data_entry.html', form=form)
        
        try:
            # Create the payment record first
            new_record = PaymentRecord(
                campaign=form.campaign.data,
                dpd=form.dpd.data,
                loan_id=form.loan_id.data,
                amount=form.amount.data,
                date_paid=form.date_paid.data,
                operator_name=form.operator_name.data,
                customer_name=form.customer_name.data
            )
            
            db.session.add(new_record)
            db.session.flush()  # Get the new record's ID without committing yet
            
            # Handle file uploads
            proof_files = form.proof_images.data
            proof_type = form.proof_types.data
            
            proof_data = save_payment_proofs(proof_files, proof_type)
            
            # Create PaymentProof records for each file
            for proof in proof_data:
                proof_record = PaymentProof(
                    payment_id=new_record.id,
                    file_path=proof['path'],
                    file_type=proof['type']
                )
                db.session.add(proof_record)
            
            db.session.commit()
            flash('Payment details and proof added successfully!', 'success')
            return redirect(url_for('team_leader.data_entry'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding record: {str(e)}', 'danger')
    
    # Get recent entries for display
    recent_entries = PaymentRecord.query.order_by(PaymentRecord.created_at.desc()).limit(10).all()
    
    # Add these stats queries
    from datetime import date
    from sqlalchemy import func
    
    today_date = date.today().strftime("%B %d, %Y")
    total_records = PaymentRecord.query.count()
    today_records = PaymentRecord.query.filter(func.date(PaymentRecord.created_at) == date.today()).count()
    
    # Count records with proofs
    records_with_proofs = db.session.query(PaymentRecord.id)\
        .join(PaymentProof, PaymentRecord.id == PaymentProof.payment_id)\
        .group_by(PaymentRecord.id).count()
    
    # Count pending disputes
    pending_disputes = Dispute.query.filter_by(status='pending').count()
    
    return render_template('team_leader/data_entry.html',
                          form=form,
                          recent_entries=recent_entries,
                          today_date=today_date,
                          total_records=total_records,
                          today_records=today_records,
                          records_with_proofs=records_with_proofs,
                          pending_disputes=pending_disputes)

@bp.route('/dispute-validation', methods=['GET', 'POST'])
@login_required
def dispute_validation():
    if current_user.role != 'team_leader':
        flash('Access denied: Team Leader role required', 'danger')
        return redirect(url_for('main.index'))
    
    # Load disputes with their payment records in one query to avoid N+1 queries
    disputes = Dispute.query.filter_by(status='pending')\
        .join(PaymentRecord, Dispute.entry_id == PaymentRecord.id)\
        .options(joinedload(Dispute.payment_record))\
        .order_by(Dispute.created_at.desc())\
        .all()
    
    # Handle form submission if this is a POST request
    if request.method == 'POST':
        dispute_id = request.form.get('dispute_id')
        action = request.form.get('action')
        comments = request.form.get('comments', '')
        
        dispute = Dispute.query.get_or_404(dispute_id)
        
        try:
            if action == 'approve':
                # Change status to pending_da_review instead of approved
                dispute.status = 'pending_da_review'
                dispute.validated_by = current_user.username
                dispute.validation_comments = comments
                dispute.validated_at = datetime.utcnow()
                flash('Dispute approved and sent to Data Analysts for final verification', 'success')
            elif action == 'reject':
                dispute.status = 'rejected'
                dispute.validated_by = current_user.username
                dispute.validation_comments = comments
                dispute.validated_at = datetime.utcnow()
                flash('Dispute rejected', 'warning')
            
            db.session.commit()
            return redirect(url_for('team_leader.dispute_validation'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing dispute: {str(e)}', 'danger')
    
    return render_template('team_leader/dispute_validation.html', disputes=disputes)

@bp.route('/create-dispute', methods=['POST'])
@login_required
def create_dispute():
    if current_user.role != 'team_leader':
        return {'success': False, 'message': 'Access denied'}, 403
    
    entry_id = request.form.get('entry_id')
    reason = request.form.get('reason')
    corrected_details = request.form.get('corrected_details')
    
    entry = PaymentRecord.query.get_or_404(entry_id)
    
    try:
        new_dispute = Dispute(
            entry_id=entry_id,
            reason=reason,
            corrected_details=corrected_details,
            status='pending',
            created_by=current_user.username
        )
        db.session.add(new_dispute)
        db.session.commit()
        flash('Dispute created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating dispute: {str(e)}', 'danger')
    
    return redirect(url_for('team_leader.data_entry'))

@bp.route('/validate-dispute', methods=['POST'])
@login_required
def validate_dispute():
    if current_user.role != 'team_leader':
        flash('Access denied: Team Leader role required', 'danger')
        return redirect(url_for('main.index'))
        
    dispute_id = request.form.get('dispute_id')
    action = request.form.get('action')
    comments = request.form.get('comments', '')
    
    dispute = Dispute.query.get_or_404(dispute_id)
    
    try:
        if action == 'approve':
            dispute.status = 'approved'
            dispute.validated_by = current_user.username
            dispute.validation_comments = comments
            dispute.validated_at = datetime.utcnow()
            flash('Dispute approved successfully', 'success')
        elif action == 'reject':
            dispute.status = 'rejected'
            dispute.validated_by = current_user.username
            dispute.validation_comments = comments
            dispute.validated_at = datetime.utcnow()
            flash('Dispute rejected', 'warning')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing dispute: {str(e)}', 'danger')
        
    return redirect(url_for('team_leader.dispute_validation'))

@bp.route('/search', methods=['GET', 'POST'])
@login_required
def search_records():
    if current_user.role != 'team_leader':
        flash('Access denied: Team Leader role required', 'danger')
        return redirect(url_for('auth.login'))
        
    search_form = PaymentRecordSearchForm()
    
    # Get all unique campaigns for the dropdown
    campaigns = db.session.query(PaymentRecord.campaign).distinct().all()
    search_form.campaign.choices = [('', 'All Campaigns')] + [(c[0], c[0]) for c in campaigns if c[0]]
    
    # Build the base query - USE CLASS ATTRIBUTE NOT STRING
    query = PaymentRecord.query.options(joinedload(PaymentRecord.proofs))
    
    # Apply filters if form is submitted or GET parameters exist
    if search_form.validate_on_submit() or request.args:
        # Get filter data from form or request args
        if request.method == 'POST':
            campaign = search_form.campaign.data
            operator_name = search_form.operator_name.data
            loan_id = search_form.loan_id.data
            customer_name = search_form.customer_name.data
            date_from = search_form.date_from.data
            date_to = search_form.date_to.data
        else:
            campaign = request.args.get('campaign', '')
            operator_name = request.args.get('operator_name', '')
            loan_id = request.args.get('loan_id', '')
            customer_name = request.args.get('customer_name', '')
            
            # Convert string dates to date objects
            date_from = request.args.get('date_from', '')
            if date_from:
                try:
                    date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                except ValueError:
                    date_from = None
            else:
                date_from = None
                
            date_to = request.args.get('date_to', '')
            if date_to:
                try:
                    date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                except ValueError:
                    date_to = None
            else:
                date_to = None
            
            # Update form with GET parameters
            search_form.campaign.data = campaign
            search_form.operator_name.data = operator_name
            search_form.loan_id.data = loan_id
            search_form.customer_name.data = customer_name
            search_form.date_from.data = date_from
            search_form.date_to.data = date_to
        
        # Apply filters
        if campaign:
            query = query.filter(PaymentRecord.campaign == campaign)
        if operator_name:
            query = query.filter(PaymentRecord.operator_name.ilike(f'%{operator_name}%'))
        if loan_id:
            query = query.filter(PaymentRecord.loan_id.ilike(f'%{loan_id}%'))
        if customer_name:
            query = query.filter(PaymentRecord.customer_name.ilike(f'%{customer_name}%'))
        if date_from:
            query = query.filter(PaymentRecord.date_paid >= date_from)
        if date_to:
            query = query.filter(PaymentRecord.date_paid <= date_to)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.order_by(PaymentRecord.created_at.desc()).paginate(page=page, per_page=per_page)
    records = pagination.items
    
    # Get unique operator names for autocomplete
    operators = db.session.query(PaymentRecord.operator_name).distinct().all()
    operator_names = [op[0] for op in operators if op[0]]
    
    return render_template(
        'team_leader/search_records.html',
        search_form=search_form,
        records=records,
        pagination=pagination,
        operators=operator_names
    )

@bp.route('/view-proof/<int:proof_id>')
@login_required
def view_proof(proof_id):
    # Allow both team leaders and data analysts to view proofs
    if current_user.role not in ['team_leader', 'data_analyst']:
        flash('Access denied', 'danger')
        return redirect(url_for('auth.login'))
        
    proof = PaymentProof.query.get_or_404(proof_id)
    
    if not proof.file_path:
        flash('No proof image available for this record', 'warning')
        return redirect(url_for('team_leader.data_entry'))
    
    # Extract directory and filename from the stored path
    directory = os.path.dirname(os.path.join(current_app.root_path, '..', proof.file_path))
    filename = os.path.basename(proof.file_path)
    
    return send_from_directory(directory, filename)

@bp.route('/record-proofs/<int:record_id>')
@login_required
def record_proofs(record_id):
    # Allow both team leaders and data analysts to view proofs
    if current_user.role not in ['team_leader', 'data_analyst']:
        flash('Access denied', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get the source parameter (defaults to data_entry for team leaders)
    source = request.args.get('source', 'data_entry')
    
    payment = PaymentRecord.query.get_or_404(record_id)
    proofs = PaymentProof.query.filter_by(payment_id=record_id).all()
    
    return render_template('team_leader/view_proofs.html', payment=payment, proofs=proofs, source=source)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, FloatField, DateField, TextAreaField, BooleanField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from flask_wtf.file import FileField, FileAllowed, MultipleFileField

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('team_leader', 'Team Leader'), ('data_analyst', 'Data Analyst')], validators=[DataRequired()])
    submit = SubmitField('Login')

class PaymentEntryForm(FlaskForm):
    campaign = SelectField('Campaign', choices=[
        ('LANDERS', 'LANDERS'),
        ('MPL', 'MPL'),
        ('MAYA CREDIT', 'MAYA CREDIT'),
        ('TALA', 'TALA'),
        ('OLP', 'OLP'),
        ('KVIKU', 'KVIKU'),
        ('SKYRO', 'SKYRO')
    ], validators=[DataRequired()])
    dpd = IntegerField('DPD (Days Past Due)', validators=[DataRequired()])
    loan_id = StringField('Loan ID', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    date_paid = DateField('Date Paid', validators=[DataRequired()])
    operator_name = StringField('Operator Name', validators=[DataRequired()])
    customer_name = StringField('Customer Name', validators=[DataRequired()])
    
    # Change to MultipleFileField for multiple file uploads
    proof_images = MultipleFileField('Proof of Payment', validators=[
        DataRequired(message='At least one proof of payment is required'),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Only images (jpg, jpeg, png) and PDF files allowed!')
    ])
    
    proof_types = SelectField('Proof Type', choices=[
        ('receipt', 'Payment Receipt'),
        ('screenshot', 'Screenshot'),
        ('email', 'Email Confirmation'),
        ('message', 'Message/SMS'),
        ('other', 'Other')
    ])
    
    submit = SubmitField('Submit')

class DisputeForm(FlaskForm):
    reason = SelectField('Reason for Dispute', choices=[
        ('wrong_operator', 'Wrong Operator'),
        ('wrong_amount', 'Wrong Amount'),
        ('wrong_date', 'Wrong Date'),
        ('duplicate_entry', 'Duplicate Entry'),
        ('other', 'Other'),
    ], validators=[DataRequired()])
    corrected_details = TextAreaField('Corrected Details', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit Dispute')

class DisputeValidationForm(FlaskForm):
    dispute_id = IntegerField('Dispute ID', validators=[DataRequired()])
    action = StringField('Action', validators=[DataRequired()])  # 'approve' or 'reject'
    comments = TextAreaField('Comments', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit')

class CampaignFilterForm(FlaskForm):
    campaign = SelectField('Campaign', choices=[], validators=[Optional()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    operator = StringField('Operator', validators=[Optional(), Length(max=80)])
    min_amount = FloatField('Min Amount', validators=[Optional()])
    max_amount = FloatField('Max Amount', validators=[Optional()])
    submit = SubmitField('Apply Filters')

class ExportForm(FlaskForm):
    export_type = RadioField('Export Type', choices=[('campaign', 'By Campaign'), ('disputes', 'Validated Disputes')], default='campaign', validators=[DataRequired()])
    campaign = SelectField('Campaign', choices=[], validators=[Optional()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    include_headers = BooleanField('Include Headers', default=True)
    submit = SubmitField('Export')

class PaymentRecordSearchForm(FlaskForm):
    campaign = SelectField('Campaign', choices=[], validators=[Optional()])
    operator_name = StringField('Operator Name', validators=[Optional()])
    loan_id = StringField('Loan ID', validators=[Optional()])
    customer_name = StringField('Customer Name', validators=[Optional()])
    date_from = DateField('Date From', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateField('Date To', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Search')

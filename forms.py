from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms import DecimalField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from wtforms.fields import DateTimeLocalField, DateField

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    currency = SelectField('Preferred Currency', choices=[
        ('USD', 'USD ($) - US Dollar'),
        ('EUR', 'EUR (€) - Euro'),
        ('GBP', 'GBP (£) - British Pound'),
        ('INR', 'INR (₹) - Indian Rupee'),
        ('JPY', 'JPY (¥) - Japanese Yen'),
        ('AUD', 'AUD ($) - Australian Dollar'),
        ('CAD', 'CAD ($) - Canadian Dollar'),
        ('CNY', 'CNY (¥) - Chinese Yuan')
    ], default='USD')
    submit = SubmitField('Register')


class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    
    deadline = DateTimeLocalField(
        'Deadline',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()]
    )

    priority = SelectField('Priority', choices=[('Low','Low'), ('Medium','Medium'), ('High','High')], default='Medium')

    tags = StringField('Tags (comma-separated)', validators=[Length(max=200)])

    submit = SubmitField('Save Task')


class BudgetForm(FlaskForm):
    category = SelectField(
        'Category',
        choices=[
            ('Grocery','Grocery'),
            ('Bills','Bills'),
            ('Transport','Transport'),
            ('Entertainment','Entertainment'),
            ('Salary','Salary'),
            ('Other','Other')
        ],
        validators=[DataRequired()]
    )

    amount = DecimalField('Amount', places=2, validators=[DataRequired(), NumberRange(min=0.01, max=999999999.99)])
    type = SelectField('Type', choices=[('expense', 'Expense'), ('income', 'Income')], validators=[DataRequired()])

    date = DateField('Date', format='%Y-%m-%d')

    submit = SubmitField('Add Transaction')

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
    currency = SelectField('Preferred Currency', choices=[('USD','USD ($)'), ('INR','INR (₹)')], default='USD')
    submit = SubmitField('Register')


class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    
    deadline = DateTimeLocalField(
        'Deadline',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()]
    )

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

    amount = DecimalField('Amount', places=2, validators=[DataRequired(), NumberRange(min=0)])
    type = SelectField('Type', choices=[('expense', 'Expense'), ('income', 'Income')], validators=[DataRequired()])

    date = DateField('Date', format='%Y-%m-%d')  # NOW PROPER DATE FIELD

    submit = SubmitField('Add Transaction')

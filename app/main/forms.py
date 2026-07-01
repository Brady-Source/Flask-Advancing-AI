from flask_wtf import FlaskForm
from wtforms import StringField , IntegerField, SubmitField, PasswordField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Regexp, Email, EqualTo, ValidationError
from ..models import User, Role
from flask_pagedown.fields import PageDownField

class NameForm(FlaskForm):
    name = StringField('What is your name?',validators= [DataRequired()])
    submit = SubmitField('Submit')
        
class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[DataRequired(), Length(0, 64)])
    username = StringField('Username', validators=[DataRequired(), Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me (2000 character max)', validators=[Length(0, 2000)])
    age = StringField('Age', validators=[Length(0, 64)])
    submit = SubmitField('Submit')
    
class EditProfileAdminForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[DataRequired(), Length(1, 64), Email()]
    )
    username = StringField(
        'Username',
        validators=[
            DataRequired(), Length(1, 64),
            Regexp(
                '^[A-Za-z][A-Za-z0-9_.]*$', 0,
                'Usernames must have only letters, numbers, dots or underscores'
            )
        ]
    )
    confirmed = BooleanField('Confirmed')
    role_id = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me', validators=[Length(0, 2000)])
    submit = SubmitField('Submit')
    age = IntegerField('age', validators=[Length(0, 64)])

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role_id.choices = [
            (role.id, role.name)
            for role in Role.query.order_by(Role.name).all()
        ]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')
        
class PostForm(FlaskForm):
    subject = StringField("What's on your mind?", validators=[DataRequired()])
    body_format = SelectField(
        'Format',
        choices=[('plain', 'Plain Text'), ('markdown', 'Markdown'), ('html', 'HTML')],
        default='plain'
    )
    body = PageDownField("Body", validators=[DataRequired()])
    tags = StringField('Tags (comma or # separated)', validators=[Length(0, 140)])
    submit = SubmitField('Submit')

    def validate_tags(self, field):
        if not field.data:
            return
        raw = field.data.replace('#', ' ')
        parts = [p.strip() for p in raw.replace(';', ',').split(',')]
        tags = [p for p in parts if p]
        field.data = ', '.join(tags)
    
class CommentForm(FlaskForm):
    body_format = SelectField(
        'Format',
        choices=[('plain', 'Plain Text'), ('html', 'HTML')],
        default='plain'
    )
    body = TextAreaField('Comment', validators=[DataRequired(), Length(1, 1000)])
    submit = SubmitField('Submit')
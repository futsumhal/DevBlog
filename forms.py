from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, URL
from flask_ckeditor import CKEditorField


##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    tags = StringField("Tags (comma separated)")
    categories = StringField("Categories (comma separated)")
    status = SelectField(
        "Status",
        choices=[("draft", "Draft"), ("published", "Published")],
        default="published",
    )
    submit = SubmitField("Submit Post")


class CreatecommentForm(FlaskForm):
    body = TextAreaField("Share Your Feedback", validators=[DataRequired(), Length(min=2, max=1000)])
    parent_id = HiddenField("Parent ID")
    submit = SubmitField("Submit Comment")

class RegisterForm(FlaskForm):

    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=100)])
    # confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class Loginform(FlaskForm):
    email=StringField('Email',validators=[DataRequired(), Email()])
    password=PasswordField('Password',validators=[DataRequired()])
    submit=SubmitField("Let me in")
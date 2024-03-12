from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, validators


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        [
            validators.DataRequired("Email krävs"),
            validators.Email(),
            validators.Length(max=50),
        ],
    )
    password = PasswordField(
        "Lösenord",
        [validators.DataRequired("Lösenord krävs"), validators.Length(max=250)],
    )


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(
        "Nuvarande lösenord",
        validators=[
            validators.DataRequired("Nuvarande lösenord krävs"),
            validators.Length(max=250),
        ],
    )
    new_password = PasswordField(
        "Nytt lösenord",
        [
            validators.DataRequired("Nytt Lösenord krävs"),
            validators.Length(max=250),
            validators.EqualTo("password_confirm", message="Lösenorden måste matcha."),
        ],
    )
    password_confirm = PasswordField(
        "Bekräfta nytt lösenord", validators=[validators.Length(max=250)]
    )

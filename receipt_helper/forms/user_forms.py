from flask_wtf import FlaskForm
from wtforms import StringField, validators
from flask_wtf.file import FileField, FileRequired, FileAllowed


class AddSingleUserForm(FlaskForm):
    name = StringField(
        "Namn",
        [
            validators.DataRequired("Namn krävs"),
            validators.Length(max=100),
        ],
    )
    email = StringField(
        "Email",
        [
            validators.DataRequired("Email krävs"),
            validators.Email("Måste vara en giltig Email"),
            validators.Length(max=100),
        ],
    )


class AddManyUsersForm(FlaskForm):
    file = FileField(
        "CSV-Fil",
        validators=[
            FileRequired("Fil krävs"),
            FileAllowed(
                ["csv"],
                "Endast csv är tilåtet!",
            ),
        ],
    )

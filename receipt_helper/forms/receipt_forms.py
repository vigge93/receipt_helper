from flask_wtf import FlaskForm
from wtforms import StringField, validators, DateField, DecimalField, BooleanField
from flask_wtf.file import FileField, FileRequired, FileAllowed


class SubmitReceiptForm(FlaskForm):
    receipt_date = DateField(
        "Datum på kvittot",
        [validators.DataRequired("Kvittodatum krävs")],
    )
    body = StringField(
        "Sektion/Utbildningsförening",
        [
            validators.DataRequired("Sektion/utbildningsförening krävs"),
            validators.Length(max=50),
        ],
    )
    activity = StringField(
        "Aktivitet",
        [validators.DataRequired("Aktivitet krävs"), validators.Length(max=250)],
    )
    amount = DecimalField(
        "Summa (SEK)", [validators.data_required("Summa krävs")], places=2
    )
    file = FileField(
        "Fil",
        validators=[
            FileRequired("Fil krävs"),
            FileAllowed(
                ["png", "jpeg", "jpg", "gif", "tiff", "raw", "svg", "webp", "pdf"],
                "Endast bild/pdf är tilåtet!",
            ),
        ],
    )
    external = BooleanField("Betalt med privat kort")

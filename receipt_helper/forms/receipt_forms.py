from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import DateField, DecimalField, StringField, validators


class SubmitReceiptForm(FlaskForm):
    receipt_date = DateField(
        "Datum på kvittot",
        [validators.DataRequired("Kvittodatum krävs")],
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


class RejectReceiptForm(FlaskForm):
    reason = StringField(
        "Anledning",
        [validators.data_required("Anledning krävs"), validators.Length(max=250)],
    )

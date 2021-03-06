from flask_wtf import FlaskForm
from wtforms.validators import Required, Length
from wtforms.fields import StringField

from atst.forms.validators import Number
from atst.utils.localization import translate


class CCPOUserForm(FlaskForm):
    dod_id = StringField(
        translate("forms.new_member.dod_id_label"),
        validators=[Required(), Length(min=10, max=10), Number()],
    )

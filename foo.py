from atst.domain.authnid.crl.loader import Loader
from atst.app import make_config, make_app
from atst.database import db
from atst.models import *

app = make_app(make_config())
ctx = app.app_context()
ctx.push()

lod = Loader("crls")

lod.load()

from flask import Flask
from flaskext.auth import Auth
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.secret_key = 'aequaiK7coTh1Oepahb7aeNgiaph3OhGIethu9keeeRae1ahieM0tu5oaekeer6S'

Auth(app)
Bootstrap(app)

def set_db(name):
    from formgear import mongo
    mongo.db = mongo.connection[name]

app.before_first_request(lambda:set_db('ikari'))

from flask import Blueprint
from pkg_resources import resource_filename
fg = Blueprint('formgear', __name__,
                template_folder=resource_filename('formgear', 'templates'))
app.register_blueprint(fg)

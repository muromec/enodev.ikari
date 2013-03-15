from flask import Flask
from flask.ext.hopak import Admin
from hopak.ds.mongo import MongoDS
from flask.ext.pymongo import PyMongo
from flaskext.auth import Auth
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.secret_key = 'aequaiK7coTh1Oepahb7aeNgiaph3OhGIethu9keeeRae1ahieM0tu5oaekeer6S'

Auth(app)
Bootstrap(app)

mongo = PyMongo(app)

admin = Admin(url='/hopak')
admin.init_app(app, MongoDS(mongo))

from flask import Blueprint
from pkg_resources import resource_filename
fg = Blueprint('hopak', __name__,
                template_folder=resource_filename('hopak', 'templates'))
app.register_blueprint(fg)

from flaskext import redtask as task
app.register_blueprint(task.app)

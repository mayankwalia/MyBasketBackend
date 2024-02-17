from flask import Flask
from flask_restful import Api
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

app = Flask(__name__, template_folder='templates')
db = SQLAlchemy()
api = Api()
mail = Mail()
cache = Cache()
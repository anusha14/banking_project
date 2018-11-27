from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

from banking_system import models
from banking_system import views

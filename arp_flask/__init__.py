from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
db = SQLAlchemy(app)

app.config['SECRET_KEY']='NotMyPassword'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/database.db'


bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'holacuentame2021@gmail.com'
app.config['MAIL_PASSWORD'] = '@Rp596693'

mail=Mail(app)

from arp_flask import routes
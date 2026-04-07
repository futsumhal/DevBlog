from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
ckeditor = CKEditor()
migrate = Migrate()

from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os
from pathlib import Path
from routes.common_routes import common_bp
from routes.admin_routes import admin_bp
from routes.student_routes import student_bp
from routes.teacher_routes import teacher_bp
from routes.org_user_routes import org_user_bp
from extensions import db, login_manager

# Load environment variables
dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

app = Flask(__name__)
CORS(app)

# Define and register the `has_role` filter
def has_role(user, role_name):
    return any(role.name == role_name for role in user.roles)

app.jinja_env.filters['has_role'] = has_role

# Configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx', 'txt'}


app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


# Register Blueprints
app.register_blueprint(common_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(org_user_bp, url_prefix='/org_user')


# Import extensions
from extensions import db, bcrypt, login_manager
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Setup migration
migrate = Migrate(app, db)

# Import models and routes
from models import *
from routes import *

# Setup user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Initialize SQLAlchemy first - without binding to an app
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'PASSWORD'  # Change this in production
    
    # Use absolute path to ensure SQLite can find the database location
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(os.path.dirname(basedir), 'instance', 'collections.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes import auth, team_leader, data_analyst
    app.register_blueprint(auth.bp)
    app.register_blueprint(team_leader.bp)
    app.register_blueprint(data_analyst.bp)

    return app
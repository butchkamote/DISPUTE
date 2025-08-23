from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os

app = create_app()

# Create a context to work with the app
with app.app_context():
    # Make sure the instance folder exists
    os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)
    
    # Create all tables
    db.create_all()
    
    # Check if we need to create initial users
    if not User.query.filter_by(username='teamleader').first():
        # Create a team leader user
        tl_user = User(
            username='teamleader',
            password=generate_password_hash('password123'),
            role='team_leader'
        )
        
        # Create a data analyst user
        da_user = User(
            username='analyst',
            password=generate_password_hash('password123'),
            role='data_analyst'
        )
        
        # Add users to database
        db.session.add(tl_user)
        db.session.add(da_user)
        db.session.commit()
        
        print("Created initial users:")
        print("Team Leader - username: teamleader, password: password123")
        print("Data Analyst - username: analyst, password: password123")

if __name__ == '__main__':
    app.run(debug=True)
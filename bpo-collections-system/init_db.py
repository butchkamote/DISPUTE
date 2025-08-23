from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

print("Creating database...")
app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print("Database tables created at:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    # Create test users
    if not User.query.first():
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
    
    print("Database initialization complete!")
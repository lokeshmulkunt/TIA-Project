from webapp import app, db

# This creates the application context
with app.app_context():
    # This creates the database tables based on your models
    db.create_all()

print("Database created successfully!")
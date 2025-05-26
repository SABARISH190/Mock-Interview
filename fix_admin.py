from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Find the admin user (ID 3 from the logs)
    admin_user = User.query.get(3)
    
    if admin_user:
        print(f"Before update - Username: {admin_user.username}, Is Admin: {admin_user.is_admin}")
        
        # Update admin status
        admin_user.is_admin = True
        db.session.commit()
        
        # Verify the update
        updated_user = User.query.get(3)
        print(f"After update - Username: {updated_user.username}, Is Admin: {updated_user.is_admin}")
        print("Admin privileges have been granted!")
    else:
        print("Admin user not found. Please check the database.")

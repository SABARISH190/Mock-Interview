from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Get all admin users
    admin_users = User.query.filter_by(is_admin=True).all()
    
    if not admin_users:
        print("No admin users found in the database!")
    else:
        print("Admin users found:")
        for user in admin_users:
            print(f"\nID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Is Admin: {user.is_admin}")
            print(f"Is Verified: {user.is_verified}")
            print(f"Is Active: {user.is_active}")
    
    # Check if current user is admin
    test_user = User.query.get(3)  # From your logs, user ID 3 was being checked
    if test_user:
        print(f"\nChecking user with ID 3:")
        print(f"Username: {test_user.username}")
        print(f"Is Admin: {test_user.is_admin}")
        print(f"Is Verified: {test_user.is_verified}")
        print(f"Is Active: {test_user.is_active}")
    else:
        print("\nUser with ID 3 not found")

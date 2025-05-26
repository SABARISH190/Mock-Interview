import os
from app import create_app, db

app = create_app()

# Log database connection info
with app.app_context():
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    # Mask password in logs
    if 'postgresql' in db_url:
        parts = db_url.split('@')
        if len(parts) > 1:
            db_url = 'postgresql://user:****@' + parts[1]
    print(f"\n=== Using Database: {db_url} ===\n")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)

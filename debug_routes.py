from app import create_app

app = create_app()

# Print all routes
print("\nRegistered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule} -> {rule.methods}")
    
# Test admin dashboard URL
with app.test_request_context():
    print("\nAdmin dashboard URL:", url_for('admin.dashboard'))
    print("Main dashboard URL:", url_for('main.dashboard'))

import os
import re

# Directory containing templates
templates_dir = os.path.join('app', 'templates')

# Pattern to match {{ csrf_token() }}
pattern = r'\{\{\s*csrf_token\(\)\s*\}\}'
replacement = '{{ csrf_token }}'

def update_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all occurrences of the pattern
    updated_content = re.sub(pattern, replacement, content)
    
    # Write back only if changes were made
    if updated_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Updated: {file_path}")

def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                update_file(file_path)

if __name__ == '__main__':
    print("Updating CSRF tokens in templates...")
    process_directory(templates_dir)
    print("Done!")

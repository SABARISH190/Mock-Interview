import os
import re
from pathlib import Path

def update_template(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already updated
    if 'page-container' in content:
        return False
    
    # Find the content block
    content_block = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock\s*%\}', 
                            content, re.DOTALL)
    
    if not content_block:
        return False
    
    # Get the content inside the block
    block_content = content_block.group(1).strip()
    
    # Skip if it's already wrapped in a container
    if block_content.strip().startswith('<div class="page-container">'):
        return False
    
    # Wrap the content in a container
    new_block = '{% block content %}\n    <div class="page-container">\n        ' + '\n        '.join(block_content.split('\n')) + '\n    </div>\n{% endblock %}'
    
    # Replace the old block with the new one
    new_content = content[:content_block.start()] + new_block + content[content_block.end():]
    
    # Remove any duplicate content blocks that might have been created
    new_content = re.sub(r'\{%\s*block\s+content\s*%\}.*?\{%\s*endblock\s*%\}', 
                        '', 
                        new_content, 
                        flags=re.DOTALL)
    
    # Add the new content block
    new_content = re.sub(r'(\{%\s*extends[^%]+%\}.*?)(\n\s*\{%\s*block\s+content\s*%\})', 
                        f'\\1\n{{% block content %}}\n    <div class="page-container">\n        {block_content}\n    </div>\n{{% endblock %}}', 
                        new_content, 
                        flags=re.DOTALL)
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    templates_dir = Path('app/templates')
    updated_count = 0
    
    # Skip these directories and files
    skip_dirs = {'static', 'email', 'errors', 'admin', 'auth'}
    skip_files = {'base.html', 'dashboard/dashboard.html'}
    
    for root, _, files in os.walk(templates_dir):
        # Skip directories in skip_dirs
        if any(skip_dir in root for skip_dir in skip_dirs):
            continue
            
        for file in files:
            if file.endswith('.html') and file not in skip_files:
                file_path = os.path.join(root, file)
                if update_template(file_path):
                    print(f'Updated: {file_path}')
                    updated_count += 1
    
    print(f'\nUpdated {updated_count} template(s).')

if __name__ == '__main__':
    main()

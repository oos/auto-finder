#!/usr/bin/env python3
"""
Script to fix JWT identity handling in all route files
"""

import os
import re

def fix_jwt_identity_in_file(file_path):
    """Fix JWT identity handling in a single file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match get_jwt_identity() calls that aren't already fixed
    pattern = r'(\s+)(user_id = get_jwt_identity\(\))(\s*\n)(\s+)(user = User\.query\.get\(user_id\))'
    replacement = r'\1\2\3\4# Convert string user_id to int for database query\n\4user_id = int(user_id) if user_id else None\n\4\5'
    
    # Apply the fix
    new_content = re.sub(pattern, replacement, content)
    
    # Also fix cases where get_jwt_identity() is used but not followed by User.query.get
    pattern2 = r'(\s+)(user_id = get_jwt_identity\(\))(\s*\n)(\s+)([^#].*user_id.*)'
    replacement2 = r'\1\2\3\4# Convert string user_id to int for database query\n\4user_id = int(user_id) if user_id else None\n\4\5'
    
    new_content = re.sub(pattern2, replacement2, new_content)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"✓ Fixed {file_path}")
        return True
    else:
        print(f"- No changes needed in {file_path}")
        return False

def main():
    """Fix all route files"""
    routes_dir = "routes"
    fixed_files = []
    
    for filename in os.listdir(routes_dir):
        if filename.endswith('.py'):
            file_path = os.path.join(routes_dir, filename)
            if fix_jwt_identity_in_file(file_path):
                fixed_files.append(file_path)
    
    print(f"\nFixed {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main()

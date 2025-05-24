"""
Template syntax checker and fixer for LightYearAI
"""
import os
import sys
import argparse
import shutil
import importlib.util
from pathlib import Path
import jinja2

def validate_template(template_path):
    """Validate a Jinja2 template file"""
    try:
        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)
        
        # First, do a simple syntax check without rendering
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        
        # Just checking syntax is usually enough to detect most issues
        return True, "Template syntax is valid (basic validation passed)"
            
    except Exception as e:
        return False, str(e)

def fix_template(template_path, fixed_template_path=None):
    """Fix template by replacing with a known good version or cleaning up tags"""
    
    # If a fixed template is provided, use it as a replacement
    if fixed_template_path and os.path.exists(fixed_template_path):
        print(f"Using fixed template from {fixed_template_path}")
        # Backup the original
        backup_path = template_path + ".backup"
        shutil.copy2(template_path, backup_path)
        print(f"Original template backed up to {backup_path}")
        
        # Replace with fixed version
        shutil.copy2(fixed_template_path, template_path)
        print(f"Replaced {template_path} with fixed version")
        return True
    
    # Otherwise, try to fix the template by parsing and cleaning up the content
    print("No fixed template provided, attempting to fix manually")
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count blocks and endblocks
        block_count = content.count("{% block ")
        endblock_count = content.count("{% endblock %}")
        
        print(f"Found {block_count} block tags and {endblock_count} endblock tags")
        
        if endblock_count > block_count:
            print(f"Too many endblock tags ({endblock_count}) compared to block tags ({block_count})")
            
            # Backup the original
            backup_path = template_path + ".backup"
            shutil.copy2(template_path, backup_path)
            print(f"Original template backed up to {backup_path}")
            
            # Check for certain patterns and fix them
            lines = content.split("\n")
            fixed_lines = []
            in_additional_styles = False
            fixed = False
            
            for line in lines:
                if "{% block additional_styles %}" in line:
                    in_additional_styles = True
                    fixed_lines.append(line)
                elif "{% endblock %}" in line and in_additional_styles and not fixed:
                    in_additional_styles = False
                    fixed_lines.append(line)
                    fixed = True
                elif "{% block content %}" in line:
                    fixed_lines.append(line)
                elif "{% endblock %}" in line and not in_additional_styles and fixed:
                    # Skip extra endblocks between additional_styles and content
                    continue
                else:
                    fixed_lines.append(line)
            
            # Write the fixed content
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(fixed_lines))
            
            print("Fixed template by removing extra endblock tags")
            return True
        else:
            print("No obvious issues to fix")
            return False
    
    except Exception as e:
        print(f"Error trying to fix template: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Check and fix Jinja2 template syntax')
    parser.add_argument('--check', action='store_true', help='Only check template without fixing')
    parser.add_argument('--template', default='templates/index.html', help='Path to template to check/fix')
    parser.add_argument('--fixed', default='templates/index_fixed.html', help='Path to fixed template to use')
    
    args = parser.parse_args()
    
    template_path = args.template
    fixed_template_path = args.fixed
    
    if not os.path.exists(template_path):
        print(f"Template file not found: {template_path}")
        return 1
    
    valid, message = validate_template(template_path)
    
    if valid:
        print(f"✅ {template_path} - {message}")
        return 0
    else:
        print(f"❌ {template_path} - {message}")
        
        if args.check:
            return 1
        
        fixed = fix_template(template_path, fixed_template_path if os.path.exists(fixed_template_path) else None)
        
        if fixed:
            valid, message = validate_template(template_path)
            if valid:
                print(f"✅ Template fixed successfully: {message}")
                return 0
            else:
                print(f"❌ Template still has issues after fix: {message}")
                return 1
        else:
            print("Could not fix template")
            return 1

if __name__ == "__main__":
    sys.exit(main())

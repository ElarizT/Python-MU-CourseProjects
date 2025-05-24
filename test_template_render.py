"""
Test the full render of templates to catch any issues before deployment
"""
import os
import sys
from flask import Flask, render_template, g
import jinja2

# Create a minimal Flask app for testing
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Set up a minimal context for templates
@app.context_processor
def inject_globals():
    return {
        'g': g
    }

@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.now()}

def test_template(template_name):
    """Test render a template to catch any issues"""
    try:
        with app.test_request_context(), app.app_context():
            # Set up g to avoid AttributeError
            g.user_name = None
            g.user_picture = None
            g.available_languages = {"en": "English", "es": "Spanish", "fr": "French"}
            g.user_language = "en"
            g.user_id = None
            g.is_authenticated = False
            g.is_admin = False
            g.subscription_tier = "free"
            
            rendered = render_template(template_name)
            return True, f"Template {template_name} renders successfully"
    except Exception as e:
        return False, f"Error rendering {template_name}: {str(e)}"

def main():
    print("Testing template rendering...")
    
    # Focus on index.html first
    index_result, index_message = test_template('index.html')
    if index_result:
        print(f"✅ {index_message}")
    else:
        print(f"❌ {index_message}")
        return 1
    
    # Test other important templates
    templates_to_test = ['layout.html']
    
    all_success = True
    for template in templates_to_test:
        success, message = test_template(template)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            all_success = False
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())

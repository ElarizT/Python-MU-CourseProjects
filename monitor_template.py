"""
Template Monitor - A utility to check if the landing page template is working correctly
"""
import os
import sys
import argparse
import requests
import re
from urllib.parse import urlparse

def check_template(url):
    """
    Check if a template is rendering correctly by making a request and
    checking for specific patterns that indicate proper rendering
    """
    if not url:
        print("Error: No URL provided")
        return False, "No URL provided"
    
    # Add scheme if not present
    if not urlparse(url).scheme:
        url = f"http://{url}"
    
    # Fix localhost URL format
    if "localhost" in url and not (url.startswith("http://") or url.startswith("https://")):
        url = f"http://{url}"
    
    try:
        print(f"Checking template at {url}...")
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return False, f"HTTP error: {response.status_code}"
            
        content = response.text
        
        # Check for signs of Jinja error
        if "jinja2.exceptions" in content or "TemplateSyntaxError" in content:
            return False, "Template syntax error detected in response"
            
        # Check for some expected content from the template
        if "Meet LightYearAI" not in content:
            return False, "Expected content 'Meet LightYearAI' not found"
            
        # Check for sign that CSS loaded correctly
        if "landing-page.css" not in content:
            return False, "CSS file reference not found in HTML"
            
        # Check for other important elements
        elements_to_check = [
            "hero-buttons",
            "feature-card",
            "btn-primary-gradient"
        ]
        
        missing_elements = [elem for elem in elements_to_check if elem not in content]
        if missing_elements:
            return False, f"Missing expected elements: {', '.join(missing_elements)}"

        # If all checks pass        
        return True, "Template appears to be rendering correctly"
        
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Check if a template is rendering correctly')
    parser.add_argument('--url', default='localhost:5000', help='URL to check')
    parser.add_argument('--retry', type=int, default=1, help='Number of times to retry if check fails')
    parser.add_argument('--wait', type=int, default=5, help='Seconds to wait between retries')
    
    args = parser.parse_args()
    
    # Initial check
    success, message = check_template(args.url)
    
    if success:
        print(f"✅ {message}")
        return 0
    else:
        print(f"❌ {message}")
        
        # Retry logic
        if args.retry > 0:
            import time
            for i in range(args.retry):
                print(f"Retrying in {args.wait} seconds... (Attempt {i+1}/{args.retry})")
                time.sleep(args.wait)
                
                success, message = check_template(args.url)
                if success:
                    print(f"✅ {message}")
                    return 0
                else:
                    print(f"❌ {message}")
            
            print(f"Failed after {args.retry} retries")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())

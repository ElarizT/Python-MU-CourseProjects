#!/bin/bash
# fix_template_syntax.sh - Fixes the index.html template syntax error before starting the app

# Print what we're doing
echo "Checking for template syntax issues..."

# Path to the template file
INDEX_TEMPLATE="templates/index.html"

if [ -f "$INDEX_TEMPLATE" ]; then
    echo "Found $INDEX_TEMPLATE, checking for syntax issues..."
    
    # Check if there are multiple endblock tags without corresponding blocks
    BLOCK_COUNT=$(grep -c "{% block " "$INDEX_TEMPLATE")
    ENDBLOCK_COUNT=$(grep -c "{% endblock %}" "$INDEX_TEMPLATE")
    
    echo "Found $BLOCK_COUNT block tags and $ENDBLOCK_COUNT endblock tags"
    
    if [ "$ENDBLOCK_COUNT" -gt "$BLOCK_COUNT" ]; then
        echo "Template has syntax errors. Fixing..."
        
        # Create a temporary file for safe editing
        TMP_FILE=$(mktemp)
        
        # Fix the template by using awk to properly structure blocks
        awk '
        BEGIN { in_additional_styles = 0; in_content = 0; fixed = 0; }
        
        /{% block additional_styles %}/ { in_additional_styles = 1; print; next; }
        /{% endblock %}/ && in_additional_styles && !fixed { 
            in_additional_styles = 0; 
            print; 
            fixed = 1;
            next; 
        }
        
        /{% block content %}/ { in_content = 1; print; next; }
        
        # Skip any endblock that appears before content block starts
        /{% endblock %}/ && !in_content && fixed { next; }
        
        # This is the final endblock for content
        /{% endblock %}/ && in_content { in_content = 0; print; next; }
        
        # Print all other lines
        { print; }
        ' "$INDEX_TEMPLATE" > "$TMP_FILE"
        
        # Replace the original file
        mv "$TMP_FILE" "$INDEX_TEMPLATE"
        
        echo "Template fixed successfully."
    else
        echo "Template syntax looks good. No changes needed."
    fi
else
    echo "Warning: Could not find $INDEX_TEMPLATE"
fi

echo "Template syntax check completed."

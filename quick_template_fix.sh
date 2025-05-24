#!/bin/bash
# quick_template_fix.sh - Quick fix for index.html template by replacing it with the fixed version

# Print what we're doing
echo "Applying quick fix for index.html template..."

# Paths to the template files
INDEX_TEMPLATE="templates/index.html"
FIXED_TEMPLATE="templates/index_fixed.html"

if [ -f "$FIXED_TEMPLATE" ]; then
    if [ -f "$INDEX_TEMPLATE" ]; then
        # Backup the original file first
        cp "$INDEX_TEMPLATE" "${INDEX_TEMPLATE}.backup"
        echo "Created backup at ${INDEX_TEMPLATE}.backup"
        
        # Replace the original with the fixed version
        cp "$FIXED_TEMPLATE" "$INDEX_TEMPLATE"
        echo "Replaced $INDEX_TEMPLATE with fixed version."
    else
        echo "Warning: Could not find $INDEX_TEMPLATE"
    fi
else
    echo "Error: Fixed template $FIXED_TEMPLATE not found!"
fi

import sys
import os
import json

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from excel_generator import generate_excel_from_prompt

# Load environment variables (if any)
from dotenv import load_dotenv
load_dotenv()

# Configure Gemini model
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

def test_complex_excel_generation():
    """
    Test the enhanced Excel generator with a complex multi-sheet report request
    """
    # The complex Excel request with multiple sheets, tables and charts
    complex_prompt = """
    Create an Excel file with the following specifications:
    - **Sheet 1: 'Sales Report'**
        Columns: 'Product', 'Q1 Sales', 'Q2 Sales', 'Q3 Sales', 'Q4 Sales'
        Data:
        - Product A: 10000, 12000, 11000, 13000
        - Product B: 15000, 16000, 17000, 18000
        - Product C: 20000, 19000, 22000, 21000
        - Product D: 18000, 21000, 20000, 22000
        - Create a **bar chart** comparing sales for each product for Q1 to Q4.

    - **Sheet 2: 'Customer Demographics'**
        Columns: 'Age Group', 'Number of Customers'
        Data:
        - 18-24: 1000
        - 25-34: 2000
        - 35-44: 1500
        - 45-54: 1200
        - 55+: 800
        - Create a **pie chart** to show the distribution of customers by age group.

    - **Sheet 3: 'Revenue Analysis'**
        Columns: 'Year', 'Revenue', 'Cost', 'Profit'
        Data:
        - 2020: 50000, 30000, 20000
        - 2021: 60000, 35000, 25000
        - 2022: 70000, 40000, 30000
        - Create a **line chart** for 'Revenue vs. Cost' over the years.

    - **Save the file as 'company_report_2020-2022.xlsx'** and ensure it contains all sheets and charts.
    """
    
    print("Testing complex Excel generator...")
    print(f"Request: {complex_prompt[:100]}...")
    
    # Generate the Excel file using the enhanced module
    file_path, filename = generate_excel_from_prompt(complex_prompt, model)
    
    print("\nExcel file generated successfully!")
    print(f"File saved at: {file_path}")
    print(f"Filename: {filename}")
    
    return file_path, filename

if __name__ == "__main__":
    test_complex_excel_generation()
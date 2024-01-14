import urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET

def extract_num_values(element):
    num_value = []
    for a in element:
        if a.text and a.text.strip().replace('.','',1).isdigit():
            num_value.append(int(a.text))
        num_value.extend(extract_num_values(a))
    return num_value
    
# Put the xml link
url_xml = 'https://py4e-data.dr-chuck.net/comments_1951523.xml'

# Open the link
with urllib.request.urlopen(url_xml) as response:
    data = response.read()

# Parse the xml data
root = ET.fromstring(data)

# Extract numeric values
values_count = extract_num_values(root)

# Calculate the sum of values
total = sum(values_count)

# Print the result
print(f'Total of values: {total}')

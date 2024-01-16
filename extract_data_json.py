import urllib.request, urllib.parse, urllib.error
import json
import ssl

# Ignire the ssl certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Open and read json data
url = 'http://py4e-data.dr-chuck.net/comments_1951524.json'
response = urllib.request.urlopen(url)
data = json.loads(response.read().decode('utf-8'))

# Find and print the sum of counts in data
sum_nums =  sum(item['count'] for item in data['comments'])
print(sum_nums)

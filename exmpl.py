import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
import ssl

url = urllib.request.urlopen('https://py4e-data.dr-chuck.net/comments_1951521.html')
bs = BeautifulSoup(url, 'html.parser')

# Find all tags named span
tags = bs.find_all('span')

# Put a variable to store the total sum
total = 0

for tag in tags:
    num = int(tag.contents[0])
    total += num

print('Sum: ', total)

            



    
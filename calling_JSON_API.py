import urllib.request, urllib.parse, urllib.error
import json
import ssl

api_key = False

# Opening alternative for google maps api
if api_key is False:
    api_key = 42
    serviceurl = 'http://py4e-data.dr-chuck.net/json?'
else:
    print('Data couldnt found')

# Ignore ssl certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Entering location details
while True:
    address = input('Enter the location: ')
    if len(address) < 1: break

    par = dict()
    par['address'] = address
    if api_key is not False: par['key'] = api_key
    url = serviceurl + urllib.parse.urlencode(par)

    print('Retrieving...', url)
    uh = urllib.request.urlopen(url, context=ctx)
    data = uh.read().decode()
    print('Retrieved', len(data), 'characters')

    try:
        js = json.loads(data)
    except:
        js = None

    if not js or 'status' not in js or js['status'] != 'OK':
        print('==Failure to retrieve data==')
        print(data)
        continue

    print(json.dumps(js, indent=4))

    if 'results' in js and len(js['results']) > 0:
        place_id = js['results'][0]['place_id']
        print('Place ID:', place_id)

        lat = js['results'][0]['geometry']['location']['lat']
        lng = js['results'][0]['geometry']['location']['lng']
        print('lat', lat, 'lng', lng)
        location = js['results'][0]['formatted_address']
        print(location)
    else:
        print('No results found for the given address.')
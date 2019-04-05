import requests
#example using rfapi
url = 'https://cloudrf.com/API/area'
payload = 'uid=21531&key=a8ec44b5ad85e0ab626e55f20e3cb5da111999a2&lat=50.355108&lon=-4.152938&txh=8&frq=868&rxh=2&dis=m&txw=0.1&aeg=2.14&rxg=2.14&pm=1&pe=1&res=30&rad=6&out=2&rxs=-95&ant=38&azi=0&cli=5&file=kmz&nam=DRAKES_ISLAND&net=DEVON&out=2&pol=v&red=-60&ter=15&tlt=0&vbw=0&col=10'
headers = {
  'Content-Type': 'application/x-www-form-urlencoded'
}
response = requests.request('POST', url, headers = headers, data = payload, allow_redirects=False)
print(response.text)
import json

f = open('keys.json', 'r')
z = f.read()
f.close()

apiKeys = json.loads(z)
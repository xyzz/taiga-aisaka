import urllib.request
import urllib.parse
import json
import sys

files = [line.rstrip() for line in open("list", "r").readlines()]

request = "http://toradora.xyz.is/wiki/api.php?action=query&titles={}&prop=imageinfo&iiprop=url&format=json".format(
	"|".join(["File:{}en.png".format(urllib.parse.quote(x)) for x in files])
)

data = json.loads(urllib.request.urlopen(request).read().decode("utf-8"))
sys.stdout.write("+")
for page in data["query"]["pages"].values():
	sys.stdout.flush()
	url = page["imageinfo"][0]["url"]
	name = page["title"][5:-6] + ".png"
	urllib.request.urlretrieve(url, "source/" + name)
	sys.stdout.write(".")
print()

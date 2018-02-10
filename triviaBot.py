from multiprocessing import Pool
from adb import ADB
from PIL import Image
import pytesseract
import glob
import os
import time
import json
import urllib.request
import urllib
import http
import base64

from apiKeys import apiKeys


def BingWebSearch(search):

	bingKey = apiKeys['bing']
	host = "api.cognitive.microsoft.com"
	path = "/bing/v7.0/search"

	term = "Microsoft Cognitive Services"

	headers = {'Ocp-Apim-Subscription-Key': bingKey}
	conn = http.client.HTTPSConnection(host)
	query = urllib.parse.quote(search)
	conn.request("GET", path + "?q=" + query, headers=headers)
	response = conn.getresponse()
	return response


def BingCheck(query, answers, keyword):

	result = BingWebSearch(query).read().decode('utf-8').encode('ascii', 'ignore').decode('ascii')
	a = json.loads(result)

	f = open('abc', 'w')
	f.write(result)
	f.close()


	if isinstance(answers, list):
		answerScore = [0,0,0]
		for result in a['webPages']['value']:

			name = result['name'].encode('ascii', 'ignore').decode('ascii')
			snippet = result['snippet'].encode('ascii', 'ignore').decode('ascii')


			i = 0


			while i < 3:
				if answers[i].lower() in name.lower():
					answerScore[i] += 1
				if answers[i].lower() in snippet.lower():
					answerScore[i] += 1

				i += 1


	else:
		answerScore = 0
		for result in a['webPages']['value']:

			name = result['name'].encode('ascii', 'ignore').decode('ascii')
			snippet = result['snippet'].encode('ascii', 'ignore').decode('ascii')

			if answers.lower() in snippet.lower():
				answerScore += 1
			if answers.lower() in name.lower():
				answerScore += 1




	return answerScore


def GoogleCheck(questionString, answers, keyword):
	apiKey = apiKeys['googleapi']
	cx = apiKeys['googlecx']

	questionString = urllib.parse.quote_plus(questionString)
	urlString = "https://www.googleapis.com/customsearch/v1?q={}&cx={}&key={}".format(questionString, cx, apiKey)

	with urllib.request.urlopen(urlString) as url:
		encJson = json.loads(url.read().decode())

	answerScore = [0, 0, 0]

	for result in encJson['items']:
		i = 0
		while i < 3:
			if answers[i] in result['snippet'].lower():
				answerScore[i] += 1
			if answers[i] in result['title'].lower():
				answerScore[i] += 1

			i += 1

	return answerScore


def NegativeCheck(questionString, answers):
	preNoun = ['for', 'are', 'an', 'a']
	qWords = questionString.split(' ')
	qLength = len(qWords)

	for sep in preNoun:
		if sep in qWords:
			sIndex = qWords.index(sep)
			keyword = qWords[sIndex + 1].replace('?', '')


def WikipediaCheck(questionString, answers, keyword):

	answerScore = []

	for answer in answers:

		pAnswer = urllib.parse.quote(answer)

		urlString = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={}&utf8=".format(
			pAnswer)

		with urllib.request.urlopen(urlString) as url:
			encJson = json.loads(url.read().decode())

		if encJson['query']['searchinfo']['totalhits'] > 0:
			wikiPageName = encJson['query']['search'][0]['title']
			pWikiName = urllib.parse.quote(wikiPageName)
			urlString = "https://en.wikipedia.org/w/api.php?action=query&titles={}&format=json&prop=revisions&rvprop=content&formatversion=2".format(
				pWikiName)

			with urllib.request.urlopen(urlString) as url:
				encJson = json.loads(url.read().decode())

			text = encJson['query']['pages'][0]['revisions'][0]['content'].lower()

			answerScore.append(text.count(keyword))

		else:
			answerScore.append(0)
			pass

	return answerScore


def getLatest():
	list_of_files = glob.glob('/home/david/Downloads/*')
	latest_file = max(list_of_files, key=os.path.getctime)
	return latest_file


def getText(file):

	im = Image.open(file)

	left = 44
	top = 310
	width = 1000
	height = 800
	box = (left, top, left+width, top+height)
	im = im.crop(box)

	GrayImg = im.convert('L')
	BlackWhite = GrayImg.point(lambda x: 0 if x<220 else 255, '1')

	BlackWhite.save('testbw.jpg', 'jpeg')


	with open('testbw.jpg', "rb") as image_file:
	    encoded_string = base64.b64encode(image_file.read())

	data = {
	'apikey' : apiKeys['ocr'],
	'base64Image' : 'data:image/png;base64,' + encoded_string.decode('utf-8')
	}
	data = bytes( urllib.parse.urlencode( data ).encode() )
	handler = urllib.request.urlopen( 'https://api.ocr.space/parse/image', data );
	result = handler.read().decode( 'utf-8' );

	a = result

	b = json.loads(a)

	text = b['ParsedResults'][0]['ParsedText'].replace('\r', '')

	text2 = text.split('\n')

	leng = len(text2)

	i = 0
	ii = 0

	questionString = ''

	while i < leng:
		questionString += text2[i]
		if('?' in text2[i]):
			ii = i + 1
			i = leng
		else:
			questionString += ' '
		i+=1
	questionString = questionString.encode('ascii', 'ignore').decode('ascii')

	answers = []
	while ii < leng and len(answers) < 3:
		if len(text2[ii]) > 0:
			answers.append(text2[ii].encode('ascii', 'ignore').decode('ascii').lower())
		ii += 1

	data = {}
	data['questionString'] = questionString
	data['answers'] = answers

	return data




# def getText(file):

# 	im = Image.open(file)

# 	left = 44
# 	top = 310
# 	width = 1000
# 	height = 800
# 	box = (left, top, left+width, top+height)
# 	im = im.crop(box)

# 	GrayImg = im.convert('L')
# 	BlackWhite = GrayImg.point(lambda x: 0 if x<220 else 255, '1')

# 	# BlackWhite.save('testbw.jpg', 'jpeg')


# 	text = pytesseract.image_to_string(BlackWhite)
# 	text2 = text.split('\n')

# 	leng = len(text2)

# 	i = 0
# 	ii = 0

# 	questionString = ''

# 	while i < leng:
# 		questionString += text2[i]
# 		if('?' in text2[i]):
# 			ii = i + 1
# 			i = leng
# 		else:
# 			questionString += ' '
# 		i+=1
# 	questionString = questionString.encode('ascii', 'ignore').decode('ascii')

# 	answers = []
# 	while ii < leng and len(answers) < 3:
# 		if len(text2[ii]) > 0:
# 			answers.append(text2[ii].encode('ascii', 'ignore').decode('ascii').lower())
# 		ii += 1

# 	data = {}
# 	data['questionString'] = questionString
# 	data['answers'] = answers

# 	return data

check_types = {
	"google": GoogleCheck,
	"bing": BingCheck,
	# "negative": NegativeCheck,
	"wiki": WikipediaCheck
}

def check_method(params):
	check_type, questionString, answers, keyword = params
	result = check_types.get(check_type)(questionString, answers, keyword)
	print(result)
	i = 0
	answer = "----- %s ---- \n" % check_type
	while i < 3:
		answer += "{}: {}".format(answers[i], result[i]) + "\n"
		i += 1

	print(answer)


def searchFor(data):
	os.system('clear')
	questionString = data['questionString'].encode('ascii', 'ignore').decode('ascii')
	answers = data['answers']

	checks_to_run = check_types.keys()
	p = Pool(len(check_types.keys()))

	check_params = []

	
	print(questionString)
	print(answers[0])
	print(answers[1])
	print(answers[2])

	keyword = input('keyword: ')
	for check in checks_to_run:
		check_params.append((check, questionString, answers, keyword))
	p.map(check_method, check_params)



def Go():
	os.system('adb shell screencap -p > image.png')
	searchFor(getText('image.png'))

Go()
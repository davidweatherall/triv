from multiprocessing import Pool
from PIL import Image
import glob
import os
import time
import json
import urllib.request
import urllib
import http
import base64

from apiKeys import apiKeys


def cleanResult(result):
	replaceArray = [
		['-', ' ']
	]
	for a in replaceArray:
		result = result.replace(a[0], a[1])

	if result[len(result)-1] == ' ':
		result = result[:-1]

	return result.lower()

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

	# f = open('abc', 'w')
	# f.write(result)
	# f.close()


	if isinstance(answers, list):
		answerScore = [0,0,0]
		for result in a['webPages']['value']:

			name = result['name'].encode('ascii', 'ignore').decode('ascii')
			snippet = result['snippet'].encode('ascii', 'ignore').decode('ascii')


			i = 0


			while i < 3:
				if answers[i].lower() in cleanResult(name):
					answerScore[i] += 1
				if answers[i].lower() in cleanResult(snippet):
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

	if 'items' in encJson:
		for result in encJson['items']:
			i = 0
			while i < 3:
				if answers[i] in cleanResult(result['snippet']):
					answerScore[i] += 1
				if answers[i] in cleanResult(result['title']):
					answerScore[i] += 1

				i += 1

		return answerScore
	else:
		return ['Error', 'Error', 'Error']


def NegativeCheck(questionString, answers):
	preNoun = ['for', 'are', 'an', 'a']
	qWords = questionString.split(' ')
	qLength = len(qWords)

	for sep in preNoun:
		if sep in qWords:
			sIndex = qWords.index(sep)
			keyword = qWords[sIndex + 1].replace('?', '')


def GetWikiScore(questionString, answer, keyword):

	keyword = keyword.lower()

	pAnswer = urllib.parse.quote(answer)

	urlString = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={}&utf8=".format(
		pAnswer)

	with urllib.request.urlopen(urlString) as url:
		wikiText = url.read().decode()

	encJson = encJson = json.loads(wikiText)



	if encJson['query']['searchinfo']['totalhits'] > 0:
		wikiPageName = encJson['query']['search'][0]['title']
		pWikiName = urllib.parse.quote(wikiPageName)
		urlString = "https://en.wikipedia.org/w/api.php?action=query&titles={}&format=json&prop=revisions&rvprop=content&formatversion=2".format(
			pWikiName)

		with urllib.request.urlopen(urlString) as url:
			wikiContent = url.read().decode()

		encJson2 = json.loads(wikiContent)

		text = cleanResult(encJson2['query']['pages'][0]['revisions'][0]['content'])

		# f = open('abc', 'w')
		# f.write(text.encode('ascii', 'ignore').decode('ascii'))
		# f.close()

		return text.count(keyword)

	else:
		return 0

def getLatest():
	list_of_files = glob.glob('/home/david/Downloads/*')
	latest_file = max(list_of_files, key=os.path.getctime)
	return latest_file


def getText(file):

	im = Image.open(file)

	left = 44
	top = 310
	width = 1000
	height = 1000
	box = (left, top, left+width, top+height)
	im = im.crop(box)

	GrayImg = im.convert('L')
	BlackWhite = GrayImg.point(lambda x: 0 if x<220 else 255, '1')

	BlackWhite.save('testbw.jpg', 'jpeg')

	text = ocrImage('testbw.jpg')

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
		if len(text2[ii]) > 0 and "prize" not in text2[ii].encode('ascii', 'ignore').decode('ascii').lower():
			answers.append(cleanResult(text2[ii].encode('ascii', 'ignore').decode('ascii')))
		ii += 1

	data = {}
	data['questionString'] = questionString
	data['answers'] = answers

	return data


check_types = {
	"google": GoogleCheck,
	"bing": BingCheck,
	# "negative": NegativeCheck,
	"wiki": GetWikiScore,
	"wikipage": GetWikiScore,
}

def check_method(params):
	check_type, questionString, answers, keyword = params
	result = { 'type' : check_type, 'answers' : answers, 'data' : check_types.get(check_type)(questionString, answers, keyword), 'keyword': keyword }
	return result


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
	splitword = input('split word: ')
	wikiPageSearch = input('wiki page search: ')

	i = 0
	if splitword: 
		while i <3:
			answers[i] = answers[i].split(splitword)[0]
			i += 1

	for check in checks_to_run:
		if check != 'wiki' and check != 'wikipage':
			check_params.append((check, questionString, answers, keyword))

	if keyword:
		i = 0
		while i < 3:
			check_params.append(['wiki', questionString, answers[i], keyword])
			i += 1

	if wikiPageSearch:
		i = 0
		while i < 3:
			check_params.append(['wikipage', questionString, wikiPageSearch, answers[i]])
			i += 1

	result = p.map(check_method, check_params)

	PrintData(result)




def Go():
	os.system('adb shell screencap -p > image.png')
	searchFor(getText('image.png'))


def PrintData(data):

	wikiAnswers = {}
	wikiPageAnswers = {}

	for entry in data:
		if entry['type'] == 'google':
			answers = entry['answers']
			google = entry['data']
			# google

		elif entry['type'] == 'bing':
			bing = entry['data']

		elif entry['type'] == 'wiki':
			wikiAnswers[entry['answers']] = entry['data']
			# wiki

		elif entry['type'] == 'wikipage':
			wikiPageAnswers[entry['keyword']] = entry['data']

	
	print('--------Bing---------')
	i = 0
	while i < 3:
		print(answers[i] + ": " + str(bing[i]))
		i += 1

	print('')


	print('--------Google---------')
	i = 0
	while i < 3:
		print(answers[i] + ": " + str(google[i]))
		i += 1


	print('')
	
	if wikiAnswers:
		print('--------Wiki Keyword Check---------')
		i = 0
		while i < 3:
			print(answers[i] + ": " + str(wikiAnswers[answers[i]]))
			i += 1
	
	if wikiPageAnswers:
		print('------ Wiki Page Check ---------')
		i = 0
		while i < 3:
			print(answers[i] + ": " + str(wikiPageAnswers[answers[i]]))
			i += 1



def encode_image(image_path, charset):
	with open(image_path, 'rb') as image:
		b64_img = base64.b64encode(image.read())

	return b64_img.decode(charset)


def get_response(b64encoded_image):
	req_url = '/v1/images:annotate?key=' + apiKeys['googlevision']

	req_body = {
	  "requests": [
		{
		  "image": {
			"content": b64encoded_image
		  },
		  "features": [
			{
			  "type": "TEXT_DETECTION"
			}
		  ]
		}
	  ]
	}

	req_headers = {"Content-Type": "application/json; charset=utf-8"}


	host = 'vision.googleapis.com'

	conn = http.client.HTTPSConnection(host)
	# query = urllib.parse.quote(search)
	conn.request("POST", req_url, headers=req_headers, body=json.dumps(req_body))
	response = conn.getresponse()

	return response


def ocrImage(local_image_path):
	body = get_response(encode_image(local_image_path, 'ascii')).read().decode('utf-8').encode('ascii', 'ignore').decode('ascii')

	a = json.loads(body)

	return a['responses'][0]['textAnnotations'][0]['description']
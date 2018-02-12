from multiprocessing import Pool
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

		text = encJson2['query']['pages'][0]['revisions'][0]['content'].lower()

		return text.count(keyword)

	else:
		return 0


# def WikipediaCheck(questionString, answers, keyword):

# 	wikiList = []

# 	for answer in answers:
# 		wikiList.append([keyword, answer])

# 	p = Pool(5)

# 	answerScore = p.map(GetWikiScore, wikiList)

# 	return answerScore


def getLatest():
	list_of_files = glob.glob('/home/david/Downloads/*')
	latest_file = max(list_of_files, key=os.path.getctime)
	return latest_file


def getText(file):

	im = Image.open(file)

	left = 44
	top = 310
	width = 1000
	height = 900
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

	i = 0
	while i < 3:
		check_params.append(['wiki', questionString, answers[i], keyword])
		i += 1

	i = 0
	while i < 3:
		check_params.append(['wikipage', questionString, wikiPageSearch, answers[i]])
		i += 1

	print(check_params)

	result = p.map(check_method, check_params)

	PrintData(result)




def Go():
	os.system('adb shell screencap -p > image.png')
	searchFor(getText('image.png'))


def PrintData(data):

	print(data)

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
	
	print('--------Wiki Keyword Check---------')
	i = 0
	while i < 3:
		print(answers[i] + ": " + str(wikiAnswers[answers[i]]))
		i += 1
	
	print('------ Wiki Page Check ---------')
	i = 0
	while i < 3:
		print(answers[i] + ": " + str(wikiPageAnswers[answers[i]]))
		i += 1
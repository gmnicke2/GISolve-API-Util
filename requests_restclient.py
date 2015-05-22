import urllib
import requests #using requests instead of pycURL
import json

def cg_rest_mergequery(url, query) :
	achar = '?'
	if ('?' in url) :
		achar = '&'
	if (len(query) > 0) :
		url = url + achar + query #concatenate ?query or &query to URL
	return url

def cg_rest_call(url, req, data) :
	query = urllib.urlencode(data)
	#print 'query is: '+query
	#PROCESS REQUEST
	if(req == 'get' or req == 'GET') :
		url = cg_rest_mergequery(url,query)#concatenate query
		r = requests.get(url,timeout=50,verify=False)
	elif(req == 'put' or req == 'PUT') :
		header = {'Content-Length: ':str(len(query))}#create header dict
		r = requests.put(url,data=data,header=header,timeout=50,verify=False)
	elif(req == 'delete' or req == 'DELETE') :
		url = cg_rest_mergequery(url, query)#concatenate query
		r = requests.delete(url, timeout=50,verify=False)
	elif(req == 'post' or req == 'POST') :
		#print "POSTING to URL: " + url + "\ndata: " + json.dumps(data) + "\ntimeout: 50"
		r = requests.post(url,data=data,timeout=50,verify=False)
	else :
		print 'HTTP request method ' + req + ' is not supported \n'
		return None

	try :
		m = r.json
	except ValueError:
		print 'Response json failed to create\n'
		return None

	return m

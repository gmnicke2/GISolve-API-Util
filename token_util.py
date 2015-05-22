import json
import requests
from openservice_util import *

#issue token
def issueToken() :
	url = getinfo('url')
	#A sample issue token request JSON
	request_json = {'username' : getinfo('username'),
		'password' : getinfo('password'),
		'lifetime' : 15*3600,
		'binding' : 1
		}
	#Need to append "token" to the API URL
	resource = "token"
	#Append resource ("token") to URL
	url += resource
	#Make RESTful POST call to "token" resource
	#Revoke would use DELETE, Verify would use PUT
	request_ret = requests.post(url,data=request_json,timeout=50,verify=False);
	#Get the response from the REST POST in JSON format
	response_json = request_ret.json
	try :
		token = response_json['result']['token']
	except (TypeError,KeyError) :
		print "Token creation failed. (Check your arguments)"
		exit()
	printResponse('Issue Token (HTTP POST)',request_json,response_json)
	return token

#verify token
def verifyToken() :
	url = getinfo('url')
	request_json = {
		'consumer' : getinfo('clientid'),
		'remote_addr' : getinfo('clientip'),
		'token' : getinfo('token'),
		'username' : getinfo('username'),
		'authrequest' : 'default'
	}
	resource = "token"
	url += resource
	headers = {'Content-Length' : str(len(json.dumps(request_json)))}
	request_ret = requests.put(url,params=request_json,headers=headers,timeout=50,verify=False)
	response_json = request_ret.json
	printResponse('Verify Token (HTTP PUT)',request_json,response_json)
	if request_json['status'] == 'success' :
		return True
	else :
		return False

#revoke token
def revokeToken() :
	url = getinfo('url')
	request_json = {
	'username' : getinfo('username'),
    	'password' : getinfo('password'),
	'token' : getinfo('token')
	}
	resource = "token"
	url += resource
	request_ret = requests.delete(url,params=request_json,timeout=50,verify=False)
	response_json = request_ret.json
	printResponse('Revoke Token \"%s\" (HTTP DELETE)' %getinfo('token'),request_json,response_json)
	#Token was revoked successfully, so store empty string as environ token
	if response_json['status'] == 'success' :
		storeinfo('token','')
		return True
	else :
		return False

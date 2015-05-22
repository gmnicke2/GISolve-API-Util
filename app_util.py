import json
import requests
from token_util import *
from openservice_util import *

#Register an app, must have a valid token
def registerApp() :
	#Gather required information
	username = getinfo('username')
	password = getinfo('password')
	appname = getinfo('appname')
	url = getinfo('url')
	token = getinfo('token')
	#If token wasn't actually issued before this call,
	#Ask for existing or just issue a new one
	if not token :
		yn = raw_input("Token not found: enter existing token (y/n)? ")
		while not (yn == 'y' or yn == 'n') :
			yn = raw_input("Please enter 'y' or 'n' : ")
		if yn == 'y' :
			token = raw_input("\nPlease enter existing token: ")
		else :
			token = issueToken()
		storeinfo('token',token)
	#Set up request JSON
	request_json = {
		'token' : token,
		'app' : appname,
		'longname' : 'Test app by %s' % username,
		'version' : 'V0.1',
		'info' : '<h2>%s</h2><p>Description of App (%s) Goes Here</p><p>Author: %s</p>' % (appname,appname,username),
		'author' : username,
		'tags' : 'test, app, %s' % username
	}
	#Append resource (app) to API URL
	resource = "app"
	url += resource
	#App register is a POST RESTful call
	#App configure is also a POST call
	#Get app information/configuration are GET calls
	request_ret = requests.post(url,data=request_json,timeout=50,verify=False)
	#Get the response from the REST POST in JSON format
	response_json = request_ret.json
	printResponse('Register App \"%s\" (HTTP POST)' %appname, request_json, response_json)
	#on success, returns the registered app's name
	try:
		return response_json['result']['app']
	except (TypeError,KeyError) :
		print "App Registration failed for \"%s\"" %appname
		print "Did you issue a valid token?"
		return None

#configure app with config JSON read in from a file
def configApp(config_filename) :
	print "Config File: \"" + config_filename + "\""
	f = open(config_filename)
	config = json.load(f)
	f.close()
	if not config :
		print "Config File incorrectly formatted.\n"
		return None
	request_json = {
		'token' : getinfo('token'),
		'app' : getinfo('appname'),
		'config' : json.dumps(config)
	}
	#append resource (appconfig) to API URL
	url = getinfo('url') + "appconfig"
	#Make RESTful POST call
	request_ret = requests.post(url,data=request_json,timeout=50,verify=False)
	#Get the response from the REST POST in JSON format
	response_json = request_ret.json
	printResponse('Configure app  \"%s\" (HTTP POST)' %getinfo('appname'), request_json, response_json)
	return True

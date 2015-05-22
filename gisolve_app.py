import json
import requests
import argparse
import requests
import os

#prints information if -v or --verbose specified
def printResponse(request_type, request_json, response_json) :
	try :
		status = response_json['status']
	except KeyError :
		print "\nResponse JSON failed to create."
		return None
	if(status != 'success') :
		print request_type + " Request Failed\n"
		return None
	request_json['password'] = '*******'
	print "\nURL: " + os.environ.get('url') + "\n"
	print "Request: " + request_type + "\n"
	print "Request Data (in JSON format): " + json.dumps(request_json) + "\n"
	print "Response (in JSON format): " + json.dumps(response_json) + "\n"

#parses command line arguments (gives help if done incorrectly)
def parseArgs() :
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--url", help="Set API URL")
	parser.add_argument("-a", "--appname", help="Set App Name")
	parser.add_argument("-c", "--clientid", help="Set Client ID")
	parser.add_argument("-i", "--clientip", help="Set Client IP")
	parser.add_argument("-u", "--username", help="Set Username")
	parser.add_argument("-p", "--password", help="Set Password")
	parser.add_argument("-act", "--action", help="register/configure/os.environ.get/getconfig for App")
	parser.add_argument("-t", "--token", help="Set Token")
	parser.add_argument("-v", "--verbose",action="store_true", help="Print results/errors")
	parser.add_argument("-cf", "--configfile", help="(For configure app) config JSON file path")
	parser.add_argument("-df", "--destfile", help="(For get config/info) file to write configuration/info JSON to")
	args = parser.parse_args()
	os.environ['verbose'] = str(args.verbose)
	#print help and exit if not all args supplied
	if not bool(args.url and args.appname and args.clientid and args.clientip and args.username and args.action and args.token) :
		parser.print_help()
		exit()
	#create environmental variables for existing and non-existing arguments
	#used for OpenService API calls (which make REST calls)
	for arg in vars(args) :
		if getattr(args,arg) and (arg != 'verbose'):
			os.environ[arg] = getattr(args,arg)
	#append a terminating '/' if non-existent in API URL
	if not os.environ['url'].endswith('/') :
		os.environ['url'] += '/'
	return parser

############################API CALLS##################################
#Register an app, must have a valid token
def registerApp() :
	#Gather required information
	username = os.environ.get('username')
	password = os.environ.get('password')
	appname = os.environ.get('appname')
	url = os.environ.get('url')
	token = os.environ.get('token')
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
	if(os.environ.get('verbose') == 'True') :
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
	if(os.environ.get('verbose') == 'True') :
		print "Config File: \"" + config_filename + "\""
	f = open(config_filename)
	config = json.load(f)
	f.close()
	if not config :
		print "Config File incorrectly formatted.\n"
		return None
	request_json = {
		'token' : os.environ.get('token'),
		'app' : os.environ.get('appname'),
		'config' : json.dumps(config)
	}
	#append resource (appconfig) to API URL
	url = os.environ.get('url') + "appconfig"
	#Make RESTful POST call
	request_ret = requests.post(url,data=request_json,timeout=50,verify=False)
	#Get the response from the REST POST in JSON format
	response_json = request_ret.json
	if(os.environ.get('verbose') == 'True') :
		printResponse('Configure app  \"%s\" (HTTP POST)' %os.environ.get('appname'), request_json, response_json)
	return True

def main() :
	parser = parseArgs()
	args = parser.parse_args()
	action = os.environ['action'].lower()
	if action == 'register' :
		registerApp()
	elif action == 'configure' :
		#check if config file was given or if it's invalid
		if args.configfile and os.path.exists(args.configfile) :
			configApp(args.configfile)
		else :
			print 'Config File Doesn\'t Exist'
	else :
		parser.print_help()
		exit()

main()
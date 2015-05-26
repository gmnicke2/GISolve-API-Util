# Set of utilities to register/configure an application with REST calls
# as well as get info or configuration of applications registered
# requires a valid token given on the command line at run time 

import json
import requests
import argparse
import requests
import os

# prints information if -v or --verbose specified
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
	print "Request Data (in JSON format): " + json.dumps(request_json,indent=4,separators=(',', ': ')) + "\n"
	print "Response (in JSON format): " + json.dumps(response_json,indent=4,separators=(',', ': ')) + "\n"

# parses command line arguments (gives help if done incorrectly)
def parseArgs() :
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose",action="store_true", help="Print results/errors")
	parser.add_argument("-r", "--url", help="Set API URL")
	parser.add_argument("-a", "--appname", help="Set App Name")
	parser.add_argument("-act", "--action", help="register/configure/getinfo/getconfig for App")
	parser.add_argument("-t", "--token", help="Set Token")
	parser.add_argument("-u", "--username",help="Set Username")
	parser.add_argument("-cf", "--configfile", help="(For configure app) config JSON file path")
	parser.add_argument("-df", "--destfile", help="(For get config/info) file to write configuration/info JSON to")
	args = parser.parse_args()
	os.environ['verbose'] = str(args.verbose)
	# print help and exit if not all required args supplied
	if not bool(args.url and args.appname and args.action and args.token and args.username) :
		parser.print_help()
		exit()
	# create environmental variables for existing and non-existing arguments
	# used for OpenService API calls (which make REST calls)
	for arg in vars(args) :
		if getattr(args,arg) and (arg != 'verbose'):
			os.environ[arg] = getattr(args,arg)
	# append a terminating '/' if non-existent in API URL
	if not os.environ['url'].endswith('/') :
		os.environ['url'] += '/'
	return (parser,args)

############################API CALLS##################################
# Register an app, must have a valid token
def registerApp() :
	# Set up request JSON
	request_json = {
		'token' : os.environ.get('token'),
		'app' : os.environ.get('appname'),
		'longname' : 'Test app by %s' % os.environ.get('username'),
		'version' : 'V0.1',
		'info' : '<h2>%s</h2><p>Description of App (%s) Goes Here</p><p>Author: %s</p>' % (os.environ.get('appname'),os.environ.get('appname'),os.environ.get('username')),
		'author' : os.environ.get('username'),
		'tags' : 'test, app, %s' % os.environ.get('username')
	}
	# Append resource (app) to API URL
	resource = "app"
	url = os.environ.get('url') + resource
	# App register is a POST RESTful call
	# App configure is also a POST call
	# Get app information/configuration are GET calls
	request_ret = requests.post(url,data=request_json,timeout=50,verify=False)
	# Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	if(os.environ.get('verbose') == 'True') :
		printResponse('Register App \"%s\" (HTTP POST)' %os.environ.get('appname'), request_json, response_json)
	# on success, return the registered app's name
	try :
		return response_json['result']['app']
	except (TypeError,KeyError) :
		print "\nApp Registration failed for \"%s\"" %os.environ.get('appname')
		print "Did you issue a valid token?"
		return None

# get app info and write it in JSON format to the destfile given as argument
def getAppInfo(dest_filename) :
	if(os.environ.get('verbose') == 'True') :
		print "\nWriting info to \"" + dest_filename + "\""
	request_json = {
		'token' : os.environ.get('token'),
		'app' : os.environ.get('appname')
	}
	# append resource (app) to API URL
	url = os.environ.get('url') + "app"
	# Make a GET RESTful call
	request_ret = requests.get(url, params=request_json,timeout=50,verify=False)
	# Get the response from the REST GET in JSON format (will be written to dest file)
	response_json = request_ret.json()
	if(os.environ.get('verbose') == 'True') :
		printResponse('Get app info for \"%s\" (HTTP GET)' %os.environ.get('appname'), request_json, response_json)
	# Dump the response JSON (the app info) into the destination file
	with open(dest_filename, 'w') as outfile :
		json.dump(response_json,outfile,indent=4,separators=(',', ': '))
		outfile.write('\n')
		outfile.close()
	# if successful, return True
	return True

# configure app with config JSON read in from a file
def configApp(config_filename) :
	if(os.environ.get('verbose') == 'True') :
		print "\nConfig File: \"" + config_filename + "\""
	f = open(config_filename)
	config = json.load(f)
	f.close()
	if not config :
		print "Config File incorrectly formatted. (JSON)\n"
		return None
	request_json = {
		'token' : os.environ.get('token'),
		'app' : os.environ.get('appname'),
		'config' : json.dumps(config)
	}
	# append resource (appconfig) to API URL
	url = os.environ.get('url') + "appconfig"
	# Make RESTful POST call
	request_ret = requests.post(url,data=request_json,timeout=50,verify=False)
	# Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	if(os.environ.get('verbose') == 'True') :
		printResponse('Configure app  \"%s\" (HTTP POST)' %os.environ.get('appname'), request_json, response_json)
	# If correctly configured, return true
	return True

# get app config and write it in JSON format to the destfile given as an argument
def getAppConfig(dest_filename) :
	if(os.environ.get('verbose') == 'True') :
		print '\nWriting config to \"' + dest_filename + '\"'
	request_json = {
		'token' : os.environ.get('token'),
		'app' : os.environ.get('appname')
	}
	# append resource (appconfig) to API URL
	url = os.environ.get('url') + "appconfig"
	# Make a GET RESTful call
	request_ret = requests.get(url, params=request_json,timeout=50, verify=False)
	# Get the response from the REST GET in JSON format (will be written to dest file)
	response_json = request_ret.json()
	if(os.environ.get('verbose') == 'True') :
		printResponse('Get app config for \"%s\" (HTTP GET)' %os.environ.get('appname'), request_json, response_json)
	# Dump the response JSON (the app config) into the destination file
	with open(dest_filename, 'w') as outfile :
		json.dump(response_json,outfile,indent=4,separators=(',',': '))
		outfile.write('\n')
		outfile.close()
	# If successful, return True
	return True

def main() :
	parser_info = parseArgs()
	parser = parser_info[0]
	args = parser_info[1]
	action = os.environ.get('action').lower()
	if action == 'register' :
		registerApp()
	elif action == 'configure' :
		# check if config file was given or if it's invalid
		if args.configfile and os.path.exists(args.configfile) :
			configApp(args.configfile)
		else :
			print 'Config File Doesn\'t Exist'
	elif action == 'getinfo' :
		# check if destination file was specified in command-line arguments
		if args.destfile :
			getAppInfo(args.destfile)
		elif not os.path.exists("getinfo_out.json") : # use this path as default
			getAppInfo("getinfo_out.json")
		else : # if default path exists, don't overwrite it, just print help & exit
			parser.print_help()
			exit()
	elif action == 'getconfig' :
		# check if destination file was specified in command-line arguments
		if args.destfile :
			getAppConfig(args.destfile)
		elif not os.path.exists("getconfig_out.json") : # use this path as default
			getAppConfig("getconfig_out.json")
		else : # if default path exists, don't overwrite it, just print help & exit
			parser.print_help()
			exit()
	else :
		parser.print_help()
		exit()

main()

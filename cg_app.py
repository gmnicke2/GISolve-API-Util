# Set of utilities to register/configure a CG application with REST calls
# as well as get info or configuration of applications registered
# requires a valid token either in bash environment or given at command line

from cg_print import *
import json
import requests
import argparse
import requests
import os, sys

# Used to disable InsecureRequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

# any argument used to overwrite environ vars is stored here;
# it is accessed throughout the code with the format:
# env_overwrite.get(<KEY>,<If KEY doesn't exist use environ or its default -- usually ''>)
# this allows for keys that don't exist / have no entries to always
# evaluate to False for error handling as well as keep the code succinct
env_overwrite = {}

verbose = False

# parses command line arguments (gives help if done incorrectly)
def parseArgs() :
	global verbose
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose",action="store_true", help="Print results/errors to stdout")
	parser.add_argument("-act", "--action", help="(REQUIRED) register/configure/getinfo/getconfig")
	parser.add_argument("-a", "--appname", help="Set App Name")
	parser.add_argument("-r", "--url", help="Set API URL")
	parser.add_argument("-u", "--username", help="Set Username")
	parser.add_argument("-t", "--token", help="Set Token")
	parser.add_argument("-cf","--configfile", help="For action \'configure\' config file in JSON format")
	parser.add_argument("-df","--destfile", help="For actions \'getinfo\' and \'getconfig\' destination file to write response")
	args = parser.parse_args()
	if not args.action :
		parser.print_help()
		exit()
	os.environ['CG_ACTION'] = args.action
	if args.verbose :
		verbose = True
	# used for OpenService API calls (which make REST calls)
	for arg in vars(args) :
		if getattr(args,arg) and arg is not 'verbose':
			env_overwrite[arg] = getattr(args,arg)
	# append a terminating '/' if non-existent in API URL
	if env_overwrite.get('url','') and not env_overwrite.get('url','').endswith('/') :
		env_overwrite['url'] += '/'
	elif os.getenv('CG_API_URL','') and not os.getenv('CG_API_URL','').endswith('/') :
		os.environ['CG_API_URL'] += '/'
	elif not os.getenv('CG_API_URL','') :
		sys.stderr.write('CG_API_URL (API URL for REST calls) not specified\n')
		exit()
	if not env_overwrite.get('appname',os.getenv('CG_APP_NAME','')) :
		sys.stderr.write('No CG_APP_NAME found or command line argument specified\n')
		exit()
	return (parser,args)

############################API CALLS##################################
# Register an app, must have a valid token
def registerApp() :
	# Set up request JSON
	global verbose
	USERNAME = env_overwrite.get('username',os.getenv('CG_USERNAME',''))
	TOKEN = env_overwrite.get('token',os.getenv('CG_TOKEN',''))
	APPNAME = env_overwrite.get('appname', os.getenv('CG_APP_NAME',''))
	URL = env_overwrite.get('url',os.getenv('CG_API_URL','https://sandbox.cigi.illinois.edu/home/rest/'))
	if not TOKEN :
		sys.stderr.write('No valid CG_TOKEN given\n')
		exit()
	request_json = {
		'token' : TOKEN,
		'app' : APPNAME,
		'longname' : 'Test app by %s' % USERNAME,
		'version' : 'V0.1',
		'info' : '<h2>%s</h2><p>Description of App (%s) Goes Here</p><p>Author: %s</p>' % (APPNAME,APPNAME,USERNAME),
		'author' : USERNAME,
		'tags' : 'test, app, %s' % USERNAME
	}
	# Append resource (app) to API URL
	resource = "app"
	URL += resource
	# App register is a POST RESTful call
	# App configure is also a POST call
	# Get app information/configuration are GET calls
	try:
		request_ret = requests.post(URL,data=request_json,timeout=50,verify=False)
	except (requests.exceptions.ConnectionError,requests.exceptions.HTTPError,requests.exceptions.MissingSchema) :
		sys.stderr.write('Problem with API URL - Is it entered correctly?\nTerminating.\n')
		exit()
	except (requests.exceptions.Timeout) :
		sys.stderr.write('Request timed out.\nTerminating.\n')
		exit()
	# Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	# Check for errors sent back in the response
	check_for_response_errors(response_json)
	if(verbose) :
		printResponse('Register App \"%s\" (HTTP POST)' %APPNAME, request_json, response_json,URL)
	# on success, return the registered app's name
	try :
		return response_json['result']['app']
	except (TypeError,KeyError) :
		sys.stderr.write("\nApp Registration failed for \"%s\"\n" %APPNAME)
		sys.stderr.write("Did you issue a valid token?\n")
		return None

# get app info and write it in JSON format to the destfile given as argument
def getAppInfo(dest_filename) :
	global verbose
	TOKEN = env_overwrite.get('token',os.getenv('CG_TOKEN',''))
	APPNAME = env_overwrite.get('appname', os.getenv('CG_APP_NAME',''))
	URL = env_overwrite.get('url',os.getenv('CG_API_URL','https://sandbox.cigi.illinois.edu/home/rest/'))
	if not TOKEN :
		sys.stderr.write('No valid CG_TOKEN given\n')
		exit()
	if(verbose) :
		print "\nWriting info to \"" + dest_filename + "\""
	request_json = {
		'token' : TOKEN,
		'app' : APPNAME
	}
	# append resource (app) to API URL
	URL += "app"
	# Make a GET RESTful call
	try :
		request_ret = requests.get(URL, params=request_json,timeout=50,verify=False)
	except (requests.exceptions.ConnectionError,requests.exceptions.HTTPError,requests.exceptions.MissingSchema) :
		sys.stderr.write('Problem with API URL - Is it entered correctly?\nTerminating.\n')
		exit()
	except (requests.exceptions.Timeout) :
		sys.stderr.write('Request timed out.\nTerminating.\n')
		exit()
	# Get the response from the REST GET in JSON format (will be written to dest file)
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	if(verbose) :
		printResponse('Get app info for \"%s\" (HTTP GET)' %APPNAME, request_json, response_json,URL)
	# Dump the response JSON (the app info) into the destination file
	with open(dest_filename, 'w') as outfile :
		json.dump(response_json,outfile,indent=4,separators=(',', ': '))
		outfile.write('\n')
		outfile.close()
	# if successful, return True
	return True

# configure app with config JSON read in from a file
def configApp(config_filename) :
	global verbose
	USERNAME = env_overwrite.get('username',os.getenv('CG_USERNAME',''))
	TOKEN = env_overwrite.get('token',os.getenv('CG_TOKEN',''))
	APPNAME = env_overwrite.get('appname', os.getenv('CG_APP_NAME',''))
	URL = env_overwrite.get('url',os.getenv('CG_API_URL','https://sandbox.cigi.illinois.edu/home/rest/'))
	if not TOKEN :
		sys.stderr.write('No valid CG_TOKEN given\n')
		exit()
	if(verbose) :
		print "\nConfig File: \"" + config_filename + "\""
	f = open(config_filename)
	config = json.load(f)
	f.close()
	if not config :
		sys.stderr.write("Config File incorrectly formatted. (JSON)\n")
		return None
	request_json = {
		'token' : TOKEN,
		'app' : APPNAME,
		'config' : json.dumps(config)
	}
	# append resource (appconfig) to API URL
	URL += "appconfig"
	# Make RESTful POST call
	try : 
		request_ret = requests.post(URL,data=request_json,timeout=50,verify=False)
	except (requests.exceptions.ConnectionError,requests.exceptions.HTTPError,requests.exceptions.MissingSchema) :
		sys.stderr.write('Problem with API URL - Is it entered correctly?\nTerminating.\n')
		exit()
	except (requests.exceptions.Timeout) :
		sys.stderr.write('Request timed out.\nTerminating.\n')
		exit()
	# Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	if(verbose) :
		printResponse('Configure app  \"%s\" (HTTP POST)' %APPNAME, request_json, response_json,URL)
	# If correctly configured, return true
	return True

# get app config and write it in JSON format to the destfile given as an argument
def getAppConfig(dest_filename) :
	global verbose
	USERNAME = env_overwrite.get('username',os.getenv('CG_USERNAME',''))
	TOKEN = env_overwrite.get('token',os.getenv('CG_TOKEN',''))
	APPNAME = env_overwrite.get('appname', os.getenv('CG_APP_NAME',''))
	URL = env_overwrite.get('url',os.getenv('CG_API_URL','https://sandbox.cigi.illinois.edu/home/rest/'))
	if not TOKEN :
		sys.stderr.write('No valid CG_TOKEN given\n')
		exit()
	if(verbose) :
		print '\nWriting config to \"' + dest_filename + '\"'
	request_json = {
		'token' : TOKEN,
		'app' : APPNAME
	}
	# append resource (appconfig) to API URL
	URL += "appconfig"
	# Make a GET RESTful call
	try :
		request_ret = requests.get(URL, params=request_json,timeout=50, verify=False)
	except (requests.exceptions.ConnectionError,requests.exceptions.HTTPError,requests.exceptions.MissingSchema) :
		sys.stderr.write('Problem with API URL - Is it entered correctly?\nTerminating.\n')
		exit()
	except (requests.exceptions.Timeout) :
		sys.stderr.write('Request timed out.\nTerminating.\n')
		exit()
	# Get the response from the REST GET in JSON format (will be written to dest file)
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	if(verbose) :
		printResponse('Get app config for \"%s\" (HTTP GET)' %APPNAME, request_json, response_json,URL)
	# Dump the response JSON (the app config) into the destination file
	with open(dest_filename, 'w') as outfile :
		json.dump(response_json,outfile,indent=4,separators=(',',': '))
		outfile.write('\n')
		outfile.close()
	# If successful, return True
	return True

def main() :
	(parser,args) = parseArgs()
	action = os.getenv('CG_ACTION','None').lower()
	if action == 'register' :
		print registerApp()
	elif action == 'configure' :
		# check if config file was given or if it's invalid
		if args.configfile and os.path.exists(args.configfile) :
			configApp(args.configfile)
		else :
			sys.stderr.write('Config File Doesn\'t Exist\n')
			exit()
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

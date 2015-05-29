# Set of utilities to register/configure a CG application with REST calls
# as well as get info or configuration of applications registered
# requires a valid token either in bash environment or given at command line

from cg_extras import *
import json
import argparse
import requests
from requests import exceptions as rex
import os, sys, logging

# Used to disable InsecureRequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger('CG LOGGER')

# any argument used to overwrite environ vars is stored here;
# it is accessed throughout the code with the format:
# env_overwrite.get(<KEY>,<If KEY doesn't exist use environ or its default -- usually ''>)
# this allows for keys that don't exist / have no entries to always
# evaluate to False for error handling as well as keep the code succinct
env_overwrite = {}

# parses command line arguments (gives help if done incorrectly)
def parseArgs() :
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--debug",
		action="store_true",
		help='Allow debug info to be written to "cg_log.log"')
	parser.add_argument("-v", "--verbose",
		action="store_true",
		help='Allow non-debug info to be written to "cg_log.log"')
	parser.add_argument("--clearlog",
		action="store_true",
		help='Clear Log ("cg_log.log")')
	parser.add_argument("-act", "--action", 
		help="(REQUIRED) register/configure/getinfo/getconfig")
	parser.add_argument("-a", "--appname", 
		help="Set App Name")
	parser.add_argument("-r", "--url", 
		help="Set API url")
	parser.add_argument("-u", "--username", 
		help="Set Username")
	parser.add_argument("-t", "--token", 
		help="Set Token")
	parser.add_argument("-cf","--configfile", 
		help="For action 'configure' config file in JSON format")
	parser.add_argument("-df","--destfile", 
		help="For actions 'getinfo' and 'getconfig' "
			"destination file to write response")
	args = parser.parse_args()
	if not args.action :
		parser.print_help()
		exit()
	# Overwrite environ variables if command line args given
	for arg in vars(args) :
		if getattr(args,arg) :
			env_overwrite[arg] = getattr(args,arg)
	# Initialize Logger
	logger_initialize(args.verbose,args.debug,args.clearlog)
	# Append a terminating '/' if non-existent in API url
	if (env_overwrite.get('url','')
		and not env_overwrite.get('url','').endswith('/')
	   ) :
		env_overwrite['url'] += '/'
	elif (os.getenv('CG_API_URL','')
		and not os.getenv('CG_API_URL','').endswith('/')
	     ) :
		os.environ['CG_API_URL'] += '/'
	elif (not os.getenv('CG_API_URL','')) :
		reportError('CG_API_URL (API url for REST calls) '
				'not specified\n')
	if (not env_overwrite.get('appname',os.getenv('CG_APP_NAME',''))) :
		reportError('No CG_APP_NAME found or '
				'command line argument specified')
	return (parser,args,args.action.lower())

############################API CALLS##################################
# Register an app, must have a valid token
def registerApp(username,appname,url,token) :
	# Set up request JSON
	request_json = {
		'token' : token,
		'app' : appname,
		'longname' : 'Test app by %s' % username,
		'version' : 'V0.1',
		'info' : '<h2>%s</h2><p>Description of App (%s) '
			'Goes Here</p><p>'
			'Author: %s</p>' % (appname,appname,username),
		'author' : username,
		'tags' : 'test, app, %s' % username
	}
	# Append resource (app) to API url
	url += 'app'
	check_url_validity(url)
	# App register is a POST RESTful call
	# App configure is also a POST call
	# Get app information/configuration are GET calls
	try:
		request_ret = requests.post(url,
			data=request_json,
			timeout=50,
			verify=False)
	except (rex.ConnectionError,
		rex.HTTPError,
		rex.MissingSchema) :
		reportError('Problem with API url - '
				'Is it entered correctly?')
	except (rex.Timeout) :
		reportError('Request timed out.')
	# Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	# Check for errors sent back in the response
	check_for_response_errors(response_json)
	logResponse('Register App \"%s\" (HTTP POST)' %appname, 
		request_json, 
		response_json,
		url)
	# on success, return the registered app's name
	try :
		return response_json['result']['app']
	except (TypeError,KeyError) :
		reportError("\nApp Registration failed for \"%s\"\n"
			"Did you issue a valid token?" %appname)
		return None

# get app info and write it in JSON format to the destfile given as argument
def getAppInfo(username,appname,url,token,dest_filename) :
	logger.info('Writing info to "' + dest_filename + '"')
	request_json = {
		'token' : token,
		'app' : appname
	}
	# append resource (app) to API url
	url += "app"
	check_url_validity(url)
	# Make a GET RESTful call
	try :
		request_ret = requests.get(url, 
			params=request_json,
			timeout=50,
			verify=False)
	except (rex.ConnectionError,
		rex.HTTPError,
		rex.MissingSchema) :
		reportError('Problem with API url - '
				'Is it entered correctly?')
	except (rex.Timeout) :
		reportError('Request timed out.')
	# Get the response from the REST GET in JSON format (will be written to dest file)
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	logResponse('Get app info for \"%s\" (HTTP GET)' %appname, 
		request_json, 
		response_json,
		url)
	# Dump the response JSON (the app info) into the destination file
	with open(dest_filename, 'w') as outfile :
		json.dump(response_json,
			outfile,
			indent=4,
			separators=(',', ': ')
			)
		outfile.write('\n')
		outfile.close()
	# if successful, return True
	logger.info('"%s" info successfully '
			'written to "%s"' %(appname,dest_filename))
	return True

# configure app with config JSON read in from a file
def configApp(username,appname,url,token,config_filename) :
	logger.info('Config File: "' + config_filename + '"')
	f = open(config_filename)
	config = json.load(f)
	f.close()
	if not config :
		reportError("Config File incorrectly formatted. (JSON)")
		return None
	request_json = {
		'token' : token,
		'app' : appname,
		'config' : json.dumps(config)
	}
	# append resource (appconfig) to API url
	url += "appconfig"
	check_url_validity(url)
	# Make RESTful POST call
	try : 
		request_ret = requests.post(url,
			data=request_json,
			timeout=50,
			verify=False)
	except (rex.ConnectionError,
		rex.HTTPError,
		rex.MissingSchema) :
		reportError('Problem with API url - '
				'Is it entered correctly?')
	except (rex.Timeout) :
		reportError('Request timed out.')
	# Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	logResponse('Configure app  \"%s\" (HTTP POST)' %appname, 
		request_json, 
		response_json,
		url)
	# If correctly configured, return true
	logger.info('"%s" successfully configured from '
			'config file "%s"' %(appname,config_filename))
	return True

# get app config and write it in JSON format to the destfile given as an argument
def getAppConfig(username,appname,url,token,dest_filename) :
	logger.info('Writing config to "' + dest_filename + '"')
	request_json = {
		'token' : token,
		'app' : appname
	}
	# append resource (appconfig) to API url
	url += "appconfig"
	check_url_validity(url)
	# Make a GET RESTful call
	try :
		request_ret = requests.get(url, 
			params=request_json,
			timeout=50, 
			verify=False)
	except (rex.ConnectionError,
		rex.HTTPError,
		rex.MissingSchema) :
		reportError('Problem with API url - '
				'Is it entered correctly?')
	except (rex.Timeout) :
		reportError('Request timed out.')
	# Get the response from the REST GET in JSON format (will be written to dest file)
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	logResponse('Get app config for \"%s\" (HTTP GET)' %appname, 
		request_json, 
		response_json,
		url)
	# Dump the response JSON (the app config) into the destination file
	with open(dest_filename, 'w') as outfile :
		json.dump(response_json,
			outfile,
			indent=4,
			separators=(',',': ')
			)
		outfile.write('\n')
		outfile.close()
	# If successful, return True
	logger.info('"%s" config successfully'
			' written to "%s"' %(appname,dest_filename))
	return True

def main() :
	(parser,args,action) = parseArgs()
	# Acquire required information (either from env or overwritten while parsing)
	username = env_overwrite.get('username',
		os.getenv('CG_USERNAME',''))
	appname = env_overwrite.get('appname', 
		os.getenv('CG_APP_NAME',''))
	url = env_overwrite.get('url',
		os.getenv('CG_API_URL',
			'https://sandbox.cigi.illinois.edu/home/rest/')
		)
	token = env_overwrite.get('token',
		os.getenv('CG_TOKEN',''))
	if not token :
		reportError('No valid CG_TOKEN given\n')
	# Make appropriate call or print help if action is not valid
	if action == 'register' :
		logger.info('REGISTERING APP: "%s"' %appname)
		print registerApp(username,
			appname,
			url,
			token)
		logger.info('App "%s" successfully registered' %appname)
	elif action == 'configure' :
		# check if config file was given or if it's invalid
		if args.configfile and os.path.exists(args.configfile) :
			logger.info('CONFIGURING APP: "%s"' %appname)
			configApp(username,
				appname,
				url,
				token,
				args.configfile)
		else :
			reportError('Config File Doesn\'t Exist')
	elif action == 'getinfo' :
		# check if destination file was specified in command-line arguments
		logger.info('GETTING APP INFO FROM: "%s"' %appname)
		if args.destfile :
			getAppInfo(username,
				appname,
				url,
				token,
				args.destfile)
		elif not os.path.exists("getinfo_out.json") : # use this path as default
			getAppInfo(username,
				appname,
				url,
				token,
				"getinfo_out.json")
		else : # if default path exists, don't overwrite it, just print help & exit
			reportError('No destination file specified'
					' for get app info')
	elif action == 'getconfig' :
		# check if destination file was specified in command-line arguments
		logger.info('GETTING APP CONFIG FROM: "%s"' %appname)
		if args.destfile :
			getAppConfig(username,
				appname,
				url,
				token,
				args.destfile)
		elif not os.path.exists("getconfig_out.json") : # use this path as default
			getAppConfig(username,
				appname,
				url,
				token,
				"getconfig_out.json")
		else : # if default path exists, don't overwrite it, just print help & exit
			reportError('No destination file specified'
					' for get app config')
	else :
		parser.print_help()
		exit()

main()

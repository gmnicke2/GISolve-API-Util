# Set of utilities to issue/verify/revoke a CG token with REST calls
# requires a valid username and password either in bash environment or given at command line

from cg_extras import *
import json
import os, sys, logging
import argparse
import requests
from requests import exceptions
import getpass

# Used to disable InsecureRequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger('CG LOGGER')

# any argument used to overwrite environ vars is stored here;
# it is accessed throughout the code with the format:
# env_overwrite.get(<KEY>,<If KEY doesn't exist use environ or its default -- usually ''>)
# this allows for keys that don't exist / have no entries to always
# evaluate to False for error handling as well as keep the code succinct
env_overwrite = {}

#parses command line arguments (gives help if done incorrectly)
def parseArgs() :
	# parse command line arguments
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
	parser.add_argument("-p", "--password",
		action="store_true", 
		help="Choose to enter different Password")
	parser.add_argument("-act", "--action", 
		help="(REQUIRED) issue/verify/revoke Token")
	parser.add_argument("-r", "--url", 
		help="Set API URL")
	parser.add_argument("-c", "--clientid", 
		help="Set Client ID (For Verify Token)")
	parser.add_argument("-i", "--clientip", 
		help="Set Client IP (For Verify Token)")
	parser.add_argument("-u", "--username", 
		help="Set Username")
	parser.add_argument("-t", "--token", 
		help="For Verify/Revoke, Set Token")
	args = parser.parse_args()
	if not args.action :
		parser.print_help()
		exit()
	if args.password :
		env_overwrite['password'] = getpass.getpass('Enter CG Password: ')
	# overwrite environ variables if command line args given
	for arg in vars(args) :
		if getattr(args,arg) and (arg != 'debug' and arg != 'password'):
			env_overwrite[arg] = getattr(args,arg)
	#append a terminating '/' if non-existent in API URL
	if env_overwrite.get('url','') and not env_overwrite.get('url','').endswith('/') :
		env_overwrite['url'] += '/'
	elif os.getenv('CG_API_URL','') and not os.getenv('CG_API_URL','').endswith('/') :
		os.environ['CG_API_URL'] += '/'
	elif not os.getenv('CG_API_URL','') :
		reportError('CG_API_URL (API URL for REST calls)' 
				'not specified\n')
	# Initialize Logger
	logger_initialize(args.verbose,args.debug,args.clearlog)
	return (parser,args,args.action.lower())

############################API CALLS##################################
#issue token
def issueToken(USERNAME,PASSWORD,URL) :
	# A sample issue token request JSON
	request_json = {'username' : USERNAME,
		'password' : PASSWORD,
		'lifetime' : 15*3600,
		'binding' : 1
	}
	# Append resource ("token") to API URL
	URL += 'token'
	check_url_validity(URL)
	# Make RESTful POST call to "token" resource
	# Revoke would use DELETE, Verify would use PUT
	try :
		request_ret = requests.post(URL,
			data=request_json,
			timeout=50,
			verify=False)
	except (exceptions.ConnectionError, 
		exceptions.HTTPError, 
		exceptions.MissingSchema) :
		reportError('Problem with API URL - ' 
				'Is it entered correctly?\nTerminating.\n')
	except (exceptions.Timeout) :
		reportError('Request timed out.\nTerminating.\n')
	# Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	try :
		token = response_json['result']['token']
	except (TypeError,KeyError) :
		reportError("Token creation failed. "
				"(Check your arguments)\n")
	logResponse('Issue Token (HTTP POST)',
		request_json,
		response_json,
		URL)
	logger.info("Token %s created successfully" %token)
	return token

# verify token
def verifyToken(USERNAME,PASSWORD,URL,CLIENT_ID,CLIENT_IP,TOKEN) :
	request_json = {
		'consumer' : CLIENT_ID,
		'remote_addr' : CLIENT_IP,
		'token' : TOKEN,
		'username' : USERNAME
	}
	URL += 'token'
	check_url_validity(URL)
	request_length = str(len(json.dumps(request_json)))
	# Set HTTP Header
	headers = {'Content-Length' : request_length}
	try :
		request_ret = requests.put(URL,
			data=request_json,
			headers=headers,
			timeout=50,
			verify=False)
	except (exceptions.ConnectionError,
		exceptions.HTTPError,
		exceptions.MissingSchema) :
		reportError('Problem with API URL - '
				'Is it entered correctly?\nTerminating.\n')
	except (exceptions.Timeout) :
		reportError('Request timed out.\nTerminating.\n')
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	logResponse('Verify Token "%s" (HTTP PUT)' %(TOKEN),
		request_json,
		response_json,
		URL)
	if response_json['status'] == 'success' :
		return True
	else :
		return False

# revoke token
def revokeToken(USERNAME,PASSWORD,URL,TOKEN) :
	request_json = {
		'username' : USERNAME,
    		'password' : PASSWORD,
		'token' : TOKEN
	}
	URL += 'token'
	check_url_validity(URL)
	try :
		# Make RESTful DELETE call
		request_ret = requests.delete(URL,
			params=request_json,
			timeout=50,
			verify=False)
	except (exceptions.ConnectionError,
		exceptions.HTTPError,
		exceptions.MissingSchema) :
		reportError('Problem with API URL - '
				'Is it entered correctly?\nTerminating.\n')
	except (exceptions.Timeout) :
		reportError('Request timed out.\nTerminating.\n')
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	logResponse('Revoke Token %s (HTTP DELETE)' %TOKEN,
		request_json,
		response_json,
		URL)
	# Token was revoked successfully, so store empty string as environ token
	if response_json['status'] == 'success' :
		logger.info('Token %s successfully revoked' %TOKEN)
		return True
	else :
		logger.info('Token %s revoke FAILED' %TOKEN)
		return False

def main() :
	(parser,args,action) = parseArgs()
	# Retrieve necessary info (either from env or overwritten while parsing)
	USERNAME = env_overwrite.get('username', 
		os.getenv('CG_USERNAME',''))
	PASSWORD = env_overwrite.get('password', 
		os.getenv('CG_PASSWORD',''))
	URL = env_overwrite.get('url', 
		os.getenv('CG_API_URL', 
			'https://sandbox.cigi.illinois.edu/home/rest/')
		)
	# Make appropriate call or print help if action is not valid
	if action == "issue" :
		logger.info("ISSUING TOKEN")
		print issueToken(USERNAME,
			PASSWORD,
			URL)
	else :
		TOKEN = env_overwrite.get('token',
			os.getenv('CG_TOKEN',''))
		if not TOKEN :
			reportError('No valid CG_TOKEN given\n')
		if action == "verify" :
			CLIENT_ID = env_overwrite.get('clientid', 
				os.getenv('CG_CLIENT_ID',''))
			CLIENT_IP = env_overwrite.get('clientip', 
				os.getenv('CG_CLIENT_IP',''))
			logger.info('VERIFYING TOKEN "%s"' %TOKEN)
			verifyToken(USERNAME,
				PASSWORD,
				URL,
				CLIENT_ID,
				CLIENT_IP,
				TOKEN)
		elif action == "revoke" :
			logger.info('REVOKING TOKEN "%s"' %TOKEN)
			revokeToken(USERNAME,
				PASSWORD,
				URL,
				TOKEN)
		else :
			parser.print_help()
			exit()

main()

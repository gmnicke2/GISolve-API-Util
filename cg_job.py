#Set of utilities to launch, monitor, and get the output of a job
#Valid token and registered app are requireed
#Monitoring and getting the output of a job requires job ID 

from cg_extras import *
import json
import argparse
import requests
from requests import exceptions
import os, sys

# Used to disable InsecureRequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

# any argument used to overwrite environ vars is stored here;
# it is accessed throughout the code with the format:
# env_overwrite.get(<KEY>,<If KEY doesn't exist use environ or its default -- usually ''>)
# this allows for keys that don't exist / have no entries to always
# evaluate to False for error handling as well as keep the code succinct
env_overwrite = {}

# parses command line arguments (gives help if done incorrectly)
def parseArgs() :
	verbose = False
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose",
		action="store_true", 
		help="Print results/errors to stdout")
	parser.add_argument("-act", "--action", 
		help="(REQUIRED) launch/monitor/output")
	parser.add_argument("-r", "--url", 
		help="Set API URL")
	parser.add_argument("-j", "--jobname", 
		help="Set Job Name")
	parser.add_argument("-o", "--owner", 
		help="Set Job Owner")
	parser.add_argument("-cf","--configfile", 
		help="For action 'configure' config file in JSON format")
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
		sys.stderr.write('CG_API_URL (API URL for REST calls) '
				'not specified\n')
		exit()
	if not env_overwrite.get('jobname',os.getenv('CG_JOB_NAME','')) :
		sys.stderr.write('No CG_JOB_NAME found or '
				'command line argument specified\n')
		exit()
	return (parser,args,verbose)

############################API CALLS##################################
# Launch a job, must have valid token and appname
def launchJob(JOBNAME, APPNAME, OWNER, URL, TOKEN, config_filename, verbose) :
	if(verbose) :
		print "\nConfig File: \"" + config_filename + "\""
	f = open(config_filename)
	config = json.load(f)
	f.close()
	if not config :
		sys.stderr.write("Config File incorrectly formatted. (JSON)\n")
		return None

	# Set up request JSON
	request_json = {
		'token' : TOKEN,
		'name' : JOBNAME,
		'app' : APPNAME,
		'owner' : OWNER,
		'config' : json.dumps(config)
	}

	resource = "job"
	URL += resource
	check_url_validity(URL)

	# Job launch is a POST RESTful call
	try :
		request_ret = requests.post(URL,
			data=request_json,
			timeout=50,
			verify=False)
	except (exceptions.ConnectionError, 
		exceptions.HTTPError, 
		exceptions.MissingSchema) :
		sys.stderr.write('Problem with API URL - ' 
				'Is it entered correctly?\nTerminating.\n')
		exit()
	except (exceptions.Timeout) :
		sys.stderr.write('Request timed out.\nTerminating.\n')
		exit()

	#Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	check_for_response_errors(response_json)
	
	try :
		os.environ['CG_JOB_ID'] = response_json['result']['id']
	except (TypeError,KeyError) :
		sys.stderr.write("Job launch failed. (Check your arguments)\n")
		exit()
	if(verbose) :
		printResponse('Job launch (HTTP POST)',
			request_json,
			response_json,
			URL)
	return os.getenv('CG_JOB_ID','')


def main() :
	(parser,args,verbose) = parseArgs()
	# Acquire required information (either from env or overwritten while parsing)
	action = os.getenv('CG_ACTION','None').lower()
	USERNAME = env_overwrite.get('username',
		os.getenv('CG_USERNAME',''))
	APPNAME = env_overwrite.get('appname', 
		os.getenv('CG_APP_NAME',''))
	JOBNAME = env_overwrite.get('name', 
		os.getenv('CG_JOB_NAME',''))
	OWNER = env_overwrite.get('owner', 
		os.getenv('CG_OWNER_NAME',''))
	URL = env_overwrite.get('url',
		os.getenv('CG_API_URL',
			'https://sandbox.cigi.illinois.edu/home/rest/')
		)
	TOKEN = env_overwrite.get('token',
		os.getenv('CG_TOKEN',''))
	if not TOKEN :
		sys.stderr.write('No valid CG_TOKEN given\n')
		exit()
	# Make appropriate call or print help if action is not valid
	if args.configfile and os.path.exists(args.configfile) :
			launchJob(JOBNAME,
				APPNAME,
				OWNER,
				URL,
				TOKEN,
				args.configfile,
				verbose)

main()

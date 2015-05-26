import json
import os
import argparse
import requests

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
	print "Request Data (in JSON format): " + json.dumps(request_json,indent=4,separators=(',', ': ')) + "\n"
	print "Response (in JSON format): " + json.dumps(response_json,indent=4,separators=(',', ': ')) + "\n"

#parses command line arguments (gives help if done incorrectly)
def parseArgs() :
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--url", help="Set API URL")
	parser.add_argument("-t", "--token", help="Set Token")
	parser.add_argument("-j", "--jobname", help="Set Job Name")
	parser.add_argument("-a", "--appname", help="Set App Name")
	parser.add_argument("-o", "--owner", help="Set Owner Name")
	parser.add_argument("-act", "--action", help="launch/monitor/output Job")
	parser.add_argument("-cf", "--configfile", help="(For configure app) config JSON file path")
	parser.add_argument("-v", "--verbose",action="store_true", help="Print results/errors")
	args = parser.parse_args()
	os.environ['verbose'] = str(args.verbose)
	#print help and exit if not all required args supplied
	if not bool(args.url and args.token and args.action) :
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
	return (parser,args)

############################API CALLS##################################
#launches new job and returns job ID is submitted successfully
def launchJob(config_filename) :
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
		'name' : os.environ.get('jobname'),
		'app' : os.environ.get('appname'),
		'owner' : os.environ.get('owner'),
		'config' : json.dumps(config,indent=4,separators=(',',': '))
	}
	# append resource to API URL
	url = os.environ.get('url') 
	# Make RESTful POST call
	request_ret = requests.post(url,data=request_json,timeout=50,verify=False)
	# Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	return response_json['result']['id']
	
	#if(os.environ.get('verbose') == 'True') :
	#	print "??"
	# on success, return the new job's name
	#try :
	#	return response_json['result']['id']
	#except (TypeError,KeyError) :
	#	print "\nJob launch failed for \"%s\"" %os.environ.get('jobname')
	#	print "Did you issue a valid token?"
	#	return None
	

#monitors job by returning status of submitted job
def monitorJob() :
	return True

#returns output of job in the form of a URI to the output archive file of a finished job
def outputJob() :
	return True

def main() :
	parser_info = parseArgs()
	parser = parser_info[0]
	args = parser_info[1]
	action = os.environ.get('action').lower()
	if action == "launch" :
		if args.configfile and os.path.exists(args.configfile) :
			launchJob(args.configfile)
		else :
			print 'Config File Doesn\'t Exist'
	else :
		parser.print_help()
		exit()

main()
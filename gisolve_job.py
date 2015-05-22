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
	print "\URL: " + os.environ.get('url') + "\n"
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
	parser.add_argument("-act", "--action", help="issue/verify/revoke Token")
	parser.add_argument("-t", "--token", help="For Verify/Revoke, Set Token")
	parser.add_argument("-v", "--verbose",action="store_true", help="Print results/errors")
	args = parser.parse_args()
	os.environ['verbose'] = str(args.verbose)
	#print help and exit if not all args supplied
	if not bool(args.url and args.appname and args.clientid and args.clientip and args.username and args.action) :
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


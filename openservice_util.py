import argparse
import os
import json
import getpass

def storeinfo(key,val) :
	os.environ[key] = val

def getinfo(key) :
	return os.getenv(key,'')

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
	print "===================" + "\n"
	print "URL: " + getinfo('url') + "\n"
	print "Request: " + request_type + "\n"
	print "Request Data (in JSON format): " + json.dumps(request_json) + "\n"
	print "Response (in JSON format): " + json.dumps(response_json) + "\n"
	print "===================" + "\n"

def parseArgs() :
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--url", help="Set API URL")
	parser.add_argument("-a", "--appname", help="Set App Name")
	parser.add_argument("-c", "--clientid", help="Set Client ID")
	parser.add_argument("-i", "--clientip", help="Set Client IP")
	parser.add_argument("-u", "--username", help="Set Username")
	parser.add_argument("-p", "--password", help="Set Password")
	args = parser.parse_args()
	#print help and exit if no args supplied
	if not bool(args.url or args.appname or args.clientid or args.password or args.clientip or args.username) :
		parser.print_help()
		exit()
	#create environmental variables for existing and non-existing arguments
	#used for OpenService API calls (which make REST calls)
	for arg in vars(args) :
		if getattr(args,arg) :
			os.environ[arg] = getattr(args,arg)
		elif not arg == 'password':
			os.environ[arg] = raw_input ("Please enter "+arg+": ")
		else :
			os.environ[arg] = getpass.getpass("Please enter "+arg+": ")
	#append a terminating '/' if non-existent in API URL
	if not os.environ['url'].endswith('/') :
		os.environ['url'] += '/'
	return None

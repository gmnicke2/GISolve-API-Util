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
	print "Request Data (in JSON format): " + json.dumps(request_json) + "\n"
	print "Response (in JSON format): " + json.dumps(response_json) + "\n"

#parses command line arguments (gives help if done incorrectly)
def parseArgs() :
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--url", help="Set API URL")
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
	if not bool(args.url and args.clientid and args.clientip and args.username and args.action) :
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
#issue token
def issueToken() :
	#A sample issue token request JSON
	request_json = {'username' : os.environ.get('username'),
		'password' : os.getenv('password',os.environ.get('NCSAPW')),#get PW from bash variable NCSAPW if password not input through argument
		'lifetime' : 15*3600,
		'binding' : 1
	}
	#Need to append "token" to the API URL
	resource = "token"
	#Append resource ("token") to URL
	url = os.environ.get('url') + resource
	#Make RESTful POST call to "token" resource
	#Revoke would use DELETE, Verify would use PUT
	request_ret = requests.post(url,data=request_json,timeout=50,verify=False);
	#Get the response from the REST POST in JSON format
	response_json = request_ret.json
	try :
		os.environ['token'] = response_json['result']['token']
	except (TypeError,KeyError) :
		print "Token creation failed. (Check your arguments)"
		exit()
	if(os.environ['verbose'] == 'True') :
		printResponse('Issue Token (HTTP POST)',request_json,response_json)
	print 'Token Created: %s' %os.environ['token']
	return os.environ['token']

#verify token
def verifyToken() :
	url = os.environ.get('url')
	request_json = {
		'consumer' : os.environ.get('clientid'),
		'remote_addr' : os.environ.get('clientip'),
		'token' : os.environ.get('token'),
		'username' : os.environ.get('username'),
		'authrequest' : 'default'
	}
	resource = "token"
	url += resource
	#Set HTTP Header
	headers = {'Content-Length' : str(len(json.dumps(request_json)))}
	request_ret = requests.put(url,params=request_json,headers=headers,timeout=50,verify=False)
	response_json = request_ret.json
	if(os.environ['verbose'] == 'True') :
		printResponse('Verify Token (HTTP PUT)',request_json,response_json)
	if request_json['status'] == 'success' :
		return True
	else :
		return False

# revoke token
def revokeToken() :
	request_json = {
		'username' : os.environ.get('username'),
    		'password' : os.getenv('password',os.environ.get('NCSAPW')),
		'token' : os.environ.get('token')
	}
	resource = "token"
	url = os.environ.get('url') + resource
	request_ret = requests.delete(url,params=request_json,timeout=50,verify=False)
	response_json = request_ret.json
	if(os.environ.get('verbose') == 'True') :
		printResponse('Revoke Token \"%s\" (HTTP DELETE)' %os.environ.get('token'),request_json,response_json)
	# Token was revoked successfully, so store empty string as environ token
	if response_json['status'] == 'success' :
		os.environ['token'] = ''
		return True
	else :
		return False

def main() :
	parser = parseArgs()
	action = os.environ.get('action').lower()
	if action == "issue" :
		issueToken()
	else :
		try :
			token = os.environ.get('token') # check if accessing token give err
		except KeyError : # token wasn't given as an argument
			parser.print_help()
			exit()
		if action == "verify" :
			verifyToken()
		elif action == "revoke" :
			revokeToken()
		else :
			parser.print_help()
			exit()

main()

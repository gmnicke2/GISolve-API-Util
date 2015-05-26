import json
import os, sys
import argparse
import requests
import getpass

env_overwrite = {}

verbose = False

#prints information if -v or --verbose specified
def printResponse(request_type, request_json, response_json) :
	try :
		status = response_json['status']
	except KeyError :
		sys.stderr.write("\nResponse JSON failed to create.\n")
		exit()
	if(status != 'success') :
		sys.stderr.write(request_type + " Request Failed\n")
		exit()
	request_json['password'] = '*******'
	print "\nURL: " + env_overwrite.get('url',os.getenv('CG_API_URL','No URL Given')) + "\n"
	print "Request: " + request_type + "\n"
	print "Request Data (in JSON format): " + json.dumps(request_json,indent=4,separators=(',', ': ')) + "\n"
	print "Response (in JSON format): " + json.dumps(response_json,indent=4,separators=(',', ': ')) + "\n"

#parses command line arguments (gives help if done incorrectly)
def parseArgs() :
	global verbose
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose",action="store_true", help="Print results/errors")
	parser.add_argument("-r", "--url", help="Set API URL")
	parser.add_argument("-c", "--clientid", help="Set Client ID (For Verify Token)")
	parser.add_argument("-i", "--clientip", help="Set Client IP (For Verify Token)")
	parser.add_argument("-u", "--username", help="Set Username")
	parser.add_argument("-p", "--password", help="Choose to enter different Password",action="store_true")
	parser.add_argument("-act", "--action", help="(REQUIRED) issue/verify/revoke Token")
	parser.add_argument("-t", "--token", help="For Verify/Revoke, Set Token")
	args = parser.parse_args()
	if not args.action :
		parser.print_help()
		exit()
	os.environ['CG_ACTION'] = args.action
	if args.verbose :
		verbose = True
	if args.password :
		env_overwrite['password'] = getpass.getpass('Enter CG Password: ')
	#used for OpenService API calls (which make REST calls)
	for arg in vars(args) :
		if getattr(args,arg) and (arg != 'verbose' and arg != 'password'):
			env_overwrite[arg] = getattr(args,arg)
	#append a terminating '/' if non-existent in API URL
	if env_overwrite.get('url','') and not env_overwrite.get('url','').endswith('/') :
		env_overwrite['url'] += '/'
	elif os.getenv('CG_API_URL','') and not os.getenv('CG_API_URL','').endswith('/') :
		os.environ['CG_API_URL'] += '/'
	elif not os.getenv('CG_API_URL','') :
		sys.stderr.write('CG_API_URL (API URL for REST calls) not specified\n')
		exit()
	return (parser,args)

############################API CALLS##################################
#issue token
def issueToken() :
	global verbose
	USERNAME = env_overwrite.get('username', os.getenv('CG_USERNAME',''))
	PASSWORD = env_overwrite.get('password', os.getenv('CG_PASSWORD',''))
	URL = env_overwrite.get('url', os.getenv('CG_API_URL','https://sandbox.cigi.illinois.edu/home/rest/'))
	#A sample issue token request JSON
	request_json = {'username' : USERNAME,
		'password' : PASSWORD,
		'lifetime' : 15*3600,
		'binding' : 1
	}
	#Need to append "token" to the API URL
	resource = "token"
	#Append resource ("token") to URL
	URL += resource
	#Make RESTful POST call to "token" resource
	#Revoke would use DELETE, Verify would use PUT
	try :
		request_ret = requests.post(URL,data=request_json,timeout=50,verify=False);
	except (InsecureRequestWarning) :
		print ''
	except (requests.exceptions.ConnectionError,requests.exceptions.HTTPError,requests.exceptions.MissingSchema) :
		sys.stderr.write('Problem with API URL - Is it entered correctly?\nTerminating.\n')
		exit()
	except (requests.exceptions.Timeout) :
		sys.stderr.write('Request timed out.\nTerminating.\n')
		exit()
	#Get the response from the REST POST in JSON format
	response_json = request_ret.json()
	try :
		os.environ['CG_TOKEN'] = response_json['result']['token']
	except (TypeError,KeyError) :
		sys.stderr.write("Token creation failed. (Check your arguments)\n")
		exit()
	if(verbose) :
		printResponse('Issue Token (HTTP POST)',request_json,response_json)
	return os.getenv('CG_TOKEN','')

#verify token
def verifyToken() :
	global verbose
	URL = env_overwrite.get('url', os.getenv('CG_API_URL','https://sandbox.cigi.illinois.edu/home/rest/'))
	USERNAME = env_overwrite.get('username', os.getenv('CG_USERNAME',''))
	CLIENT_ID = env_overwrite.get('clientid', os.getenv('CG_CLIENT_ID',''))
	CLIENT_IP = env_overwrite.get('clientip', os.getenv('CG_CLIENT_IP',''))
	TOKEN = env_overwrite.get('clientip',os.getenv('CG_TOKEN',''))
	if not TOKEN :
		sys.stderr.write('No valid CG_TOKEN given\n')
		exit()
	request_json = {
		'consumer' : CLIENT_ID,
		'remote_addr' : CLIENT_IP,
		'token' : TOKEN,
		'username' : USERNAME,
		'authrequest' : 'default'
	}
	resource = "token"
	URL += resource
	#Set HTTP Header
	headers = {'Content-Length' : str(len(json.dumps(request_json)))}
	try :
		request_ret = requests.put(URL,params=request_json,headers=headers,timeout=50,verify=False)
	except (requests.exceptions.ConnectionError,requests.exceptions.HTTPError,requests.exceptions.MissingSchema) :
		sys.stderr.write('Problem with API URL - Is it entered correctly?\nTerminating.\n')
		exit()
	except (requests.exceptions.Timeout) :
		sys.stderr.write('Request timed out.\nTerminating.\n')
		exit()
	response_json = request_ret.json()
	if(verbose) :
		printResponse('Verify Token (HTTP PUT)',request_json,response_json)
	if request_json['status'] == 'success' :
		return True
	else :
		return False

# revoke token
def revokeToken() :
	global verbose
	USERNAME = env_overwrite.get('username',os.getenv('CG_USERNAME',''))
	PASSWORD = env_overwrite.get('password',os.getenv('CG_PASSWORD',''))
	TOKEN = env_overwrite.get('token',os.getenv('CG_TOKEN',''))
	URL = env_overwrite.get('url',os.getenv('CG_API_URL','https://sandbox.cigi.illinois.edu/home/rest/'))
	if not TOKEN :
		sys.stderr.write('No valid CG_TOKEN given\n')
		exit()
	request_json = {
		'username' : USERNAME,
    		'password' : PASSWORD,
		'token' : TOKEN
	}
	resource = "token"
	URL += resource
	try :
		request_ret = requests.delete(URL,params=request_json,timeout=50,verify=False)
	except (requests.exceptions.ConnectionError,requests.exceptions.HTTPError,requests.exceptions.MissingSchema) :
		sys.stderr.write('Problem with API URL - Is it entered correctly?\nTerminating.\n')
		exit()
	except (requests.exceptions.Timeout) :
		sys.stderr.write('Request timed out.\nTerminating.\n')
		exit()
	response_json = request_ret.json()
	if(verbose) :
		printResponse('Revoke Token \"%s\" (HTTP DELETE)' %os.environ.get('token'),request_json,response_json)
	# Token was revoked successfully, so store empty string as environ token
	if response_json['status'] == 'success' :
		os.environ['token'] = ''
		return True
	else :
		return False

def main() :
	parser_info = parseArgs()
	parser = parser_info[0]
	args = parser_info[1]
	action = os.environ.get('CG_ACTION','None').lower()
	if action == "issue" :
		print issueToken()
	else :
		if action == "verify" :
			verifyToken()
		elif action == "revoke" :
			revokeToken()
		else :
			parser.print_help()
			exit()

main()

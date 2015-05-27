import json
import sys

# prints information if -v or --verbose specified
def printResponse(request_type, request_json, response_json, url) :
	request_json['password'] = '*******'
	print "\nURL: " + url + "\n"
	print "Request: " + request_type + "\n"
	print "Request Data (in JSON format): " + json.dumps(request_json,indent=4,separators=(',', ': ')) + "\n"
	print "Response (in JSON format): " + json.dumps(response_json,indent=4,separators=(',', ': ')) + "\n"

# checks for errors in response and prints necessary info to stderr
def check_for_response_errors(response_json) :
	try :
		status = response_json['status']
	except KeyError :
		sys.stderr.write("\nResponse JSON failed to create.\n")
		exit()
	if(status != 'success') :
		sys.stderr.write("Request Failed\n")
		sys.stderr.write("Error %d: %s\n" %(response_json['result']['error_code'],response_json['result']['message']))
		exit()

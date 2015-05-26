import json
import os
import requests
import argparse

def main() :
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--url", help="Set API URL")
	args = parser.parse_args()
	if not bool(args.url) :
		parser.print_help()
		exit()
	if not args.url.endswith('/') :
		args.url += '/'
	request_ret = requests.get(args.url+'version',timeout=50,verify=False)
	response_json = request_ret.json
	try :
		print 'API Version: %s' %(response_json['version'])
	except (KeyError,TypeError) :
		print 'Version retrieval failed. (Check API Url)'

main()

import json
import requests
import argparse
import os

env_overwrite = {}

def main() :
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--url", help="Set API URL")
	args = parser.parse_args()
	if args.url :
		env_overwrite['url'] = args.url
	if env_overwrite.get('url','') and not env_overwrite.get('url','').endswith('/') :
		env_overwrite['url'] += '/'
	elif os.getenv('CG_API_URL', '') and not os.getenv('CG_API_URL','').endswith('/') :
		os.environ['CG_API_URL'] += '/'
	request_ret = requests.get(env_overwrite.get('url',os.getenv('CG_API_URL','https://sandbox.cigi.illinois.edu/home/rest/'))+'version',timeout=50,verify=False)
	response_json = request_ret.json()
	try :
		print 'API Version: %s' %(response_json['version'])
	except (KeyError,TypeError) :
		print 'Version retrieval failed. (Check API Url)'

main()

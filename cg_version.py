from cg_extras import *
import json
import requests
from requests import exceptions
import argparse
import os

# Used to disable InsecureRequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

env_overwrite = {}

def main() :
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--url", 
			help="Set API URL")
	args = parser.parse_args()
	if args.url :
		env_overwrite['url'] = args.url
	if (env_overwrite.get('url','') 
		and not env_overwrite.get('url','').endswith('/')
	   ) :
		env_overwrite['url'] += '/'
	elif (os.getenv('CG_API_URL', '') 
		and not os.getenv('CG_API_URL','').endswith('/')
	     ) :
		os.environ['CG_API_URL'] += '/'
	try :
		request_ret = requests.get(
			env_overwrite.get('url',
				os.getenv('CG_API_URL',
				'https://sandbox.cigi.illinois.edu/home/rest/')
			)+'version',
			timeout=50,
			verify=False)
	except (exceptions.ConnectionError, 
		exceptions.HTTPError, 
		exceptions.MissingSchema) :
		sys.stderr.write('Problem with API url - ' 
				'Is it entered correctly?\n')
		sys.exit(1)
	except (exceptions.Timeout) :
		sys.stderr.write('Request timed out.\n')
		sys.exit(1)
	response_json = request_ret.json()
	try :
		print 'API Version: %s' %(response_json['version'])
	except (KeyError,TypeError) :
		sys.stderr.write('Version retrieval failed. (Check API Url)\n')
		sys.exit(1)

main()

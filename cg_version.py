#!/usr/bin/env python

"""
Utility to print the current API version for GISolve

Print Version:
	./cg_version.py
"""

from cg_token import CGException, cg_rest, logger_initialize
import json
import requests
import argparse
import os, sys, logging

# This is used sed to disable InsecureRequestWarning.
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

def parse_args() :
    """Defines command line positional and optional arguments and checks
        for valid action input if present.
        
    Args: none

    Returns: A (tuple) containing the following:
        args (namespace) : used to overwrite env variables when necessary
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug",
    	action="store_true",
    	help='Allow debug info to be written to stderr')
    parser.add_argument("-e", "--endpoint",
    	default=os.getenv('CG_API',''),
    	help="Set API url")

    args = parser.parse_args()

    logger_initialize(args.debug)

    if not args.endpoint :
    	logger.error('CG_API (API url for REST calls) '
    				'not specified\n')
    	sys.exit(1)

    return args;

def main() :
	args = parse_args()

	url = args.endpoint.rstrip('/') + '/version'

	try :
		response = cg_rest('GET',url,timeout=50,verify=False)
		print response['version']

	except CGException as e :
		logger.error(e)
		sys.exit(1)

if(__name__ == ("__main__")) :
	main()

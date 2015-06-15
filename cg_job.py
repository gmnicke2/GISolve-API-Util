#!/usr/bin/env python

"""
Set of utilities to:
	Launch a Job with a configuration file in JSON format
	Monitor a Job and write the response JDON to a destination file
	Get the Job Output of a Job and print the output archive HTTP URL

All calls require a valid token either from CG_TOKEN or command line --token

Launch Job:
	# launch a job with name "My_Job" and store the ID to CG_JOB_ID env variables
	# requires a valid registered app name, either from CG_APP_NAME env variables
	# or with command line --appname
	export CG_JOB_ID=`./cg_job.py --jobname My_Job -cf <config file path>`

Monitor a Job:
	# monitor a job and specify destination file path for the monitor response
	./cg_job.py monitor -df <dest file path>

Get Job Output:
	# prints the job output to stdout
	./cg_job.py output
"""

from cg_token import CGException, cg_rest, logger_initialize
import json
import argparse
import requests
import os, sys, logging

# Used to disable InsecureRequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

def parse_args() :
    """Defines command line positional and optional arguments and checks
        for valid action input if present.
        
    Args: none

    Returns: A (tuple) containing the following:
        args (namespace) : used to overwrite env variables when necessary
        action (string) : for main to use as a switch for calls to perform
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug",
        action="store_true",
        help='Allow debug info to be written to stderr')
    parser.add_argument("-j", "--jobname",
		default=os.getenv('CG_JOB_NAME',''),
		help="Set Job Name")
    parser.add_argument("-jid", "--jobid",
		default=os.getenv('CG_JOB_ID',''),
		help="Set Job ID")
    parser.add_argument("-e", "--endpoint",
        default=os.getenv('CG_API',''),
        help="Set API url")
    parser.add_argument("-u", "--username",
        default=os.getenv('CG_USERNAME',''), 
        help="Set Username")
    parser.add_argument("-t", "--token", 
        default=os.getenv('CG_TOKEN',''),
        help="Set Token")
    parser.add_argument("-a", "--appname",
        default=os.getenv('CG_APP_NAME',''), 
        help="Set App Name")
    parser.add_argument("-cf","--configfile", 
        help="For Job Launch, configuration file in JSON format")
    parser.add_argument("-n","--ncpu",
    	type=int,
    	default=0,
    	help="For Job Launch specify # of CPUs > 0 to request")
    parser.add_argument("-wtime", "--walltime",
    	type=float,
    	default=0,
    	help="For Job Launch specify how long (minutes) for job to run")
    parser.add_argument("-df","--destfile", 
        help="For Job Monitoring, destination file path to write response")
    parser.add_argument("action", nargs='?', type=str, default='launch',
        help="launch/monitor/output")

    args = parser.parse_args()

    logger_initialize(args.debug)

    if not args.endpoint :
        logger.error('CG_API (API url for REST calls) '
                	'not specified\n')
        sys.exit(1)

    if args.action.lower() not in ['launch','monitor','output'] :
        logger.error('Invalid Action')
        sys.exit(1)

    return (args,args.action.lower())

def launch_job(endpoint, token, jobname, appname,
			owner, config_filename, computation) :
	""" Calls the Gateway Launch Job function and returns the Job ID

	Args:
		endpoint (string, URL): the REST endpoint
		token (string): a valid token to allow user to manipulate jobs
		jobname (string): name of the job to launch
		appname (string): name of the app to launch the job with
		owner (string): owner of the application
		config_filename(string, path): Path to job config in JSON format
		computation (dict, optional): Dictionary possibly containing:
			ncpu (int): number of CPUs to run the job owner
			walltime (long): how long the job should run, in minutes

	Returns:
		(string): Launched Job's ID

	Raise:
		Passes any exceptions raised in cg_rest.
	"""

	logger.debug('Job Config File: "' + config_filename + '"')

	f = open(config_filename)
	config = json.load(f)
	f.close()
	if not config :
		logger.error("Config File incorrectly formatted.")
		sys.exit(1)

	data = {
		'token' : token,
		'name' : jobname,
		'app' : appname,
		'owner' : owner,
		'config_filename' : config_filename,
		'computation' : computation
	}

	url = endpoint.rstrip('/') + '/job'

	response = cg_rest('POST', url, **data)

	return response['result']['id']
	
def monitor_job(endpoint, token, job_id, dest_filename) :
	"""Calls the Gateway Monitor Job function and writes
	the response to the destination file

	Args:
		endpoint (string, URL): the REST endpoint
		token (string): a valid token to allow user to manipulate jobs
		job_id (string): a valid Job ID to monitor
		dest_filename (string, path): path to file to write monitor response

	Returns:
		(void)

	Raises:
		Passes any exceptions raised in cg_rest
	"""

	logger.debug('Monitoring job id "%s" and writing'
				' response to "' + dest_filename + '"')

	params = {
		'token' : token,
		'id' : job_id
	}

	url = endpoint.rstrip('/') + '/job'

	response = cg_rest('GET', url, **params)

	# Dump the response JSON (the job monitor response) into destination file
	with open(dest_filename, 'w') as outfile :
		json.dump(response, outfile, indent=4, separators=(',', ': '))
		outfile.write('\n')
		outfile.close()

	logger.debug('Monitor of Job ID "%s" successfully '
				'written to "%s"' %(job_id,dest_filename))

def get_job_output(endpoint, token, job_id) :
	"""Calls the Gateway Monitor Job function and writes
	the response to the destination file

	Args:
		endpoint (string, URL): the REST endpoint
		token (string): a valid token to allow user to manipulate jobs
		job_id (string): a valid Job ID to get the output of

	Returns:
		(string, URL): HTTP URL of job output archive file

	Raises:
		Passes any exceptions raised in cg_rest
	"""
	logger.debug('Getting Job Output for Job ID "%s"' %job_id)

	params = {
		'token' : token,
		'id' : job_id
	}

	url = endpoint.rstrip('/') + '/joboutput'

	response = cg_rest('GET', url, **params)

	return response['result']['uri']

def main() :
	(args,action) = parse_args()

	if not args.token :
		logger.error('No valid CG_TOKEN given')
		sys.exit(1)

	try :
		if (action == 'launch') :
			if not (args.jobname) :
				logger.error('No valid Job Name provided')
				sys.exit(1)
			elif not (args.appname) :
				logger.error('No CG_APP_NAME found or '
							'command line argument specified')
				sys.exit(1)

			computation = {}

			if(args.ncpu != 0) :
				computation['ncpu'] = args.ncpu
			if(args.walltime != 0) :
				computation['walltime'] = args.walltime

			if args.configfile and os.path.exists(args.configfile) :
				print launch_job(args.endpoint, args.token, args.jobname,
						args.appname, args.username, args.configfile,
						computation)
			else :
				print ('No valid job configuration file given')

		elif (action == 'monitor') :
			if not (args.jobid) :
				logger.error('No CG_JOB_ID found or '
							'command line argument specified')
				sys.exit(1)

			if args.destfile :
				monitor_job(args.endpoint, args.token, 
							args.jobid, args.destfile)

			elif not os.path.exists("monitor_job_out.json") : # use as default
				monitor_job(args.endpoint, args.token,
							args.jobid, "monitor_job_out.json")

			else : # if default path exists, don't overwrite it
				logger.error('No destination file specified '
							'for job monitor output')
				sys.exit(1)

		else :
			if not (args.jobid) :
				logger.error('No CG_JOB_ID found or '
							'command line argument specified')
				sys.exit(1)

			print ("HTTP URL of job output archive file: ")
			print get_job_output(args.endpoint, args.token, args.jobid)


	except CGException as e :
		logger.error(e)
		sys.exit(1)

if(__name__ == ("__main__")) :
	main()
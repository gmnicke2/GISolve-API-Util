import json
import sys
import requests
import logging
import ipaddress
import urlparse

logger = logging.getLogger('CG LOGGER')

# Since logger.error() will be followed by a 
# logging.FileHandler.close() and an exit(),
# this function helps there be less syntax with more indirection
def reportError(message) :
	# Print to stderr and log error message and timestamp
	logger.error(message)
	# Close file associated with the file handler
	logger.handlers[1].close()
	# Exit with error
	sys.exit(1)

# Initializes logger (defines what is written where and if log file clears)
def logger_initialize(verbose,debug,clear) :
	logging_format = ("\n%(levelname)s - %(asctime)s\n%(message)s")
	formatter = logging.Formatter(logging_format)
	# Errors, Warnings, and Criticals always printed to stderr
	err_handler = logging.StreamHandler()
	err_handler.setLevel(logging.WARNING)
	err_handler.setFormatter(formatter)
	# Create file handler to pipe necessary logger levels to a log file
	# Clear the file if user specified --clearlog
	# Otherwise, append
	if clear :
		file_handler = logging.FileHandler('cg_log.log', 'w')
	else :
		file_handler = logging.FileHandler('cg_log.log')
	# If -d/--debug specified, log will contain ALL levels
	# If -v/--verbose specifiged, log will only contain up to INFO level
	# Otherwise, only ERROR, WARNING, CRITICAL in log
	# If debug and verbose specified, debug chosen
	if debug :
		level = logging.DEBUG
		file_handler.setLevel(level)
	elif verbose :
		level = logging.INFO
		file_handler.setLevel(level)
	else :
		level = logging.WARNING
		file_handler.setLevel(level)
	file_handler.setFormatter(formatter)
	logger.setLevel(level)
	logger.addHandler(err_handler)
	logger.addHandler(file_handler)

# prints information if -v or --verbose specified
def logResponse(request_type, request_json, response_json, url) :
	request_json['password'] = '*******'
	logger.debug("URL: " + url)
	logger.debug("Request: " + request_type)
	logger.debug("Request Data (in JSON format)"
		": " + json.dumps(request_json,indent=4,separators=(',',': ')))
	logger.debug("Response (in JSON format)"
		": " + json.dumps(response_json,indent=4,separators=(',',': ')))

# checks for errors in response and prints necessary info to stderr
def check_for_response_errors(response_json) :
	logger.debug("Checking for errors from server's response")
	try :
		status = response_json['status']
	except KeyError :
		reportError("\nResponse JSON failed to create.")
	logger.debug("Response JSON created successfully")
	if(status != 'success') :
		reportError('Request Failed\n'
			'Error %d: "%s"' 
			%(response_json['result']['error_code'],
			response_json['result']['message'])
			)
	logger.debug('Response JSON indicates "success"')

# makes sure URL passes some tests (mostly if dealing with url as an IP)
def check_url_validity(url) :
	logger.debug('Testing URL host name validity')
	host_name = urlparse.urlparse(url).hostname
	# make sure host name isn't localhost
	if host_name == 'localhost' :
		logger.error('"' + url + '" is an invalid URL')
		exit()
	# make sure host name isn't internal
	try :
		ip_addr = ipaddress.ip_address(unicode(host_name))
	except ValueError :
		pass
	else :
		if (ip_addr.is_loopback 
			or ip_addr.is_reserved
			or ip_addr.is_private
		   ) :
			logger.error('"' + url + '" is an invalid URL')
			exit()
	logger.debug('URL passed host name tests')


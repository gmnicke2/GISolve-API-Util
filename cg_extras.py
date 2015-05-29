import json
import sys
import requests
from requests import exceptions as rex
import logging
import ipaddress
import urlparse

def cg_rest(method, url, logger, **kwargs) :
    method = method.upper()
    try :
        request_ret = requests.request(method,url,**kwargs)
    except (rex.ConnectionError,
        rex.HTTPError,
        rex.MissingSchema) :
        logger.error('Problem with API url - '
                'Is it entered correctly?')
        sys.exit(1)
    except (rex.Timeout) :
        logger.error('Request timed out.')
        sys.exit(1)
    return request_ret.json()

# Initializes logger (defines what is written to stderr and if log file clears)
def logger_initialize(name,verbose,debug) :
    logger = logging.getLogger(name)
    logging_format = ("\n%(levelname)s - %(asctime)s\n%(message)s")
    formatter = logging.Formatter(logging_format)
    stream_handler = logging.StreamHandler()
    if debug :
        logger.setLevel(logging.DEBUG)
        stream_handler.setLevel(logging.DEBUG)
    elif verbose :
        logger.setLevel(logging.VERBOSE)
        stream_handler.setLevel(logging.VERBOSE)
    else :
        logger.setLevel(logging.WARNING)
        stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

# prints information if -v or --verbose specified
def logResponse(request_type, request_json, response_json, url,logger) :
    request_json['password'] = '*******'
    logger.debug("URL: " + url)
    logger.debug("Request: " + request_type)
    logger.debug("Request Data (in JSON format)"
        ": " + json.dumps(request_json,indent=4,separators=(',',': ')))
    logger.debug("Response (in JSON format)"
        ": " + json.dumps(response_json,indent=4,separators=(',',': ')))

# checks for errors in response and prints necessary info to stderr
def check_for_response_errors(response_json,logger) :
    logger.debug("Checking for errors from server's response")
    try :
        status = response_json['status']
    except KeyError :
        logger.error("\nResponse JSON failed to create.")
        sys.exit(1)
    logger.debug("Response JSON created successfully")
    if(status != 'success') :
        logger.error('Request Failed\n'
            'Error %d: "%s"' 
            %(response_json['result']['error_code'],
            response_json['result']['message'])
            )
        sys.exit(1)
    logger.debug('Response JSON indicates "success"')

# makes sure URL passes some tests (mostly if dealing with url as an IP)
def check_url_validity(url,logger) :
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


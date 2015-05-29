# Set of utilities to issue/verify/revoke a CG token with REST calls
# requires a valid username and password either in bash environment or given at command line

import json
import ipaddress, urlparse
import requests
import logging
import sys
from requests import exceptions as rex

# Used to disable InsecureRloggerequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

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
def check_url_validity(url) :
    logger.debug('Testing URL host name validity')
    host_name = urlparse.urlparse(url).hostname
    # make sure host name isn't localhost
    if host_name == 'localhost' :
        logger.error('"' + url + '" is an invalid URL')
        sys.exit(1)
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
            sys.exit(1)
    logger.debug('URL passed host name tests')

def cg_rest(method, url, **kwargs) :
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

#issue token
def issueToken(username,password,url) :
    # A sample issue token request JSON
    request_json = {'username' : username,
        'password' : password,
        'lifetime' : 15*3600,
        'binding' : 1
    }
    url += 'token'
    check_url_validity(url)
    response_json = cg_rest('POST',
        url,
        data=request_json,
        timeout=50,
        verify=False)
    check_for_response_errors(response_json)
    try :
        token = response_json['result']['token']
    except (TypeError,KeyError) :
        logger.error("Token creation failed. "
                "(Check your arguments)\n")
        sys.exit(1)
    logResponse('Issue Token (HTTP POST)',
        request_json,
        response_json,
        url)
    logger.info("Token %s created successfully" %token)
    return token

# verify token
def verifyToken(username,password,url,client_id,client_ip,token) :
    request_json = {
        'consumer' : client_id,
        'remote_addr' : client_ip,
        'token' : token,
        'username' : username
    }
    url += 'token'
    check_url_validity(url)
    request_length = str(len(json.dumps(request_json)))
    headers = {'Content-Length' : request_length}
    response_json = cg_rest('PUT',
        url,
        data=request_json,
        headers=headers,
        timeout=50,
        verify=False)
    check_for_response_errors(response_json)
    logResponse('Verify Token "%s" (HTTP PUT)' %(token),
        request_json,
        response_json,
        url)
    return True

# revoke token
def revokeToken(username,password,url,token) :
    request_json = {
        'username' : username,
        'password' : password,
        'token' : token
    }
    url += 'token'
    check_url_validity(url)
    response_json = cg_rest('DELETE',
        url,
        params=request_json,
        timeout=50,
        verify=False)
    check_for_response_errors(response_json)
    logResponse('Revoke Token %s (HTTP DELETE)' %token,
        request_json,
        response_json,
        url)
    return True 

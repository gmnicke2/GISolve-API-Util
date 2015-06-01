#!/usr/bin/env python

"""
Set of utilities to issue/verify/revoke a CG token with REST calls
Requires valid username and password either in bash environment or
given at the command line.

Issue Token:
    Token can be easily created (and stored to env) with the folloing:
    
        # create token using CG_USERNAME, CG_PASSWORD, and CG_API env variables
        ./cg_token.py

        # create token specifying all the parameters on command line
        ./cg_token.py --username <login> --password <password> --endpoint <url>

        # create token using CG_USERNAME, CG_API, but prompt for password
        ./cg_token.py --password -

        # add token to environmental variables
        export CG_TOKEN=`./cg_token.py`

        # add token to environmental variable, specify extra parameters
        export CG_TOKEN=`./cg_token.py --username <login> --endpoint <newurl>`

Verify or Revoke Token:
    Verifying or Revoking requires the positional 'verify' or 'revoke' 
    command line argument.

    User can still override env variables with command-line arguments.

    Uses CG_API, and CG_TOKEN env variables for both.
    Verify uses CG_CLIENT_ID and CG_CLIENT_IP for consumer ID & user client IP,
    Revoke uses CG_USERNAME and CG_PASSWORD for security purposes :

        # Verify token, overriding CG_CLIENT_ID and CG_CLIENT_IP with command line
        # (Upon success, it will print the remaining lifetime of the token in seconds)
        ./cg_token.py verify --clientid <ID> --clientip <IP>

        # Revoke token, overriding CG_TOKEN with command line
        ./cg_token.py revoke --token <token>

Print debug info to stderr:
    Append the flag "--debug" or "-d" :
        ./cg_token.py --debug
"""
import sys, os, getpass
import json
import logging
import requests
import argparse
from requests import exceptions as rex

# Used to disable InsecureRloggerequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

class CGException(Exception) :

    def __init__(self, result) :
        self.message = result['message']
        self.error_code = result['error_code']

def logger_initialize(debug) :
    """Initializes the format and level for the logger"""

    _format = ("%(levelname)s - %(asctime)s\n%(message)s\n")
    if debug :
        logging.basicConfig(format=_format,
                            level=logging.DEBUG)
    else :
        logging.basicConfig(format=_format,
                            level=logging.WARNING)

def log_response(method, url, response, **kwargs) :
    """Logs request and response when in debug mode"""

    request = kwargs.get('data',kwargs.get('params',None))
    if request.get('password', '') :
        request['password'] = '*******'
    logger.debug("URL: " + url)
    logger.debug("Request: " + method)
    logger.debug("Request Data (in JSON format)"
        ": " + json.dumps(request,indent=4,separators=(',',': ')))
    logger.debug("Response (in JSON format)"
        ": " + json.dumps(response,indent=4,separators=(',',': ')))

def parseArgs() :
    """Defines command line positional and optional arguments and checks
        for valid action input if present. Additionally prompts with getpass
        if user specifies "--password -" to override CG_PASSWORD
    
    Args: none

    Returns: A (tuple) containing the following:
        parser (object) : used to print help when necessary
        args (namespace) : used to overwrite env variables when necessary
        action (string) : for main to use as a switch for calls to perform
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug",
        action="store_true",
        help='Allow debug info to be written to stderr')
    parser.add_argument("-e", "--endpoint", 
        help="Set API url")
    parser.add_argument("-p", "--password",
        help="Set password. '-' for secure prompting")
    parser.add_argument("-u", "--username", 
        help="Set Username")
    parser.add_argument("-t", "--token", 
        help="Set Token for Verify/Revoke")
    parser.add_argument("-c", "--clientid",
        help="Set Client ID for Verify")
    parser.add_argument("-i", "--clientip",
        help="Set Client IP for Verify")
    parser.add_argument("action", nargs='?', type=str,
        help='issue/verify/revoke')

    args = parser.parse_args()

    logger_initialize(args.debug)

    if args.password and args.password == '-' : 
        args.password = getpass.getpass("Enter desired CG Password: ")

    if (not args.endpoint and not os.getenv('CG_API','')) :
        logger.error('CG_API (API url for REST calls) '
                'not specified\n')
        sys.exit(1)

    if (not args.action) :
        action = "issue"
    else :
        action = args.action.lower()
    if action not in ['issue','verify','revoke'] :
        logger.error('Incorrect Action')
        sys.exit(1) 

    return (parser,args,action)

def cg_rest(method, endpoint, **kwargs) :
    """Calls the CG REST endpoint passing keyword arguments given.

    'cg_rest' provides a basic wrapper around the HTTP request to
    the rest endoing and attempts to provide informative error
    messages when errors occur. Exceptions are passed to the calling
    function for final resolution.
    
        cg_rest('POST', <url>, data=request)
        
            or with additional HTTP arguments
        
        cg_rest('POST', <url>, headers=headers, data=request)

    Args:
        method (str): the HTTP method that will be called
        endpoint (str, URL): the REST endpoint
        kwargs (optional): data/params json dicts, header dicts, etc.

    Returns:
        (dict): decodes the response and returns it as a dictionary
    
    Raises:
        Raises CGException when the gateway server return an error status.
        Other exceptions may be raised based errors with the HTTP request
        and response. See documentation of Python's request module for
        a complete list.
    """ 
    try :
        r = requests.request(method.upper(),endpoint,timeout=50, verify=False,
                            **kwargs)
        r.raise_for_status()
    
    except (rex.ConnectionError, rex.HTTPError, rex.MissingSchema) as e :
        logger.debug("Problem with API endpoint '%s', "
                "is it entered correctly?" %endpoint)
        raise

    except (rex.Timeout) as e :
        logger.debug('Request timed out, the service may be '
                    'temporarily unavailable')
        raise

    response = r.json()
    log_response(method, endpoint, response, **kwargs)

    # If status is not provided, default to error.
    if response.get('status','error') == 'error' :
        logger.debug("Call fails with '%s'" %response['result']['message'])
        raise CGException(response['result'])

    return response

#issue token
def issueToken(endpoint, username, password, lifetime=15*3600, binding=1) :
    """Calls the Gateway issueToken function and returns token.

    Args:
        endpoint (string, URL): the REST endpoint
        username (string): the user's login
        password (string): the user's password
        lifetime (int): the lifetime of a token in seconds
        binding (int): 1 if user wants token to be bound to user IP
                       0 else

    Returns:
        (string): Open Service API token

    Raises:
        Passes any exceptions raised in cg_rest.
    """

    request = {
        'username' : username,
        'password' : password,
        'lifetime' : lifetime,
        'binding' : binding
    }

    url = endpoint.rstrip('/') + '/token'
    logger.debug('Issuing token from %s' %url)

    response = cg_rest('POST', url, data=request)

    return response['result']['token']

def verifyToken(endpoint, client_id, client_ip, token) :
    """Calls the Gateway verifyToken function, returns remaining token lifetime.

    Args:
        endpoint(string, URL): the REST endpoint
        client_id (string): Consumer ID
        client_ip (string): User Client's IP Address
        token (string): Token to verify
    
    Returns:
        (int): Remaining lifetime of token (in seconds)

    Raises:
        Passes any exceptions raised in cg_rest.
    """

    request = {
        'consumer' : client_id,
        'remote_addr' : client_ip,
        'token' : token
    }

    url = endpoint.rstrip('/') + '/token'
    logger.debug("Verifying token '%s' from '%s'" %(token,url))
    request_length = str(len(json.dumps(request)))
    headers = {'Content-Length' : request_length}

    response = cg_rest('PUT', url, headers=headers, data=request) 

    return response['result']['lifetime']

def revokeToken(endpoint, username, password, token) :
    """Calls the Gateway revokeToken function

    Args:
        endpoint (string, URL): the REST endpoint
        username (string): the user's login
        password (string): the user's password
        token (string): The token to be revoked

    Returns: void

    Raises:
        Passes any exceptions raised in cg_rest.
    """

    request= {
        'username' : username,
        'password' : password,
        'token' : token
    }

    url = endpoint.rstrip('/') + "/token"
    logger.debug("Revoking token '%s' from '%s'" %(token,url))

    response = cg_rest('DELETE', url, params=request)

def main() :
    (parser, args, action) = parseArgs()
    username = args.username if args.username else os.getenv('CG_USERNAME','')
    password = args.password if args.password else os.getenv('CG_PASSWORD','')
    endpoint = args.endpoint if args.endpoint else os.getenv('CG_API','')

    try :
        if action == "issue" :
            print issueToken(endpoint, username, password)

        else :
            token = args.token if args.token else os.getenv('CG_TOKEN','')
            if not token :
                logger.error('No valid CG_TOKEN given')
                sys.exit(1)

            if action == "verify" :
                client_id = args.clientid if args.clientid else os.getenv(''
                                                           'CG_CLIENT_ID','')
                client_ip = args.clientip if args.clientip else os.getenv(''
                                                        'CG_CLIENT_IP','')
                print verifyToken(endpoint, client_id, client_ip, token)

            else :
                revokeToken(endpoint, username, password, token)

    except CGException as e :
        logger.error('Error %d: %s' %(e.error_code, e.message))
        sys.exit(1)

if __name__ == '__main__' :
    main()

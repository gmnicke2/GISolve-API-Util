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

        # Verify token, overriding CG_CLIENT_ID and CG_CLIENT_IP with command
        # line (Upon success, it will print the remaining lifetime of the token
        # in seconds)
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

# This is used sed to disable InsecureRequestWarning.
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

class CGException(Exception) :

    def __init__(self, result) :
        self.message = result['message']
        self.error_code = result['error_code']
    def __str__(self) :
        return ("Error %d: %s" %(self.error_code, self.message))

def logger_initialize(debug) :
    """Initializes the format and level for the logger"""

    _format = ("%(levelname)s - %(asctime)s\n%(message)s\n")
    if debug :
        logging.basicConfig(format=_format,
                            level=logging.DEBUG)
    else :
        logging.basicConfig(format=_format,
                            level=logging.WARNING)

def log_response(method, url, response, request) :
    """Logs request and response when in debug mode"""
    
    iBREAKJENKINSf request.get('password', '') :
        request['password'] = '*******'
    logger.debug("URL: " + url)
    logger.debug("Request: " + method)
    logger.debug("Request Data (in JSON format)"
        ": " + json.dumps(request,indent=4,separators=(',',': ')))
    logger.debug("Response (in JSON format)"
        ": " + json.dumps(response,indent=4,separators=(',',': ')))

def parse_args() :
    """Defines command line positional and optional arguments and checks
        for valid action input if present. Additionally prompts with getpass
        if user specifies "--password -" to override CG_PASSWORD
    
    Args: none

    Returns: A (tuple) containing the following:
        args (namespace) : used to overwrite env variables when necessary
        action (string) : for main to use as a switch for calls to perform
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug",
        action="store_true",
        help='Allow debug info to be written to stderr')
    parser.add_argument("-e", "--endpoint",
        default=os.getenv('CG_API',''), 
        help="Set API url")
    parser.add_argument("-p", "--password",
        default=os.getenv('CG_PASSWORD',''),
        help="Set password. '-' for secure prompting")
    parser.add_argument("-u", "--username", 
        default=os.getenv('CG_USERNAME',''),
        help="Set Username")
    parser.add_argument("-t", "--token", 
        default=os.getenv('CG_TOKEN',''),
        help="Set Token for Verify/Revoke")
    parser.add_argument("-l", "--lifetime",
        type=long,
        default=43200,
        help="Set Lifetime for Token Issue in seconds"
            ". minimum=3600 (1hr), maximum=12*3600 (12hr)")
    parser.add_argument("-b", "--binding",
        type=int,
        default=1,
        help="1: Bind with IP Address, 0: Don't Bind")
    parser.add_argument("-c", "--clientid",
        default=os.getenv('CG_CLIENT_ID',''),
        help="Set Client ID for Verify")
    parser.add_argument("-i", "--clientip",
        default=os.getenv('CG_CLIENT_IP',''),
        help="Set Client IP for Verify")
    parser.add_argument("action", nargs='?', type=str, default='issue',
        help='issue/verify/revoke')

    args = parser.parse_args()

    logger_initialize(args.debug)

    if args.password and args.password == '-' : 
        args.password = getpass.getpass("Enter desired CG Password: ")

    if not args.endpoint :    
        logger.error('CG_API (API url for REST calls) '
                'not specified\n')
        sys.exit(1)

    if args.action.lower() not in ['issue','verify','revoke'] :
        logger.error('Invalid Action')
        sys.exit(1) 

    return (args,args.action.lower())

def cg_rest(method, endpoint, headers={}, **kwargs) :
    """Calls the CG REST endpoint passing keyword arguments given.

    'cg_rest' provides a basic wrapper around the HTTP request to
    the rest endpoint, and attempts to provide informative error
    messages when errors occur. Exceptions are passed to the calling
    function for final resolution.
    
        cg_rest('POST', <url>, headers=<HTTP headers dict>, username=<username>, 
password=<password>, ...)
        
            or with a previously constructed data/params dict
        
        cg_rest('POST', <url>, headers=headers, **data/params)

            or with no header necessary

        cg_rest('POST', <url>, **data/params)

    Args:
        method (str): the HTTP method that will be called
        endpoint (str, URL): the REST endpoint
        headers (dict, optional): HTTP headers
        kwargs (optional): common keywords include username, password, etc.

    Returns:
        (dict): decodes the response and returns it as a dictionary
    
    Raises:
        Raises CGException when the gateway server return an error status.
        Other exceptions may be raised based errors with the HTTP request
        and response. See documentation of Python's request module for
        a complete list.
    """ 
    try :
        if method.upper() == 'POST' or method.upper() == 'PUT' :
            r = requests.request(method.upper(), endpoint, timeout=50, 
                                verify=False, headers=headers, data=kwargs)
        else : # Must be 'GET' or 'DELETE'
            r = requests.request(method.upper(), endpoint, timeout=50,
                                verify=False, headers=headers, params=kwargs)
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
    log_response(method, endpoint, response, kwargs)

    # If status is not provided, default to error.
    if response.get('status','') and response.get('status','') == 'error' :
        logger.debug("Call fails with '%s'" %response['result']['message'])
        raise CGException(response['result'])

    return response

def issue_token(endpoint, username, password, lifetime, binding) :
    """Calls the Gateway issueToken function and returns token.

    Args:
        endpoint (string, URL): the REST endpoint
        username (string): the user's login
        password (string): the user's password
        lifetime (int): the lifetime of a token in seconds 
                        (3600 <= lifetime <= 12*3600)
        binding (int): 1 if user wants token to be bound to user IP
                       0 else

    Returns:
        (string): Open Service API token

    Raises:
        Passes any exceptions raised in cg_rest.
    """

    data = {
        'username' : username,
        'password' : password,
        'lifetime' : lifetime,
        'binding' : binding
    }

    url = endpoint.rstrip('/') + '/token'
    logger.debug('Issuing token from %s' %url)

    response = cg_rest('POST', url, **data)

    return response['result']['token']

def verify_token(endpoint, username, token, client_id, client_ip) :
    """Calls the Gateway verifyToken function, returns remaining token lifetime.

    Args:
        endpoint(string, URL): the REST endpoint
        username (string):     
        token (string): Token to verify
        client_id (string): Consumer ID
        client_ip (string): User Client's IP Address

    Returns:
        (int): Remaining lifetime of token (in seconds)

    Raises:
        Passes any exceptions raised in cg_rest.
    """

    data = {
        'token' : token,
        'consumer' : client_id,
        'remote_addr' : client_ip,
        'username' : username
    }

    url = endpoint.rstrip('/') + '/token'
    logger.debug("Verifying token '%s' from '%s'" %(token,url))
    data_length = str(len(json.dumps(data)))
    headers = {'Content-Length' : data_length}

    response = cg_rest('PUT', url, headers=headers, **data) 

    return response['result']['lifetime']

def revoke_token(endpoint, username, password, token) :
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

    params = {
        'token' : token,
        'username' : username,
        'password' : password,
    }
    url = endpoint.rstrip('/') + "/token"
    logger.debug("Revoking token '%s' from '%s'" %(token,url))

    response = cg_rest('DELETE', url, **params)

def main() :
    (args, action) = parse_args()
    
    try :
        if action == "issue" :
            if ((args.binding not in [0,1]) or 
                not (3600<=args.lifetime<=43200)) :
                logger.error("Lifetime must be between 3600 and 43200,"
                                "\nBinding must be 0 or 1")
                sys.exit(1)

            print issue_token(args.endpoint, args.username, args.password,
                                args.lifetime, args.binding)

        else :
            if not args.token :
                logger.error('No valid CG_TOKEN given')
                sys.exit(1)

            if action == "verify" :
                print verify_token(args.endpoint, args.username, 
                                    args.token, args.clientid, args.clientip)

            else :
                revoke_token(args.endpoint, args.username, 
                            args.password, args.token)

    except CGException as e :
        logger.error(e)
        sys.exit(1)

if __name__ == '__main__' :
    main()

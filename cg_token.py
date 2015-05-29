# Set of utilities to issue/verify/revoke a CG token with REST calls
# requires a valid username and password either in bash environment or given at command line

from cg_extras import *
import json
import os, sys, logging
import argparse
import requests
from requests import exceptions as rex
import getpass

# Used to disable InsecureRequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

# any argument used to overwrite environ vars is stored here;
# it is accessed throughout the code with the format:
# env_overwrite.get(<KEY>,<If KEY doesn't exist use environ or its default -- usually ''>)
# this allows for keys that don't exist / have no entries to always
# evaluate to False for error handling as well as keep the code succinct
env_overwrite = {}

#parses command line arguments (gives help if done incorrectly)
def parseArgs() :
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug",
        action="store_true",
        help='Allow debug info to be written to "cg_log.log"')
    parser.add_argument("-v", "--verbose",
        action="store_true",
        help='Allow non-debug info to be written to "cg_log.log"')
    parser.add_argument("-p", "--password",
        action="store_true", 
        help="Choose to enter different Password")
    parser.add_argument("-act", "--action", 
        help="(REQUIRED) issue/verify/revoke Token")
    parser.add_argument("-r", "--url", 
        help="Set API url")
    parser.add_argument("-c", "--clientid", 
        help="Set Client ID (For Verify Token)")
    parser.add_argument("-i", "--clientip", 
        help="Set Client IP (For Verify Token)")
    parser.add_argument("-u", "--username", 
        help="Set Username")
    parser.add_argument("-t", "--token",
        help="For Verify/Revoke, Set Token")
    parser.add_argument("action",
        type=str,
        help="issue/verify/revoke")
    args = parser.parse_args()
    if not args.action :
        parser.print_help()
        exit()
    if args.password :
        env_overwrite['password'] = getpass.getpass('Enter CG Password: ')
    # overwrite environ variables if command line args given
    for arg in vars(args) :
        if getattr(args,arg) :
            env_overwrite[arg] = getattr(args,arg)
    # Initialize Logger
    logger = logger_initialize(__name__,args.verbose,args.debug)
    # Append a terminating '/' if non-existent in API url
    if (env_overwrite.get('url','') 
        and not env_overwrite.get('url','').endswith('/') 
       ) :
        env_overwrite['url'] += '/'
    elif (os.getenv('CG_API_URL','') 
        and not os.getenv('CG_API_URL','').endswith('/')
         ) :
        os.environ['CG_API_URL'] += '/'
    elif (not os.getenv('CG_API_URL','')) :
        logger.error('CG_API_URL (API url for REST calls)' 
                'not specified')
        sys.exit(1)
    return (parser,args,args.action.lower(),logger)

############################API CALLS##################################
#issue token
def issueToken(username,password,url,logger) :
    # A sample issue token request JSON
    request_json = {'username' : username,
        'password' : password,
        'lifetime' : 15*3600,
        'binding' : 1
    }
    # Append resource ("token") to API url
    url += 'token'
    check_url_validity(url,logger)
    # Make RESTful POST call to "token" resource
    # Revoke would use DELETE, Verify would use PUT
    response_json = cg_rest('POST',
        url,
        logger,
        data=request_json,
        timeout=50,
        verify=False)
    check_for_response_errors(response_json,logger)
    try :
        token = response_json['result']['token']
    except (TypeError,KeyError) :
        logger.error("Token creation failed. "
                "(Check your arguments)\n")
        sys.exit(1)
    logResponse('Issue Token (HTTP POST)',
        request_json,
        response_json,
        url,
        logger)
    logger.info("Token %s created successfully" %token)
    return token

# verify token
def verifyToken(username,password,url,client_id,client_ip,token,logger) :
    request_json = {
        'consumer' : client_id,
        'remote_addr' : client_ip,
        'token' : token,
        'username' : username
    }
    url += 'token'
    check_url_validity(url,logger)
    request_length = str(len(json.dumps(request_json)))
    # Set HTTP Header
    headers = {'Content-Length' : request_length}
    # Make RESTful PUT call
    response_json = cg_rest('PUT',
        url,
        logger,
        data=request_json,
        headers=headers,
        timeout=50,
        verify=False)
    check_for_response_errors(response_json,logger)
    logResponse('Verify Token "%s" (HTTP PUT)' %(token),
        request_json,
        response_json,
        url,
        logger)
    if response_json['status'] == 'success' :
        return True
    else :
        return False

# revoke token
def revokeToken(username,password,url,token,logger) :
    request_json = {
        'username' : username,
        'password' : password,
        'token' : token
    }
    url += 'token'
    check_url_validity(url,logger)
    response_json = cg_rest('DELETE',
        url,
        logger,
        params=request_json,
        timeout=50,
        verify=False)
    check_for_response_errors(response_json,logger)
    logResponse('Revoke Token %s (HTTP DELETE)' %token,
        request_json,
        response_json,
        url,
        logger)
    # Token was revoked successfully, so store empty string as environ token
    if response_json['status'] == 'success' :
        logger.info('Token %s successfully revoked' %token)
        return True
    else :
        logger.info('Token %s revoke FAILED' %token)
        return False

def main() :
    (parser,args,action,logger) = parseArgs()
    # Retrieve necessary info (either from env or overwritten while parsing)
    username = env_overwrite.get('username', 
        os.getenv('CG_USERNAME',''))
    password = env_overwrite.get('password', 
        os.getenv('CG_PASSWORD',''))
    url = env_overwrite.get('url', 
        os.getenv('CG_API_URL', 
            'https://sandbox.cigi.illinois.edu/home/rest/')
        )
    # Make appropriate call or print help if action is not valid
    if action == "issue" :
        logger.info("ISSUING TOKEN")
        print issueToken(username,
            password,
            url,
            logger)
    else :
        token = env_overwrite.get('token',
            os.getenv('CG_TOKEN',''))
        if not token :
            logger.error('No valid CG_TOKEN given')
            sys.exit(1)
        if action == "verify" :
            client_id = env_overwrite.get('clientid', 
                os.getenv('CG_CLIENT_ID',''))
            client_ip = env_overwrite.get('clientip', 
                os.getenv('CG_CLIENT_IP',''))
            logger.info('VERIFYING TOKEN "%s"' %token)
            verifyToken(username,
                password,
                url,
                client_id,
                client_ip,
                token,
                logger)
        elif action == "revoke" :
            logger.info('REVOKING TOKEN "%s"' %token)
            revokeToken(username,
                password,
                url,
                token,
                logger)
        else :
            parser.print_help()
            exit()

main()

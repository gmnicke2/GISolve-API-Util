#!/usr/bin/env python

"""
Set of utilities to:
    Register an App
    Configure an App from a configuration file in JSON format
    Get App Info or config and write the response JSON to a destination file

All calls require a valid token either from CG_TOKEN or command line --token

Register App:
    # register an app with name "My_App" and store the name to CG_APP_NAME env var
    export CG_APP_NAME=`./cg_app.py --appname My_App`

Configure App from file "config.json" and print debug information to stderr:
    # Don't need to specify app name again if stored in CG_APP_NAME env var
    ./cg_app.py configure --configfile config.json --debug

Get App Info and Config and write to respective JSON files:
    # Get App Info of a different app than CG_APP_NAME
    ./cg_app getinfo --appname Other_App --destfile getinfo_out.json

    # Get Config of app stored in CG_APP_NAME
    ./cg_app getconfig --destfile getconfig_out.json
"""

from cg_token import CGException, log_response, cg_rest, logger_initialize
import json
import argparse
import requests
import os, sys, logging
import getpass

# Used to disable InsecureRequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

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
    parser.add_argument("-a", "--appname",
        default=os.getenv('CG_APP_NAME',''), 
        help="Set App Name")
    parser.add_argument("-e", "--endpoint",
        default=os.getenv('CG_API',''),
        help="Set API url")
    parser.add_argument("-u", "--username",
        default=os.getenv('CG_USERNAME',''), 
        help="Set Username")
    parser.add_argument("-t", "--token", 
        default=os.getenv('CG_TOKEN',''),
        help="Set Token")
    parser.add_argument("-cf","--configfile", 
        help="For action 'configure' config file in JSON format")
    parser.add_argument("-df","--destfile", 
        help="For actions 'getinfo' and 'getconfig' "
            "destination file to write response")
    parser.add_argument("action", nargs='?', type=str, default='register',
        help="register/configure/getinfo/getconfig")

    args = parser.parse_args()

    logger_initialize(args.debug)

    if not args.endpoint :
        logger.error('CG_API (API url for REST calls) '
                'not specified\n')
        sys.exit(1)

    if args.action.lower() not in ['register','configure','getinfo',
                        'getinfo','getconfig'] :
        logger.error('Invalid Action')
        sys.exit(1)

    return (args,args.action.lower())

def register_app(endpoint, username, appname, token) :
    """Calls the Gateway register_application function and returns the app name

    Args:
        endpoint (string, URL): the REST endpoint
        username (string): the user's login
        appname (string): the name of the app to be registered
        token (string): a valid token to allow user to manipulate apps

    Returns:
        (string): Registered App's name

    Raise:
        Passes any exceptions raised in cg_rest.
    """

    data = {
        'token' : token,
        'app' : appname,
        'longname' : 'Test app by %s' % username,
        'version' : 'V0.1',
        'info' : '<h2>%s</h2><p>Description of App (%s) '
            'Goes Here</p><p>'
            'Author: %s</p>' % (appname,appname,username),
        'author' : username,
        'tags' : 'test, app, %s' % username,
        'type' : 0
    }

    url = endpoint.rstrip('/') + '/app'
    logger.debug("Register app '%s' from '%s'" %(appname,url))

    response = cg_rest('POST', url, **data)
    
    return response['result']['app']

def get_app_info(endpoint, appname, token, dest_filename) :
    """Calls the Gateway Get App Information function
    
    Args:
        endpoint (string,  URL): the REST endpoint
        appname (string): the user's login
        token (string): Valid token to allow user to manipulate applications
        dest_filename (string, path): Path to file for the info to be written to

    Returns:
        (void)

    Raises:
        Passes any exceptions raised in cg_rest
    """

    logger.debug('Writing info to "' + dest_filename + '"')

    params = {
        'token' : token,
        'app' : appname
    }

    url = endpoint.rstrip('/') + '/app'

    response = cg_rest('GET', url, **params)

    # Dump the response JSON (the app info) into the destination file
    with open(dest_filename, 'w') as outfile :
        json.dump(response, outfile, indent=4, separators=(',', ': '))
        outfile.write('\n')
        outfile.close()

    logger.debug('"%s" info successfully '
            'written to "%s"' %(appname,dest_filename))

def config_app(endpoint, appname, token, config_filename) :
    """Calls the Gateway Configure App function
    
    Args:
        endpoint (string,  URL): the REST endpoint
        appname (string): the user's login
        token (string): Valid token to allow user to manipulate applications
        config_filename (string, path): Path to app config in JSON format

    Returns:
        (void)

    Raises:
        Passes any exceptions raised in cg_rest
    """

    logger.debug('Config File: "' + config_filename + '"')

    f = open(config_filename)
    config = json.load(f)
    f.close()
    if not config :
        logger.error("Config File incorrectly formatted.")
        sys.exit(1)

    data = {
        'token' : token,
        'app' : appname,
        'config' : json.dumps(config)
    }

    url = endpoint.rstrip('/') + '/appconfig'

    response = cg_rest('POST', url, **data)

    logger.debug('"%s" successfully configured from '
            'config file "%s"' %(appname,config_filename))

def get_app_config(endpoint, appname, token, dest_filename) :
    """Calls the Gateway Get App Configuration function
    
    Args:
        endpoint (string,  URL): the REST endpoint
        appname (string): the user's login
        token (string): Valid token to allow user to manipulate applications
        dest_filename (string, path): Path to file for config to be written to

    Returns:
        (void)

    Raises:
        Passes any exceptions raised in cg_rest
    """

    logger.debug('Writing config to "' + dest_filename + '"')

    params = {
        'token' : token,
        'app' : appname
    }

    url = endpoint.rstrip('/') + '/appconfig'
    
    response = cg_rest('GET', url, **params)

    # Dump the response JSON (the app config) into the destination file
    with open(dest_filename, 'w') as outfile :
        json.dump(response, outfile, indent=4, separators=(',', ': '))
        outfile.write('\n')
        outfile.close()

    logger.debug('"%s" config successfully'
            ' written to "%s"' %(appname,dest_filename))

def main() :
    (args,action) = parse_args()
    
    if not args.token :
            logger.error('No valid CG_TOKEN given')
            sys.exit(1)

    if not args.appname :
        logger.error('No CG_APP_NAME found or '
            'command line argument specified')
        sys.exit(1)

    try :
        if action == 'register' :
            print register_app(args.endpoint, args.username, 
                                args.appname, args.token) 

        elif action == 'configure' :
                if args.configfile and os.path.exists(args.configfile) :
                    config_app(args.endpoint, args.appname, 
                                args.token, args.configfile)
                else :
                    logger.error('Config File Doesn\'t Exist')
                    sys.exit(1)

        elif action == 'getinfo' :
            if args.destfile :
                get_app_info(args.endpoint, args.appname, 
                            args.token, args.destfile)
            
            elif not os.path.exists("getinfo_out.json") : # use as default
                get_app_info(args.endpoint, args.appname, 
                            args.token, "getinfo_out.json")
            
            else : # if default path exists, don't overwrite it
                logger.error('No destination file specified'
                        ' for get app info')
                sys.exit(1)

        else :
            if args.destfile :
                get_app_config(args.endpoint, args.appname, 
                                args.token, args.destfile)

            elif not os.path.exists("getconfig_out.json") : # use as default
                get_app_config(args.endpoint, args.appname, 
                                args.token, "getconfig_out.json")
            
            else : # if default path exists, don't overwrite it
                logger.error('No destination file specified'
                    ' for get app config')
                sys.exit(1)

    except CGException as e :
        logger.error(e)
        sys.exit(1)

if (__name__ == ("__main__")) :
    main()

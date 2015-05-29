from cg_token import *
import json
import argparse
import requests
from requests import exceptions as rex
import os, sys, logging
import getpass

# Used to disable InsecureRequestWarning that occurs with this API
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)

def logger_initialize(verbose,debug) :
    _format = ("%(levelname)s - %(asctime)s\n%(message)s\n")
    if debug :
        logging.basicConfig(format=_format,
                            level=logging.DEBUG)
    elif verbose :
        logging.basicConfig(format=_format,
                            level=logging.INFO)
    else :
        logging.basicConfig(format=_format,
                            level=logging.WARNING)

# parses command line arguments (gives help if done incorrectly)
def parseArgs() :
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug",
        action="store_true",
        help='Allow debug info to be written to stderr')
    parser.add_argument("-v", "--verbose",
        action="store_true",
        help='Allow non-debug info to be written to stderr')
    parser.add_argument("-p", "--password",
        action="store_true",
        help='Choose to set different password')
    parser.add_argument("-a", "--appname", 
        help="Set App Name")
    parser.add_argument("-r", "--url", 
        help="Set API url")
    parser.add_argument("-u", "--username", 
        help="Set Username")
    parser.add_argument("-t", "--token", 
        help="Set Token")
    parser.add_argument("-c", "--clientid",
        help="Set Client ID")
    parser.add_argument("-i", "--clientip",
        help="Set Client IP")
    parser.add_argument("-cf","--configfile", 
        help="For action 'configure' config file in JSON format")
    parser.add_argument("-df","--destfile", 
        help="For actions 'getinfo' and 'getconfig' "
            "destination file to write response")
    parser.add_argument("action",
        type=str,
        help="For Token: issue/verify/revoke"
            ", App: register/configure/getinfo/getconfig")
    args = parser.parse_args()
    logger_initialize(args.verbose,args.debug)
    if args.action.lower() not in ['issue','verify',
                                'revoke','register',
                                'configure','getinfo','getconfig'] :
        logger.error('Incorrect Action')
        sys.exit(1) 
    if args.password : 
        args.password = getpass.getpass("Enter desired CG Password: ")
    # Initialize Logger
    # Append a terminating '/' if non-existent in API url
    if (args.url
        and not args.url.endswith('/')
       ) :
        args.url += '/'
    elif (os.getenv('CG_API_URL','')
        and not os.getenv('CG_API_URL','').endswith('/')
         ) :
        os.environ['CG_API_URL'] += '/'
    elif (not os.getenv('CG_API_URL','')) :
        logger.error('CG_API_URL (API url for REST calls) '
                'not specified\n')
        sys.exit(1)
    return (parser,args,args.action.lower())

############################APP CALLS##################################
# Register an app, must have a valid token
def registerApp(username,appname,url,token) :
    # Set up request JSON
    request_json = {
        'token' : token,
        'app' : appname,
        'longname' : 'Test app by %s' % username,
        'version' : 'V0.1',
        'info' : '<h2>%s</h2><p>Description of App (%s) '
            'Goes Here</p><p>'
            'Author: %s</p>' % (appname,appname,username),
        'author' : username,
        'tags' : 'test, app, %s' % username
    }
    # Append resource (app) to API url
    url += 'app'
    check_url_validity(url)
    # Get the response from the REST POST in JSON format
    response_json = cg_rest('POST',
        url,
        data=request_json,
        timeout=50,
        verify=False)
    # Check for errors sent back in the response
    check_for_response_errors(response_json)
    logResponse('Register App \"%s\" (HTTP POST)' %appname, 
        request_json, 
        response_json,
        url)
    # on success, return the registered app's name
    try :
        return response_json['result']['app']
    except (TypeError,KeyError) :
        logger.error("\nApp Registration failed for \"%s\"\n"
            "Did you issue a valid token?" %appname)
        sys.exit(1)
        return None

# get app info and write it in JSON format to the destfile given as argument
def getAppInfo(username,appname,url,token,dest_filename) :
    logger.info('Writing info to "' + dest_filename + '"')
    request_json = {
        'token' : token,
        'app' : appname
    }
    # append resource (app) to API url
    url += "app"
    check_url_validity(url)
    # Get the response from the REST GET in JSON format (will be written to dest file)
    response_json = cg_rest('GET',
        url,
        params=request_json,
        timeout=50,
        verify=False)
    check_for_response_errors(response_json)
    logResponse('Get app info for \"%s\" (HTTP GET)' %appname, 
        request_json, 
        response_json,
        url)
    # Dump the response JSON (the app info) into the destination file
    with open(dest_filename, 'w') as outfile :
        json.dump(response_json,
            outfile,
            indent=4,
            separators=(',', ': ')
            )
        outfile.write('\n')
        outfile.close()
    # if successful, return True
    logger.info('"%s" info successfully '
            'written to "%s"' %(appname,dest_filename))
    return True

# configure app with config JSON read in from a file
def configApp(username,appname,url,token,config_filename) :
    logger.info('Config File: "' + config_filename + '"')
    f = open(config_filename)
    config = json.load(f)
    f.close()
    if not config :
        logger.error("Config File incorrectly formatted. (JSON)")
        sys.exit(1)
    request_json = {
        'token' : token,
        'app' : appname,
        'config' : json.dumps(config)
    }
    # append resource (appconfig) to API url
    url += "appconfig"
    check_url_validity(url)
    # Get the response from the REST POST in JSON format
    response_json = cg_rest('POST',
        url,
        data=request_json,
        timeout=50,
        verify=False)
    check_for_response_errors(response_json)
    logResponse('Configure app  \"%s\" (HTTP POST)' %appname, 
        request_json, 
        response_json,
        url)
    # If correctly configured, return true
    logger.info('"%s" successfully configured from '
            'config file "%s"' %(appname,config_filename))
    return True

# get app config and write it in JSON format to the destfile given as an argument
def getAppConfig(username,appname,url,token,dest_filename) :
    logger.info('Writing config to "' + dest_filename + '"')
    request_json = {
        'token' : token,
        'app' : appname
    }
    # append resource (appconfig) to API url
    url += "appconfig"
    check_url_validity(url)
    response_json = cg_rest('GET',
        url,
        params=request_json,
        timeout=50,
        verify=False)
    check_for_response_errors(response_json)
    logResponse('Get app config for \"%s\" (HTTP GET)' %appname, 
        request_json, 
        response_json,
        url)
    # Dump the response JSON (the app config) into the destination file
    with open(dest_filename, 'w') as outfile :
        json.dump(response_json,
            outfile,
            indent=4,
            separators=(',',': ')
            )
        outfile.write('\n')
        outfile.close()
    # If successful, return True
    logger.info('"%s" config successfully'
            ' written to "%s"' %(appname,dest_filename))
    return True

def main() :
    (parser,args,action) = parseArgs()
    # Retrieve necessary info (either from env or overwritten while parsing)
    username = args.username if args.username else os.getenv('CG_USERNAME','')
    password = args.password if args.password else os.getenv('CG_PASSWORD','')
    url = args.url if args.url else os.getenv('CG_API_URL','')
    appname = args.appname if args.appname else os.getenv('CG_APP_NAME','')
    # Make appropriate call or print help if action is not valid
    if action == "issue" :
        logger.info("Issuing Token")
        print issueToken(username,
            password,
            url)
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
            logger.info('Verifying Token "%s"' %token)
            verifyToken(username,
                password,
                url,
                client_id,
                client_ip,
                token)
        elif action == "revoke" :
            logger.info('Revoking Token "%s"' %token)
            revokeToken(username,
                password,
                url,
                token)
            exit()
        if (not (args.appname or os.getenv('CG_APP_NAME',''))) :
            logger.error('No CG_APP_NAME found or '
                'command line argument specified')
            sys.exit(1)
        if action == 'register' :
            logger.info('Registering App: "%s"' %appname)
            print registerApp(username,
                appname,
                url,
                token)
            logger.info('App "%s" successfully registered' %appname)
        elif action == 'configure' :
            # check if config file was given or if it's invalid
            if args.configfile and os.path.exists(args.configfile) :
                logger.info('Configuring App: "%s"' %appname)
                configApp(username,
                    appname,
                    url,
                    token,
                    args.configfile)
            else :
                logger.error('Config File Doesn\'t Exist')
                sys.exit(1)
        elif action == 'getinfo' :
            # check if destination file was specified in command-line arguments
            logger.info('Getting App Info from: "%s"' %appname)
            if args.destfile :
                getAppInfo(username,
                    appname,
                    url,
                    token,
                    args.destfile)
            elif not os.path.exists("getinfo_out.json") : # use this path as default
                getAppInfo(username,
                    appname,
                    url,
                    token,
                    "getinfo_out.json")
            else : # if default path exists, don't overwrite it, just print help & exit
                logger.error('No destination file specified'
                        ' for get app info')
                sys.exit(1)
        elif action == 'getconfig' :
            # check if destination file was specified in command-line arguments
            logger.info('Getting App Config from: "%s"' %appname)
            if args.destfile :
                getAppConfig(username,
                    appname,
                    url,
                    token,
                    args.destfile)
            elif not os.path.exists("getconfig_out.json") : # use this path as default
                getAppConfig(username,
                    appname,
                    url,
                    token,
                    "getconfig_out.json")
            else : # if default path exists, don't overwrite it, just print help & exit
                logger.error('No destination file specified'
                    ' for get app config')
                sys.exit(1)
        else :
            parser.print_help()
            exit()
if (__name__ == ("__main__")) :
    main()

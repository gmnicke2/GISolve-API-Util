import os
from openservice_util import *
from token_util import *
from app_util import *

if __name__ == ("__main__") :
	parseArgs()
	#Just testing various rest calls things
	token = issueToken()
	storeinfo('token',token)
	print('Token created: %s\n' %(getinfo('token')))
	#verified = verifyToken()
	#print('Token verified? %r\n' %(verified))
	revoked = revokeToken()
	#verified = verifyToken()
	print('Token revoked? %r\n' %(revoked))
	#token = issueToken()
	#storeinfo('token',token)
	#print('New Token created: %s\n' %(getinfo('token')))
	app = registerApp()
	if app :
		print('App Registered: \" %s \"\n' %app)
	config_file = raw_input("Enter config filename: ")
	if config_file and os.path.exists(config_file) :
		config_success = configApp(config_file)
	if config_success :
		print('App \" %s \" configured from config file \" %s \"' %(app,config_file))
	#TODO: Implement user-based calls to token/app/job utilities
	#located in token_util.py, app_util.py, and job_util.py

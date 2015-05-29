#!/bin/bash
APPNAME1="TEST1"
APPNAME2="TEST2"
CONFIG_FILE="config.json"
GETINFO_FILE="getinfo_response.json"
GETCONFIG_FILE="getconfig_response.json"
rm getinfo_out.json getconfig_out.json
echo ------------------------------------------------------------------
echo testing: issue + revoke + issue + registerApp + getAppInfo
echo ------------------------------------------------------------------
echo Issuing Token
export CG_TOKEN=`python cg_app.py issue`
echo DONE
echo Revoking Token
python cg_app.py revoke
echo DONE
echo Issuing Token
export CG_TOKEN=`python cg_app.py issue`
echo DONE
echo Registering $APPNAME
export CG_APP_NAME=`python cg_app.py register --appname=$APPNAME1`
echo App Created: \"$CG_APP_NAME\"
echo DONE
echo FIN
echo ------------------------------------------------------------------
echo testing with verbose: issue + verify + registerApp + configureApp + getInfo + getConfig
echo ------------------------------------------------------------------
echo Issuing Token
export CG_TOKEN=`python cg_app.py issue -v`
echo DONE
echo Verifying \"$CG_TOKEN\"
python cg_app.py verify -v
echo Registering $APPNAME
export CG_APP_NAME=`python cg_app.py register --appname=$APPNAME2 -v`
echo App Created: \"$CG_APP_NAME\"
echo DONE
echo Configuring \"$CG_APP_NAME\" with config file \"$CONFIG_FILE\"
python cg_app.py configure -cf $CONFIG_FILE -v
echo DONE
echo Writing info about \"$CG_APP_NAME\" to \"$GETINFO_FILE\"
python cg_app.py getinfo -v
echo DONE
echo Writing config of \"$APPNAME2\" to \"$GETCONFIG_FILE\"
python cg_app.py getconfig -v
echo DONE
echo FIN

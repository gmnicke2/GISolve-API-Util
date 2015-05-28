#!/bin/bash
APPNAME1="TEST1"
APPNAME2="TEST2"
CONFIG_FILE="config.json"
GETINFO_FILE="getinfo_response.json"
GETCONFIG_FILE="getconfig_response.json"
echo ------------------------------------------------------------------
echo testing: issue + revoke + issue + registerApp + getAppInfo
echo ------------------------------------------------------------------
echo Issuing Token
export CG_TOKEN=`python cg_token.py -act issue --clearlog`
echo DONE
echo Revoking Token
python cg_token.py -act revoke
echo DONE
echo Issuing Token
export CG_TOKEN=`python cg_token.py -act issue`
echo DONE
echo Registering $APPNAME
export CG_APP_NAME=`python cg_app.py -act register --appname=$APPNAME1`
echo App Created: \"$CG_APP_NAME\"
echo DONE
echo FIN
echo ------------------------------------------------------------------
echo testing with verbose: issue + registerApp + configureApp + getInfo + getConfig
echo ------------------------------------------------------------------
echo Issuing Token
export CG_TOKEN=`python cg_token.py -act issue -v`
echo DONE
echo Registering $APPNAME
export CG_APP_NAME=`python cg_app.py -act register --appname=$APPNAME2 -v`
echo App Created: \"$CG_APP_NAME\"
echo DONE
echo Configuring \"$CG_APP_NAME\" with config file \"$CONFIG_FILE\"
python cg_app.py -act configure -cf $CONFIG_FILE -v
echo DONE
echo Getting info about \"$CG_APP_NAME\" and writing it to \"$GETINFO_FILE\"
python cg_app.py -act getinfo -df $GETINFO_FILE -v
echo DONE
echo Getting config of \"$APPNAME2\" and writing it to \"$GETCONFIG_FILE\"
python cg_app.py -act getconfig -df $GETCONFIG_FILE -v
echo DONE
echo FIN

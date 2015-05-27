#!/bin/bash
APPNAME1="TEST1"
APPNAME2="TEST2"
VERBOSE_DEST="v_out.txt"
CONFIG_FILE="config.json"
GETINFO_FILE="getinfo_response.json"
GETCONFIG_FILE="getconfig_response.json"
echo ------------------------------------------------------------------
echo testing: issue + revoke \(verbose\) + issue + registerApp + getAppInfo
echo ------------------------------------------------------------------
echo Issuing Token
export CG_TOKEN=`python cg_token.py -act issue`
echo DONE
echo Revoking Token \(Verbose\)
python cg_token.py -act revoke -v > $VERBOSE_DEST
echo DONE
echo Wrote verbose to \"$VERBOSE_DEST\" :
cat $VERBOSE_DEST
echo
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
export CG_TOKEN=`python cg_token.py -act issue`
echo DONE
echo Registering $APPNAME
export CG_APP_NAME=`python cg_app.py -act register --appname=$APPNAME2`
echo App Created: \"$CG_APP_NAME\"
echo DONE
python cg_app.py -act configure -cf $CONFIG_FILE -v
echo DONE
python cg_app.py -act getinfo -df $GETINFO_FILE -v
echo DONE
python cg_app.py -act getconfig -df $GETCONFIG_FILE -v
echo DONE
echo FIN

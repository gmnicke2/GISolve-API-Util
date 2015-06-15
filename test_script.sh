#!/bin/bash
APPNAME1="TEST1"
APPNAME2="TEST2"
JOBNAME1="TEST_JOB1"
CONFIG_FILE="appconfig.json"
GETINFO_FILE="getinfo_response.json"
GETCONFIG_FILE="getconfig_response.json"
MONITORJOB_FILE="monitor_response.json"
rm getinfo_out.json getconfig_out.json monitor_response.json
export CG_API="https://sandbox.cigi.illinois.edu/home/rest/"
echo ------------------------------------------------------------------
echo testing: issue + revoke + issue + registerApp + getAppInfo
echo ------------------------------------------------------------------
echo Issuing Token
export CG_TOKEN=`./cg_token.py -d`
echo DONE
echo Revoking Token
./cg_token.py -d revoke
echo DONE
echo Issuing Token
export CG_TOKEN=`./cg_token.py -d`
echo DONE
echo Registering $APPNAME
export CG_APP_NAME=`./cg_app.py --appname=$APPNAME1 -d --infofile appinfo.json`
echo App Created: \"$CG_APP_NAME\"
echo DONE
echo FIN
echo ------------------------------------------------------------------
echo testing: issue + verify + registerApp + configureApp + getInfo + getConfig
echo ------------------------------------------------------------------
echo Issuing Token
export CG_TOKEN=`./cg_token.py -d issue`
echo DONE
echo Verifying \"$CG_TOKEN\"
./cg_token.py -d verify
echo Registering $APPNAME
export CG_APP_NAME=`./cg_app.py --appname=$APPNAME2 -d --infofile appinfo.json`
echo App Created: \"$CG_APP_NAME\"
echo DONE
echo Configuring \"$CG_APP_NAME\" with config file \"$CONFIG_FILE\"
./cg_app.py -cf $CONFIG_FILE -d configure
echo DONE
echo Writing info about \"$CG_APP_NAME\" to \"$GETINFO_FILE\"
./cg_app.py -d -df $GETINFO_FILE getinfo
echo DONE
echo Writing config of \"$APPNAME2\" to \"$GETCONFIG_FILE\"
./cg_app.py -d -df $GETCONFIG_FILE getconfig
echo DONE
echo
echo ------------------------------------------------------------------
echo testing: Job Submit + Job Monitor + Job Output
echo ------------------------------------------------------------------
echo Submitting Job $JOBNAME1
export CG_JOB_ID=`./cg_job.py -d -cf jobconfig.json --jobname $JOBNAME1`
echo DONE
echo Monitoring Job $JOBNAME1
./cg_job.py -d -df $MONITORJOB_FILE monitor
echo DONE
echo Getting Job Output for $JOBNAME1
./cg_job.py -d output
echo DONE
echo FIN

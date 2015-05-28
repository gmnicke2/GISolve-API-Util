#!/bin/bash
T="python cg_token.py -act"
A="python cg_app.py -act"
rm *.pyc get*
export CG_TOKEN=`$T issue -d --clearlog`
export CG_TOKEN=`$T issue -d`
echo VERIFYING WITH INVALID CONSUMER ID
$T verify -d
echo USING NONEXISTENT USERNAME
$T revoke -u nonexistent -d
echo USING FAULTY URN
$T revoke -r https://wrong.url/ -d
$T revoke -d
export CG_TOKEN=`$T issue -d`
export CG_APP_NAME=`$A register --appname="TESTAPP" -d`
echo USING NONEXISTENT CONFIG PATH
$A configure -cf nonexistentpath -d
$A configure -cf config.json -d
$A getinfo -d
echo USING DEFAULT GETINFO DEST THAT ALREADY EXISTS
$A getinfo -d
echo OVERWRITING GETINFO DEST DEFAULT MANUALLY
$A getinfo -df getinfo_out.json -d
$A getinfo -df getinfo_otherout.json -d
$A getconfig -d
echo USING DEFAULT GETCONFIG DEST THAT ALREADY EXISTS
$A getconfig -d
echo OVERWRITING GETCONFIG DEST DEFAULT MANUALLY
$A getconfig -df getconfig_out.json -d
$A getconfig -df getconfig_otherout.json -d
rm *.pyc get*
echo DONE

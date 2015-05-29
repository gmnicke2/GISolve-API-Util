#!/bin/bash
A="python cg_app.py"
rm *.pyc get*
export CG_TOKEN=`$A issue -d`
export CG_TOKEN=`$A issue -d`
echo VERIFYING WITH INVALID CONSUMER ID
$A verify -d
echo
echo USING NONEXISTENT USERNAME
$A revoke -u nonexistent -d
echo
echo USING FAULTY URL
$A revoke -r https://wrong.url/ -d
echo
$A revoke -d
export CG_TOKEN=`$A issue -d`
export CG_APP_NAME=`$A register --appname="TESTAPP" -d`
echo USING NONEXISTENT CONFIG PATH
$A configure -cf nonexistentpath -d
echo
$A configure -cf config.json -d
$A getinfo -d
echo USING DEFAULT GETINFO DEST THAT ALREADY EXISTS
$A getinfo -d
echo
echo OVERWRITING GETINFO DEST DEFAULT MANUALLY
$A getinfo -df getinfo_out.json -d
echo DONE
$A getinfo -df getinfo_otherout.json -d
$A getconfig -d
echo USING DEFAULT GETCONFIG DEST THAT ALREADY EXISTS
$A getconfig -d
echo
echo OVERWRITING GETCONFIG DEST DEFAULT MANUALLY
$A getconfig -df getconfig_out.json -d
echo DONE
$A getconfig -df getconfig_otherout.json -d
echo rm *.pyc get*
rm *.pyc get*
echo FIN

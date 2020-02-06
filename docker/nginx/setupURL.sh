#!/bin/sh

if [ -z "$SUFFIX" ]
then
    echo "Not tested"
    #mv /nginx.conf /etc/nginx/conf.d
else
	#Remove commas from environment varibale
	BASE_CLEAN=$(echo $BASE | sed 's/"//g')
	SUFFIX_CLEAN=$(echo $SUFFIX | sed 's/"//g')
	sed -i "s,{BASE},$BASE_CLEAN,g" nginxSuffix.conf 
	sed -i "s,{SUFFIX},$SUFFIX_CLEAN,g" nginxSuffix.conf 
	mv /nginxSuffix.conf /etc/nginx/conf.d
fi

tail -f /dev/null 
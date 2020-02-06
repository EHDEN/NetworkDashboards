#!/bin/sh

if [ -z "$SUFFIX" ]
then
    SUFFIX_CLEAN=""
else
	#Remove commas from environment varibale and add slash
	SUFFIX_CLEAN="/$(echo $SUFFIX | sed 's/"//g')"
fi

sed -i "s,{SUFFIX},$SUFFIX_CLEAN,g" base.html
sed -i "s,{SUFFIX},$SUFFIX_CLEAN,g" basic.html
sed -i "s,{SUFFIX},$SUFFIX_CLEAN,g" theme.html
sed -i "s,{SUFFIX},$SUFFIX_CLEAN,g" webpack.config.js
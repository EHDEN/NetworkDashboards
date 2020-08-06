#!/bin/sh

while read var; do
   	#echo $var
    	case $var in
		*NGINX_SUFFIX* ) SUFFIX="$(echo $var|rev|cut -d'=' -f1|rev)" ;;
	esac
done < ../.env

echo $SUFFIX

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
sed -i "s,{SUFFIX},$SUFFIX_CLEAN,g" Loading.jsx
sed -i "s,{SUFFIX},$SUFFIX_CLEAN,g" DisplayQueryButton.jsx



#!/bin/sh

if [ $(nordvpn status | awk -F ":" 'NR==1{print $2}') == 'Connected' ];
then echo '🥸';
else echo '🤔';
fi

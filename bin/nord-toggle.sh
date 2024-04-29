#!/bin/sh

if [ $(nordvpn status | awk -F ":" 'NR==1{print $2}') == 'Connected' ];
then nordvpn disconnect;
else nordvpn connect --group P2P ID;
fi

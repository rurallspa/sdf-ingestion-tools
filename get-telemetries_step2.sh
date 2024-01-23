#! /bin/bash
set -e

for f in files/*
do
	echo $f
	while read -r row; do
		echo $row | sed -e 's/\\\"//g' | jq -r '.rawData'  | base64 --decode > telemetries/$(openssl rand -hex 22).json
	done < $f
done


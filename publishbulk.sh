#! /bin/bash
set -e
data=$(find -type f -path "$1" | head -9)
while [ "$data" ]
do
	python3 ./helper.py $data >  /tmp/mess.json
	/usr/local/bin/aws sns publish-batch --profile=rurall --publish-batch-request-entries file:///tmp/mess.json --topic-arn="arn:aws:sns:eu-west-1:902738125373:sdf-ingestion" > /dev/null
	echo $data
	rm $data
	pwd
	data=$(find -type f -path "$1" | head -9)
	echo $data
done

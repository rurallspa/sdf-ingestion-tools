#! /bin/bash
set -e
data=$(ls -U telemetries/ | head -9)
while [ "$data" ]
do
	`cd telemetries; python3 ../helper.py $data >  /tmp/mess.json`
	/usr/local/bin/aws sns publish-batch --profile=rurall --publish-batch-request-entries file:///tmp/mess.json --topic-arn="arn:aws:sns:eu-west-1:902738125373:sdf-ingestion" > /dev/null
	echo $data
	cd telemetries/
	rm $data
	cd ..
	data=$(ls -U telemetries/ | head -9)
done

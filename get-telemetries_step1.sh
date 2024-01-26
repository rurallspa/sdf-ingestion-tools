#! /bin/bash
set -e

aws s3 ls --recursive s3://rurall-sdf-ingestion/errors/$1 --profile=rurall | awk '{print $4}' > /tmp/data.txt

while read f; do
  aws s3 cp s3://rurall-sdf-ingestion/$f files/ --profile=rurall
done < /tmp/data.txt

rm /tmp/data.txt

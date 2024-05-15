a=$(find base64-batch -type f -name '*.json' | wc -l)

for file in base64-batch/*.json
do
    aws firehose put-record-batch --delivery-stream sdf-implement-tag-telemetries --records "file://$file"
    rm "$file"
    a=$(($a-1))
    echo $a
done
a=$(find ./base64 -type f -name '*.json' | wc -l)

for file in ./base64/*.json
do
    data=$(cat "$file")
    aws firehose put-record --delivery-stream sdf-implement-tag-telemetries --record "$data"
    rm "$file"
    a=$(($a-1))
    echo $a
done
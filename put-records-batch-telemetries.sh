a=$(find telemetries-batch -type f -name '*.json' | wc -l)
export AWS_PAGER=""

for file in telemetries-batch/*.json
do
    aws firehose put-record-batch --delivery-stream SDF-ingestion --records "file://$file" --no-paginate --no-cli-pager
    rm "$file"
    a=$(($a-1))
    echo $a
    sleep 2
done

rm -rf files_processed
rm -rf telemetries_processed
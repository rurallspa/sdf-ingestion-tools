import io
import boto3
import pyarrow.parquet as pq

def merge_parquet(items):
    """
    Merge parquet files for the specified pairs of vin and date
    :param items: list of dictionaries with vin and date keys
    """
    S3 = boto3.resource('s3')

    for item in items:
        bucket = 'rurall-sdf-ingestion'
        prefix = f'telemetries/vin={item["vin"]}/date={item["date"]}'
        keys = [p.get('Key') for p in S3.meta.client.list_objects_v2(Bucket=bucket, Prefix=prefix)['Contents']]
        files = [
            io.BytesIO(S3.meta.client.get_object(Bucket=bucket, Key=p)['Body'].read())
            for p in keys
        ]
        if len(files) > 1:
            print(f"Merging parquet files for VIN {item['vin']} and date {item['date']}")
            input_schema = pq.ParquetFile(files[0]).schema_arrow
            buffer = io.BytesIO()
            with pq.ParquetWriter(buffer, schema=input_schema) as writer:
                for file in files:
                    writer.write_table(pq.read_table(file, schema=input_schema))
            buffer.seek(0)
            S3.meta.client.upload_fileobj(buffer, bucket, prefix + '/merged.parquet')
            for key in keys:
                if 'merged' not in key:
                    S3.meta.client.delete_object(Bucket=bucket, Key=key)

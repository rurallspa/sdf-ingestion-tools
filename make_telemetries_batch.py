import json
import re
import os
import uuid
import shutil
import progressbar
import base64
import sys


INPUT_FOLDER = 'files'
OUTPUT_FOLDER = 'telemetries-batch'


DTYPES = {
    'altitude': float,
    'latitude': float,
    'longitude': float,
    'messagecounter': int,
    'serialnumberctm': str,
    'relative_engine_torque_sdf': int,
    'tank_level_sdf': int,
    'c_epb_state': str,
    'vehicle_speed_sdf': float,
    'c_epb_xactuator': float,
    'c_epb_backup_batt_volt': float,
    'engine_speed_sdf': float,
    'actual_engine_torque_sdf': int,
    'front_pto_speed_sdf': int,
    'rear_pto_speed_sdf': int,
    '4wd_status_sdf': str,
    'difflock_state_sdf': str,
    'fuel_consumption_sdf': float,
    'intake_manifold_temperature': int,
    'exhaust_gas_temperature': float,
    'engine_oil_pressure_sdf': float,
    'power_reduction': int,
    'power_reduction_md3': int,
    'rear_lift_position_sdf': int,
    'dpf_sootloadpercent': int,
    'battery_voltage_sdf': float,
    'cabin_temperature_sdf': float,
    'ac_status_sdf': int,
    'urea_level_sdf': float,
    'ambient_temperature_sdf': float,
    'oil_temperature_sdf_-_frutteto': int,
    'engine_coolant_temperature_sdf': int,
    'engine_oil_temperature_sdf': int,
    'engine_hours_sdf': float,
    'timestamp': str,
    'vin': str,
    'date': str
}


def convert_files(input_folder=INPUT_FOLDER, output_folder=OUTPUT_FOLDER):
    record_batch = []
    tot_len_bytes = 0
    batch_id = str(uuid.uuid4())

    files = sorted([f for f in os.listdir(input_folder)], reverse=True)
    if not files:
        print(f'No files found in {input_folder}')
        return False
    match = re.search(r"\d{4}-\d{2}-\d{2}", files[0])
    batch_start_date = match.group(0) if match else "unknown"
    print('Counting number of records...')
    total_records = sum((sum(1 for _ in open(f'./{input_folder}/{fn}', 'r', encoding='utf-8')) for fn in files))
    print('Total number of records:', total_records)
    print('Coverting', len(files), 'files to batches of <= 500 records and <= 4MB each')
    print('Estimated final number of batches:', total_records // 500 + 1)

    if not os.path.exists(f'./{input_folder}_processed'):
        os.makedirs(f'./{input_folder}_processed')

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in progressbar.progressbar(files):
        if filename.endswith('.json'):
            try:
                with open(f'./{input_folder}/{filename}', 'r', encoding='utf-8') as file:
                    row_data = json.load(file)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error processing file: {filename}. Error: {e}")
                continue
            encoded_payload = base64.b64encode(json.dumps(row_data).encode('utf-8'))
            tot_len_bytes += len(encoded_payload)
            record = dict(Data=encoded_payload.decode('utf-8'))

            if tot_len_bytes < (4 * 1e6) and len(record_batch) < 500:
                record_batch.append(record)
                
            else:
                record_batch = [record]
                batch_id = str(uuid.uuid4())
                tot_len_bytes = len(encoded_payload)
                match = re.search(r"\d{4}-\d{2}-\d{2}", filename)
                batch_start_date = match.group(0) if match else "unknown"

            with open(f'{output_folder}/{batch_start_date}_{batch_id}.json', 'w') as f:
                json.dump(record_batch, f)

        else:
            with open(f'./{input_folder}/{filename}', 'r', encoding='utf-8') as file:
                for row in file:
                    try:
                        row_data = json.loads(row.replace('\\"', '"'))
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        try:
                            row_data = json.loads(row)
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            print(f"Error processing row: {row.strip()}. Error: {e}")
                            continue

                    encoded_payload = row_data.get("rawData", "").encode('utf-8')
                    tot_len_bytes += len(encoded_payload)
                    record = dict(Data=encoded_payload.decode('utf-8'))
                    
                    if tot_len_bytes < (4 * 1e6) and len(record_batch) < 500:
                        record_batch.append(record)
                    else:
                        record_batch = [record]
                        batch_id = str(uuid.uuid4())
                        tot_len_bytes = len(encoded_payload)
                        match = re.search(r"\d{4}-\d{2}-\d{2}", filename)
                        batch_start_date = match.group(0) if match else "unknown"

                    with open(f'{output_folder}/{batch_start_date}_{batch_id}.json', 'w') as f:
                        json.dump(record_batch, f)
    
        shutil.move(f'./{input_folder}/{filename}', f'./{input_folder}_processed/{filename}')
    return True

if __name__ == '__main__':
    try:
        input_folder = sys.argv[1]
    except IndexError:
        input_folder = INPUT_FOLDER
    try:
        output_folder = sys.argv[2]
    except IndexError:
        output_folder = OUTPUT_FOLDER

    _ = convert_files(input_folder, output_folder)

    print(f'./{output_folder} contains', len([f for f in os.listdir(output_folder) if f.endswith('.json')]), 'json batch files ready to be uploaded')
    print("Proceed to execute 'put-records-batch-telemetries.sh' script to send the data to Firehose")
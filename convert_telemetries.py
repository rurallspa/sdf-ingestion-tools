import os
import json
import pandas as pd
import numpy as np


input_folder = 'telemetries-to-convert'
input_position_file_name = 'telemetry_position.csv'
input_telemetry_param_file_name = 'telemetry_param.csv'
output_folder = 'telemetries'


COLUMN_DTYPES = {
    'altitude': float,
    'latitude': float,
    'longitude': float,
    'messageCounter': int,
    'serialNumberCtm': str,
    'Relative engine torque SDF': int,
    'Tank Level SDF': int,
    'C_EPB_STATE': str,
    'Vehicle speed SDF': float,
    'C_EPB_XACTUATOR': float,
    'C_EPB_BACKUP_BATT_VOLT': float,
    'Engine Speed SDF': float,
    'Actual engine torque SDF': int,
    'Front PTO Speed SDF': int,
    'Rear PTO Speed SDF': int,
    '4WD status SDF': str,
    'DiffLock state SDF': str,
    'Fuel Consumption SDF': float,
    'Intake_Manifold_Temperature': int,
    'Exhaust_Gas_Temperature': float,
    'Engine oil pressure SDF': float,
    'Power_reduction': int,
    'Power_reduction_MD3': int,
    'Rear Lift Position SDF': int,
    'DPF_SootLoadPercent': int,
    'Battery voltage SDF': float,
    'Cabin temperature SDF': float,
    'AC status SDF': int,
    'Urea level SDF': float,
    'Ambient temperature SDF': float,
    'Oil Temperature SDF - Frutteto': int,
    'Engine Coolant Temperature SDF': int,
    'Engine oil temperature SDF': int,
    'Engine Hours SDF': float,
    'timeStamp': str
}

TELEMETRY_NAMES = (
    'Relative engine torque SDF',
    'Tank Level SDF',
    'C_EPB_STATE',
    'Vehicle speed SDF',
    'C_EPB_XACTUATOR',
    'C_EPB_BACKUP_BATT_VOLT',
    'Engine Speed SDF',
    'Actual engine torque SDF',
    'Front PTO Speed SDF',
    'Rear PTO Speed SDF',
    '4WD status SDF',
    'DiffLock state SDF',
    'Fuel Consumption SDF',
    'Intake_Manifold_Temperature',
    'Exhaust_Gas_Temperature',
    'Engine oil pressure SDF',
    'Power_reduction',
    'Power_reduction_MD3',
    'Rear Lift Position SDF',
    'DPF_SootLoadPercent',
    'Battery voltage SDF',
    'Cabin temperature SDF',
    'AC status SDF',
    'Urea level SDF',
    'Ambient temperature SDF',
    'Oil Temperature SDF - Frutteto',
    'Engine Coolant Temperature SDF',
    'Engine oil temperature SDF',
    'Engine Hours SDF',
)

def csv_telemetries_to_json(gps_path, telemetry_path, output_path):
    """
    Converts csv telemetries into json ready to be ingested by AWS Glue.
    
    Arguments:
        gps_path : str
            path to the gps file in csv format. The file must contain at least 3 columns: TIME_MSG_RECEIVED, LATITUDE, LONGITUDE.
        telemetry_path : str
            path to the telemetry file in csv format. The file must contain at least 3 columns: TIME_MSG_RECEIVED, PARAM_NAME, ACTUAL_NORMALIZED_VALUED.
        output_path : str
            where the output telemetries should be saved. A json file will be created for each individual telemetry.
    """
    gps = pd.read_csv(gps_path, decimal='.', delimiter=';', index_col='time').drop_duplicates()
    telemetries = pd.read_csv(telemetry_path, delimiter=';').drop_duplicates()
    telemetries['actual_normalized_valued'] = np.where(
        telemetries.param_name.isin(['4WD status SDF', 'DiffLock state SDF', 'C_EPB_STATE']), 
        telemetries.actual_raw_value_s, 
        telemetries.actual_normalized_valued
    )

    data = telemetries[['time', 'param_name', 'actual_normalized_valued']]
    data = data.pivot(index='time', columns='param_name', values='actual_normalized_valued')
    vin = telemetries['vin'].unique()[0]
    data['vin'] = vin
    data['altitude'] = data['messageCounter'] = data['serialNumberCtm'] = data['telemetries'] = 0        
    data[['latitude', 'longitude', 'altitude']] = gps[['latitude', 'longitude', 'altitude']]
    data = data.reset_index()
    data = data.rename(columns={'time': 'timeStamp'})
    for column_name in COLUMN_DTYPES.keys():
        if column_name not in data.columns:
            data[column_name] = None
    data = data.replace({np.nan: None})
    data = data.astype(COLUMN_DTYPES, errors='ignore')
    data = data.replace({np.nan: None, 'None': None})
    base_data = data[['altitude', 'latitude', 'longitude', 'messageCounter', 'serialNumberCtm', 'telemetries', 'timeStamp', 'vin']].copy()
    nested_telemetries = data.apply(
        lambda row: [{'name': column_name, 'physicalValue': COLUMN_DTYPES[column_name](row[column_name]) if row[column_name] is not None else None} 
        for column_name in TELEMETRY_NAMES], axis=1
    )
    base_data['telemetries'] = nested_telemetries
    base_data['timeStamp'] = pd.to_datetime(base_data['timeStamp'], utc=True).apply(lambda x: x.isoformat().replace("+00:00", "Z"))
    telemetries_list = base_data.to_dict(orient='records')
    quantiles = dict(zip(np.linspace(0, len(telemetries_list) - 1, 10, dtype=int), range(10)))
    for i, t in enumerate(telemetries_list):
        if i in quantiles.keys():
            print(f'{quantiles[i]*10}%')
        with open(f"{output_path}/{vin}_{t['timeStamp']}.json", "w") as f:
            json.dump(t, f)
    print(data.info())
    return data


if __name__ == "__main__":
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)
    initial_n_telemetries = len([f for f in os.listdir(output_folder) if f.endswith('.json')])
    if initial_n_telemetries > 0:
        user_input = input("The output folder is not empty. Do you want to clear it? (Y/N): ").strip().lower()
        if user_input in('Y', 'y', 'yes', 'YES'):
            for f in os.listdir(output_folder):
                if f.endswith('.json'):
                    os.remove(os.path.join(output_folder, f))
            print("Output folder cleared.")
        elif user_input in ('N', 'n', 'no', 'NO'):
            print("Keeping existing files in the output folder.")
        else:
            print("Invalid input. Exiting.")
            exit(1)
    initial_n_telemetries = len([f for f in os.listdir(output_folder) if f.endswith('.json')])
    print("Initial number of telemetries in output folder:", initial_n_telemetries)
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    unique_vins = set(f.split('_')[0] for f in csv_files)
    
    for vin in unique_vins:
        position_file = f"{vin}_{input_position_file_name}"
        telemetry_file = f"{vin}_{input_telemetry_param_file_name}"
        
        if position_file not in csv_files or telemetry_file not in csv_files:
            raise Exception(
                f'Missing files for VIN {vin}: expected {position_file} and {telemetry_file}'
            )
    for vin in unique_vins:
        position_file = f"{input_folder}/{vin}_{input_position_file_name}"
        telemetry_file = f"{input_folder}/{vin}_{input_telemetry_param_file_name}"
        
        print(f'Processing VIN {vin}...')
        _ = csv_telemetries_to_json(
            position_file, 
            telemetry_file, 
            output_folder
        )
    print("Total number of telemetries generated:", len([f for f in os.listdir(output_folder) if f.endswith('.json')]) - initial_n_telemetries)

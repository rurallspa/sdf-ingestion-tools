import pandas as pd
import numpy as np
import json
import base64
import os
import uuid
import sys

try:
    sep, decimal, thousands = sys.argv[1], sys.argv[2], sys.argv[3]
except IndexError:
    sep, decimal, thousands = ';', ',', '.'

if thousands == 'None':
    thousands = None

print(f'Using sep={sep} decimal={decimal} thousands={thousands}')

def convert_csv():
    record_batch = []
    tot_len_bytes = 0
    batch_id = str(uuid.uuid4())

    for file in os.listdir('csv'):
        if file.endswith('.csv'):
            df = pd.read_csv(f'./csv/{file}', sep=sep, decimal=decimal, thousands=thousands).replace(np.nan, None)
            df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M:%S.%f %z', utc=True).apply(lambda x: x.isoformat().replace('+00:00', 'Z'))
            df['row_create_dt'] = pd.to_datetime(df['row_create_dt'], format='%Y-%m-%d %H:%M:%S.%f %z', utc=True).apply(lambda x: x.isoformat().replace('+00:00', 'Z'))
            data = df.to_dict(orient='records')

            for d in data:
                payload_out = dict(
                    serialNumberCtm=d['serial_number_ctm'],
                    tags=[dict(
                        data=dict(
                            batteryVoltage=d['battery_voltage'],
                            humidity=d['humidity'],
                            lowBattery=d['low_battery'],
                            temperature=d['temperature'],
                        ),
                        latitude=d['latitude'],
                        longitude=d['longitude'],
                        altitude=d['altitude'],
                        macAddress=d['mac_address'],
                        name=d['name'],
                        timestamp=d['time'],
                        vehicleSpeed=d['vehicle_speed'],
                        messageCounter=d['daily_message_counter']
                    )],
                    vin=d['vin']
                )

                with open(f"json/{d['mac_address']}_{d['time']}.json", "w") as f:
                    json.dump(payload_out, f)

                encoded_payload = base64.b64encode(json.dumps(payload_out).encode('utf-8'))
                tot_len_bytes += len(encoded_payload)
                record = dict(Data=encoded_payload.decode('utf-8'))
                
                if tot_len_bytes < 4e6 and len(record_batch) < 500:
                    record_batch.append(record)
                else:
                    record_batch = [record]
                    batch_id = str(uuid.uuid4())

                with open(f'base64-batch/{batch_id}.json', 'w') as f:
                    json.dump(record_batch, f)
                    
                with open(f"base64/{d['mac_address']}_{d['time']}.json", "w") as f:
                    json.dump(record, f)

    return record_batch


if __name__ == '__main__':
    record_batch = convert_csv()
    print(len(record_batch), 'records succesfully converted to json')
    print('/json folder now has', len([f for f in os.listdir('json') if f.endswith('.json')]), 'files')
    print('/base64 folder now has', len([f for f in os.listdir('base64') if f.endswith('.json')]), 'files')
    print('/base64-batch folder now has', len([f for f in os.listdir('base64-batch') if f.endswith('.json')]), 'files')
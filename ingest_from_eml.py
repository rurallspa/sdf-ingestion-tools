import email
import os.path
import json
import boto3
import time

stepf = boto3.client('stepfunctions')
stepf_per_minute = 4
path = './s2/s2'
for i,eml in enumerate(os.listdir(path)):
	with open(path+'/'+eml) as email_file:
		email_message = email.message_from_file(email_file)
		print(email_message.get_payload().split('--')[0])
		stepf.start_execution(
        	stateMachineArn='arn:aws:states:eu-west-1:902738125373:stateMachine:ibf-s2-ingestion',
			input=email_message.get_payload().split('--')[0]
		)
		time.sleep(60/stepf_per_minute)

import sys
import json
import uuid
print(json.dumps([
	dict(
		Id=str(uuid.uuid4()),
		Message=open(f, 'r').read()
	)
	for f in sys.argv[1:]
]))

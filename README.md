# Wadutils

> Common Python utilities/helpers

## Installation

To install from pip:

```
pip install https://github.com/WadiInternet/wadutils/archive/master.zip
or
pip3 install https://github.com/WadiInternet/wadutils/archive/master.zip

```

To install from source:
```
git clone git@github.com:WadiInternet/wadutils.git

python setup.py develop
or
python3 setup.py develop
```

## Requirements

```
pip install -r requirements.txt
or
pip3 install -r requirements.txt
```

## Usage\Examples
The broad swathes of snippets available are:

#### Google Utilities

##### Google login

Connect to Google API for accessing all google related services such as accessing google documents for example.

- Required Package : gspread, oauth2client
- Environment Variable: GOOGLE_CREDS  path to the google credential file [client_secrets]

```
from wadutils import google_login
google_connection = google_login()
google_connection.open_by_key(GOOGLE_DOCUMENT_KEY)
```

##### Google URL shortener

URL shortener API for goo.gl

- Required Package: pyshorteners
- Environment Variable: SHORTENER_API_KEY

```
from wadutils import url_shortener
short_url = url_shortener(long_url)
```

#### Amazon Utilities
##### S3 Connection

Getting connection to S3 bucket for accessing/updating files.

- Required Package: boto
- Environment Variable: AMAZON_ACCESS_KEY_ID, SECRET_ACCESS_KEY

```
from wadutils import get_s3_connection
bucket = get_s3_connection('bucket_name')
```

##### Read CSV file from S3
Getting content from a csv file hosted on S3

- Required Package: boto
- Environment Variable: AMAZON_ACCESS_KEY_ID, SECRET_ACCESS_KEY

```
from wadutils import read_file_s3
file_content_as_list = read_file_s3(file_name, bucket_name)
```

##### SQS Connection
Getting connection to Amazon SQS for pushing/pulling messages from queue

- Required Package: boto
- Environment Variable: AMAZON_REGION, AMAZON_ACCESS_KEY_ID, SECRET_ACCESS_KEY

```
from wadutils import get_sqs_connection
queue = get_sqs_connection('queue_name')
```

##### Write to SQS
Write messages to SQS Queue

- Required Package: boto
- Environment Variable: AMAZON_REGION, AMAZON_ACCESS_KEY_ID, SECRET_ACCESS_KEY

```
import json
from wadutils import write_to_sqs
data = {"first_name":"foo","last_name":"bar"}
write_to_sqs('queue_name', json.dumps(data))
```

#### Rabbit MQ
Connecting to Rabbit MQ, and publishing messages

##### Getting Rabbit MQ Connection
- Required Package: pika, pika_pool
- Environment Variable: RABBIT_CRED

```
from wadutils import get_rabbit_connection
rabbit_connection = get_rabbit_connection()
```

##### Rabbit publish
- Required Package: pika, pika_pool
- Environment Variable: RABBIT_CRED

```
from wadutils import rabbit_publish
data = {"first_name":"foo","last_name":"bar"}
rabbit_connection = rabbit_publish(data)
```

#### Dropbox

##### Dropbox Connection
Getting dropbox connection
- Required Package: dropbox
- Environment Variable: DROPBOX_TOKEN

```
from wadutils import get_dropbox_connection
connection = get_dropbox_connection()
```

##### Get file from Dropbox
Fetches file from dropbox , stores it locally, and returns the local path of file stored, supports an additional parameter move, which moves the folder to specified location in dropbox.

- Required Package: dropbox
- Environment Variable: DROPBOX_TOKEN

```
from wadutils import get_file_dropbox
file_location = get_file_dropbox(file_name)
```

##### Push file to Dropbox
Upload a file to dropbox

- Required Package: dropbox
- Environment Variable: DROPBOX_TOKEN

```
from wadutils import push_file_dropbox
response = push_file_dropbox(directory_path, file_name)
```


#### Generic Utilities
##### Convert to json
Used for converting the payload to json, particularly preventing datetime and decimal field error

```
from wadutils import to_json
data = {"first_name":"foo","score":23.4}
json_output = to_json(data)
```

##### String to Hex Conversion
Particularly used for converting arabic characters to their hexadecimal counterparts.

```
from wadutils import str_to_hex
text_update = str_to_hex(u'ﻡﺮﺤﺑﺍ')
```

##### yaml to dict
Returns a dict object for a yml file.

```
from wadutils import yaml_loader
GENERIC_DICT = yaml_loader('generic.yml')
```

##### Write to CSV
Generates a csv file with the records provided.

```
from wadutils import write_to_csv
data = [{"first_name":"foo","last_name":"bar"}, {"first_name":"foo2","last_name":"bar2"}]
write_to_csv('test.csv', data)
```

##### CSV Reader
Reads a CSV file and returns the values in a list

```
from wadutils import csv_reader
csv_records = csv_reader("/tmp/", 'test.csv')
```

##### Chunks
Breaks down a data structure into specified chunks

```
from wadutils import chunker
data = [1,2,3....10000]
chunks = chunker(data, 1000)
```

##### update timestamp
Stores a value in a temporary redis file
- Required Package: hirlite

```
from datetime import datetime
from wadutils import update_timestamp
now = datetime.utcnow()
update_timestamp('last_updated', now)
```

##### get timestamp
Fetches the value stored previously, if not found gets the timestamp of last 30 mins.
- Required Package: hirlite

```
from wadutils import get_timestamp
timestamp = get_timestamp('last_updated')
```

[client_secrets]: <https://developers.google.com/api-client-library/python/guide/aaa_client_secrets>


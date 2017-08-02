'''A collection of utilities used by different processes'''

import os

from .utils import memoize
from lxml import etree
import requests
from requests_ntlm import HttpNtlmAuth

'''Google Utilities'''

@memoize(expiry_time=60*5)
def google_login():
    '''Login to google for reading google docs
       :param: GOOGLE_CREDS: complete file path to .json OAUTH credential file
    '''

    import gspread, json
    from oauth2client.client import SignedJwtAssertionCredentials

    scope = ['https://spreadsheets.google.com/feeds']
    json_key = json.load(open(os.environ['GOOGLE_CREDS']))

    try:
        credentials = SignedJwtAssertionCredentials(json_key['client_email'],\
            json_key['private_key'], scope)
    except TypeError: #for python3 support
        credentials = SignedJwtAssertionCredentials(json_key['client_email'],\
            bytes(json_key['private_key'], 'UTF-8'), scope)

    google_connection = gspread.authorize(credentials)
    return google_connection

def url_shortener(url):
    '''Shorten url through google api
      :param url: url to be shortened, with urlencode
      :param SHORTENER_API_KEY: goo.gl shortener key
    '''

    from pyshorteners.shorteners import Shortener
    shortener = Shortener('GoogleShortener', api_key=os.environ['SHORTENER_API_KEY'])
    short_url = shortener.short(url)
    return short_url


'''Amazon Utilities'''

@memoize(expiry_time=60*10)
def get_s3_connection(bucket):
    '''Establishing an S3 Connection
       :param AMAZON_ACCESS_KEY_ID: Access key for AWS
       :param SECRET_ACCESS_KEY: Secret key for AWS
    '''

    from boto.s3.connection import S3Connection

    conn = S3Connection(os.environ['AMAZON_ACCESS_KEY_ID'], os.environ['SECRET_ACCESS_KEY'])
    bucket_obj = conn.get_bucket(bucket)

    return bucket_obj

@memoize(expiry_time=60*10)
def get_sqs_connection(queue):
    '''Connect to the SQS queue
       :param AMAZON_REGION: Amazon region
       :param AMAZON_ACCESS_KEY_ID: Access key for AWS
       :param SECRET_ACCESS_KEY: Secret key for AWS
    '''

    from boto import sqs

    connection = sqs.connect_to_region(
        os.environ['AMAZON_REGION'],
        aws_access_key_id=os.environ['AMAZON_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['SECRET_ACCESS_KEY'])
    queue_obj = connection.get_queue(queue)

    return queue_obj

def write_to_sqs(queue_name, message):
    '''Write to sqs queue
       :param queue_name: Name of valid queue created in AWS
       :param message: json formatted message
    '''

    from boto import sqs

    mail_queue = get_sqs_connection(queue_name)
    message_object = sqs.message.Message()
    message_object.set_body(message)
    status = mail_queue.write(message_object)

    return status

def read_file_s3(file_name, bucket_name):
    '''Reading from S3 file, storing it locally in tmp
       :param file_name: name of the file to be retrieved from S3
       :param bucket_name: name of S3 bucket
    '''

    import tempfile
    import csv

    bucket = get_s3_connection(bucket_name)
    response = bucket.get_key(file_name)

    if not response: return False

    temp_dir = tempfile.mkdtemp(prefix="S3")
    response.get_contents_to_filename(temp_dir+file_name)

    with open(temp_dir+file_name, 'rb') as csvfile:
        stock_rows = csv.reader(csvfile)
        stock_rows.next()
        rows = [row for row in stock_rows]

    return rows


'''Rabbit MQ'''

@memoize(expiry_time=60*10)
def get_rabbit_connection():
    '''Connect to Rabbit MQ
       :param RABBIT_CRED: connection string for rabbit MQ
    '''

    import pika
    import pika_pool

    pool = pika_pool.QueuedPool(
        create=lambda: pika.BlockingConnection(
            parameters=pika.URLParameters(os.environ['RABBIT_CRED'])),
        max_size=10,
        max_overflow=10,
        timeout=10,
        recycle=3600,
        stale=45,
        )
    return pool

def rabbit_publish(payload):
    '''Publish to Rabbit MQ
      :param ROUTING_KEY: key for rabbit MQ
    '''
    import json

    with get_rabbit_connection().acquire() as cxn:
        cxn.channel.basic_publish(
            exchange='',
            routing_key=os.environ['ROUTING_KEY'],
            body=json.dumps(payload), mandatory=True)


'''Geckoboard '''

def update_geckoboard_text(widget_key, text):
    '''Update text widget on Gecko
       :param widget_key: key for the widget to be updated
       :param text: text to be pushed
       :param GECKO_API_KEY: geckoboard access key
    '''

    import requests
    import json

    geckourl = "https://push.geckoboard.com/v1/send/"+widget_key
    gecko_post = requests.post(
        geckourl,
        data=json.dumps({"api_key":os.environ['GECKO_API_KEY'],\
            "data": {"item":[{"text":text}]}}),\
        headers={'Content-Type': 'application/json'}
        )
    return gecko_post


'''Flask'''
def stream_template(app, template_name, **context):
    '''Stream Flask templates
       :param app: flask app object
       :param template_name: name of the template to be streamed
       :param context: data to be streamed
    '''

    app.update_template_context(context)
    template_obj = app.jinja_env.get_template(template_name)
    return_value = template_obj.stream(context)
    return_value.enable_buffering(5)
    return return_value

def generate_csv_flask(records):
    '''Generate CSV file from flask request
      :param records: records in the format of tuple of list [('head1','data1')('head2','data2')]
    '''

    for rows in records:
        row_list = []
        for row in rows:
            val = str(row[1]) or ''
            row_list.append(str(val.replace(',', '/')))
        yield ','.join(row_list) + '\n'

def generate_csv_flask_unicode(records):
    '''Generate unicode CSV file from flask request
      :param records: records in the format of tuple of list [('head1','data1')('head2','data2')]
    '''

    for rows in records:
        row_list = []
        for row in rows:
            val = (unicode(row[1]).encode("utf-8")) if row else ''
            row_list.append((val.replace(',', '/')))
        yield ','.join(row_list) + '\n'


'''Dropbox'''

@memoize(expiry_time=60*5)
def get_dropbox_connection():
    '''Establish a connection to Dropbox
       :param DROBOX_TOKEN: OAUTH Token for connecting to Dropbox
    '''

    import dropbox
    connection = dropbox.Dropbox(
        os.environ['DROPBOX_TOKEN'],
        max_retries_on_error=2, max_retries_on_rate_limit=2)
    return connection

def get_file_dropbox(file_name, move=True):
    '''Fetch file from dropbox, if not present return None, once read move file to archive
      :param file_name: name of the file to be retrieved
    '''

    import tempfile
    import dropbox
    from datetime import datetime

    client = get_dropbox_connection()
    temp_dir = tempfile.mkdtemp(prefix='dropbox-')
    now_date = str(datetime.utcnow()).replace(" ", "_")

    try:
        response = client.files_download_to_file(
            download_path='/{}/{}'.format(temp_dir, file_name), path='/{}'.format(file_name))
        if move:
            client.files_move(
                from_path='/{}'.format(file_name),
                to_path='/archive/{}_{}'.format(now_date, file_name))
            return temp_dir, file_name
        return response
    except dropbox.exceptions.ApiError as error:
        print(error)
        return

def push_file_dropbox(temp_dir, file_name):
    '''Push files to dropbox
       :param temp_dir: location of the file on local system
       :param file_name: name of the file
    '''

    import dropbox

    client = get_dropbox_connection()
    file_obj = open(temp_dir+file_name, 'rb')
    mode = dropbox.files.WriteMode('add')
    response = client.files_upload(
        f=file_obj, path='/{}'.format(file_name), mode=mode, autorename=True)
    file_obj.close()

    return response


'''Generic Utilities'''

def to_json(obj):
    '''Convert object to datetime '''

    import json
    import datetime
    from decimal import Decimal

    def default(obj):
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()[:16]
        if isinstance(obj, Decimal):
            return int(obj)
        raise ValueError("Can't convert: %s" % repr(obj))

    return json.dumps(obj, default=default)

def str_to_hex(text):
    '''Converting arabic text to hex for sending as sms
       :param text: text in unicode format
    '''

    text = text.strip("u").strip("'")
    arabic_hex = [hex(ord(b)).replace("x", "").upper().zfill(4) for b in text]
    arabic_hex.append("000A")
    text_update = "".join(arabic_hex)
    return text_update

@memoize(expiry_time=60*10)
def yaml_loader(filename):
    '''Generate a dict from yml/twig file
       :param filename: file path along with file name
    '''

    import yaml
    file_obj = open(filename)
    yml_dict = yaml.safe_load(file_obj)
    file_obj.close()
    return yml_dict

def pushformatter(param):
    '''Format contact number'''

    try:
        param = str(param)
    except UnicodeEncodeError:
        return None
    number = param.translate(None, '+').translate(None, '-')
    if number[:3] == '971':
        dialstring = '00'+number
        return dialstring
    elif number[:2] == '00':
        return number
    else:
        dialstring = '00'+number
        return dialstring

def decimal_default(obj):
    '''Converting decimal to float for json '''

    import decimal
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

def write_to_csv(file_name, records, fieldnames=None):
    '''Dumping to csv file from a dict'''

    import csv
    from datetime import datetime

    with open('/tmp/' + file_name, 'w') as csvfile:
        if not fieldnames:
            fieldnames = records[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in records:
            writer.writerow(row)
        print('{} dumped at: {}'.format(file_name, datetime.now()))

def csv_reader(dir_path, file_name):
    '''Reading data from CSV file
      :param dir_path: location of file on system
      :param file_name: name of file
    '''

    import csv
    with open(dir_path+file_name, 'r', encoding='ascii', errors='ignore') as csvfile:
        reader = csv.reader(csvfile)
        try:
            data = [row for row in reader]
        except csv.Error as error:
            print(error)
            return ''
    return data

def csv_reader_dict(dir_path, file_name):
    '''Reading csv file and returning list of dict for data
      :param dir_path: location of file
      :param file_name: name of file
    '''

    import csv
    with open(dir_path+file_name) as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]

    return data

def chunker(seq, size):
    '''break data structure to mentioned sized chunks
       :param seq: list of records
       :param size: chunks to broken into
    '''

    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def update_timestamp(key, timestamp):
    '''update the redis key with timestamp
      :param key: unique identifier
      :param timestamp: timestamp
    '''

    import hirlite
    rlite = hirlite.Rlite(path='timer.rld')
    rlite.command('set', key, timestamp)

def get_timestamp(key):
    '''Fetch last runtime
      :param key: unique identifier
    '''

    from datetime import datetime, timedelta
    import hirlite

    rlite = hirlite.Rlite(path='timer.rld')

    if rlite.command('get', key):
        timestamp = rlite.command('get', key)
    else:
        timestamp = datetime.utcnow() - timedelta(minutes=60)

    try: #py3
        timestamp = timestamp.decode("utf-8")
    except AttributeError:
        timestamp = timestamp
    return timestamp


'''DB connections/updates '''

def get_engine(db):
    '''fetch sql engine
       :param db: mysql connection string in format mysql://username:password@host:port
    '''

    from sqlalchemy import create_engine
    conn = create_engine(db, pool_recycle=60, max_overflow=0, pool_timeout=30)
    return conn.connect()

def insert_into(engine, table_name, values):
    '''For inserting data into DB, on duplicate key update
       :param engine: mysql connection string in format mysql://username:password@host:port/schema
       :param table_name: name of the table
       :param value: list of dicts
    '''

    import sqlalchemy

    if not values: return

    engine = sqlalchemy.create_engine(engine)
    metadata = sqlalchemy.MetaData(bind=engine)
    table = sqlalchemy.Table(table_name, metadata, autoload=True)

    table = metadata.tables[table_name]
    for row in values:
        columns = list(set(table._columns.keys()) & set(row.keys()))
        query = sqlalchemy.text(
            "INSERT INTO `{}` ({}) VALUES ({}) ON DUPLICATE KEY UPDATE {}".format(
                table_name, ", ".join(columns), ", ".join(":" + c for c in columns),
                ", ".join("{}=VALUES({})".format(c, c) for c in columns)))
        engine.execute(query, row)

    return engine

def get_results_as_dict(*args, **kwargs):
    '''return sql data as a list of dict
      :param query: sql query to be executed
      :param db: mysql connection string
    '''

    return list(get_results_as_dict_iter(*args, **kwargs))

def get_results_as_dict_iter(engine, query, dict=dict, engines={}, **kwargs):
    '''fetch results from sql read query
       :param engine: mysql connection string
       :param query: mysql query to be executed
    '''

    from sqlalchemy.sql import text
    from namutil import format_query_with_list_params

    try:
        basestring = basestring
    except NameError:
        basestring = (str, bytes)

    if isinstance(engine, basestring):
        engine = get_engine(engines.get(engine, engine))
    is_session = 'session' in repr(engine.__class__).lower()
    query, kwargs = format_query_with_list_params(query, kwargs)

    q = text(query.format(**kwargs))
    result = engine.execute(q, params=kwargs) if is_session else engine.execute(q, **kwargs)
    keys = result.keys()
    for r in result:
        yield dict((k, v) for k, v in zip(keys, r))
    engine.close()
    engine.engine.dispose()

def write_to_db(db, table_name, truncate, records, *args, **kwargs):
    '''bulk update data to mysql table
      :param db: mysql connection string in format mysql://username:password@host:port/schema
      :param table_name: name of the table to be updated
      :param truncate: by default false, if set to 1, truncates the table before updating
      :param records: list of tuples of record in the same order as column names in db
      :param ignore: by default true, to not consider the primary key id field,
                     if set to false data needs to be supplied
      :param query: raw insert/update query to be executed
    '''

    import sqlalchemy

    engine = get_engine(db)

    if 'query' in kwargs:
        engine.execute(kwargs['query'])
        engine.close()
        engine.engine.dispose()
        return engine

    metadata = sqlalchemy.MetaData(bind=engine)
    table = sqlalchemy.Table(table_name, metadata, autoload=True)
    table = metadata.tables[table_name]

    columns = table._columns.keys()
    if 'ignore' not in kwargs:
        columns.pop(0)
    del columns[len(records[0]):]

    if truncate:
        query = sqlalchemy.text("Truncate {}".format(table_name))
        engine.execute(query)

    query = sqlalchemy.text("INSERT INTO `{}` ({}) VALUES {} \
            ON DUPLICATE KEY UPDATE {}".format(table_name, ", ".join(columns), \
            str(records).strip('[]'), ", ".join("{}=VALUES ({})".format(c, c) \
            for c in columns)))
    engine.execute(query)
    engine.close()
    engine.engine.dispose()

    return engine

def get_graylogger(host, facility, level='INFO', port=12201, **kwargs):
    import logging, graypy
    logger = logging.getLogger(facility)
    logger.setLevel(getattr(logging, level))
    logger.addHandler(graypy.GELFHandler(host, port, **kwargs))
    h = logging.StreamHandler()
    h.setLevel(logging.DEBUG)
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.info("Starting")
    return logger


class SoapHelper(object):
    def get_xml(self, xmldata, post_url, soap_action, username=None, password=None):
        auth = HttpNtlmAuth(username, password)
        soap_response = requests.post(post_url, headers={
            "Content-Type": "text/xml; charset=utf-8",
            "Content-Length": str(len(xmldata)),
            "SOAPAction": soap_action}, 
            data=xmldata,
            auth=auth)

        if soap_response.status_code == 200:
            return {'status': True, 'message': "Item successfully exported to erp!"}

        xml = etree.fromstring(soap_response.content)
        error = None
        try:
            for elem in xml.iter('faultstring'):
                error = elem.text
        except Exception as e:
            error = "Unknown error occurred!"

        return {'status': False, 'message': error}

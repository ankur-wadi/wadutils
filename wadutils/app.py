import os
from namutil import memoize
from collections import OrderedDict, defaultdict

#google/docs
@memoize(expiry_time=60*2)
def google_login():
    '''Login to google for reading gdocs '''

    import gspread, json
    from oauth2client.client import SignedJwtAssertionCredentials

    scope = ['https://spreadsheets.google.com/feeds']
    json_key = json.load(open(os.environ['GOOGLE_CREDS'])) #complete file path to .json creds file for accessing google sheets
    try:
       credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)
    except TypeError: #for python3 support
       credentials = SignedJwtAssertionCredentials(json_key['client_email'], bytes(json_key['private_key'], 'UTF-8'), scope)
    gc = gspread.authorize(credentials)
    return gc

#amazon/s3
def sqs_connection(queue):
    from boto import sqs
    '''Connect to the SQS queue'''
    '''Required AMAZON_REGION, AMAZON_ACCESS_KEY_ID, SECRET_ACCESS_KEY in env vars ''' 

    conn = sqs.connect_to_region(
              os.environ['AMAZON_REGION'],
              aws_access_key_id=os.environ['AMAZON_ACCESS_KEY_ID'],
              aws_secret_access_key=os.environ['SECRET_ACCESS_KEY'])
    ops_queue = conn.get_queue(queue)
    return ops_queue

def write_to_sqs(queue_name, message):
    '''Write to sqs queue '''

    mail_queue = sqs_connection(queue_name)
    m = sqs.message.Message()
    data = message
    m.set_body(data)
    status = mail_queue.write(m)
    return status

def read_file_s3(file_name, bucket_name):
   '''Reading from S3 file, storing it locally in tmp '''

   import tempfile
   from boto.s3.connection import S3Connection
   conn = S3Connection(os.environ['AMAZON_ACCESS_KEY_ID'], os.environ['SECRET_ACCESS_KEY'])

   bucket = conn.get_bucket(bucket_name)
   res = bucket.get_key(file_name)
   if not res: return False
   temp_dir = tempfile.mkdtemp()
   res.get_contents_to_filename(temp_dir+file_name)

   with open(temp_dir+file_name, 'rb') as csvfile:
        stock_rows = csv.reader(csvfile)
        stock_rows.next()
        rows = [row for row in stock_rows]

   return rows

#generic
def to_json(obj):
    '''Convert object to datetime '''

    import json,datetime
    from decimal import Decimal
    def default(obj):
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()[:16]
        if isinstance(obj, Decimal):
            return int(obj)
        raise ValueError("Can't convert: %s" % repr(obj))
    return json.dumps(obj, default=default)

def str_to_hex(text):
    '''Converting arabic text to hex for sending as sms ''' 

    text = text.strip("u").strip("'") 
    arabic_hex = [hex(ord(b)).replace("x","").upper().zfill(4) for b in text]
    arabic_hex.append("000A")
    text_update = "".join(arabic_hex)
    return text_update

def yaml_loader(filename): 
    '''Generate a dict from yml/twig file '''
    '''Send file name along with path '''

    import yaml
    f = open(filename)
    yml_dict = yaml.safe_load(f)
    f.close()
    return yml_dict

def pushformatter(param):
    '''Format contact number'''
    try:
        param = str(param)
    except UnicodeEncodeError:
       return None
    number=param.translate(None,'+').translate(None,'-')
    if number[:3]=='971':
       dialstring='00'+number
       return dialstring
    elif number[:2]=='00':
        return number
    else:
        dialstring='00'+number
        return dialstring

def generate(items):
    '''Push content to CSV file '''

    for row in items:
        li = []
        for r in row:
            val = str(r[1]) or ''
            li.append(str(val.replace(',','/')))
        yield ','.join(li) + '\n'

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

def generate_unicode(items):
   '''Unicode support '''

   for row in items:
       li = []
       for r in row:
           val = (unicode(r[1]).encode("utf-8")) if r else ''
           li.append((val.replace(',','/')))
       yield ','.join(li) + '\n'

class OrderedDefaultDict(OrderedDict):
    '''Arranging nested Dictionary in default order'''

    def __init__(self, default_factory=None, *args, **kwargs):
        super(OrderedDefaultDict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        val = self[key] = self.default_factory()
        return val

def csv_reader(file):
    import csv
    '''Reading csv and creating Dict'''

    order_items = OrderedDefaultDict(OrderedDict)
    csv_file = file
    reader = csv.reader(csv_file)
    header = reader.next()
    for row in reader:
        try: row[1]
        except IndexError: print("CSV formatting error, update the row resave the file and upload: %s"%(row))
        order_items[row[0]][row[1]] = OrderedDict(zip(header, row))
    return order_items

def chunker(seq, size):
    '''break data structure to mentioned sized chunks'''

    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def update_timestamp(key, timestamp):
    '''update the redis key with timestamp'''

    import hirlite
    rlite = hirlite.Rlite(path='timer.rld')
    rlite.command('set', key, timestamp)

def get_timestamp(key):
    '''Fetch last runtime'''

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

#geckoboard
def update_geckoboard_text(widget_key, text):
    '''Update text widget on Gecko ''' 
    import os, requests
    geckourl = "https://push.geckoboard.com/v1/send/"+widget_key
    gecko_post = requests.post(geckourl, data=json.dumps({"api_key":os.environ['APIKEY'], "data": {"item":[{"text":text}]} }),
           headers={'Content-Type': 'application/json'})
    return gecko_post

#flask
def stream_template(app, template_name, **context):
    '''Stream Flask templates '''

    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv

#rabbit
@memoize(expiry_time=60*30)
def rabbit_connect():
    '''Connect to Rabbit '''

    import pika
    import pika_pool

    pool = pika_pool.QueuedPool(
     create=lambda: pika.BlockingConnection(parameters=pika.URLParameters(os.environ['RABBIT_CRED'])),
     max_size=10,
     max_overflow=10,
     timeout=10,
     recycle=3600,
     stale=45,
    )
    return pool

def rabbit_publish(payload):
    '''Publish to Rabbit MQ '''

    with pool.acquire() as cxn:
       message = cxn.channel.basic_publish(exchange='',                                                                                    
                      routing_key=os.environ['ROUTING_KEY'],
                      body = json.dumps(payload), mandatory = True)

#dropbox
def read_file_dropbox(file_name):
    '''Fetch file from dropbox, if not present return None, once read move file to archive ''' 

    import dropbox
    access_token = os.environ['DROPBOX_TOKEN']
    print("Reading File: %s"%(file_name))
    client = dropbox.client.DropboxClient(access_token)

    try:
      f, metadata = client.get_file_and_metadata('/%s'%(file_name))
      return f
    except dropbox.rest.ErrorResponse as e:
      return  

def write_file_dropbox(temp_dir,file_name):
    '''push files to dropbox'''

    import dropbox
    access_token = os.environ['DROPBOX_TOKEN']
    client = dropbox.client.DropboxClient(access_token)
    f = open(temp_dir+file_name, 'rb')
    response = client.put_file('/%s'%(file_name), f, overwrite=False)
    f.close()
    return response

def dropbox_to_local(file_name):
    '''Fetch file from dropbox, copying content to local system, move file to archive '''

    import tempfile
    import dropbox
    import csv
    from datetime import datetime

    access_token = os.environ['DROPBOX_TOKEN']
    client = dropbox.client.DropboxClient(access_token)

    f = read_file_dropbox(file_name)
    if not f: return None
    temp_dir = tempfile.mkdtemp()

    out = open(temp_dir+file_name, 'wb')
    out.write(f.read())
    out.close()

    with open(temp_dir+file_name, 'r', encoding='ascii',errors='ignore') as csvfile:
        rows = csv.reader(csvfile)
        data = [row for row in rows]

    client.file_move('/%s'%(file_name), \
               '/archive/%s_%s'%(str(datetime.utcnow()).replace(" ", "_"), file_name))
    return data

#sqlalchemy/db
def create_record(engine, query, **kwargs):
    '''Executing Queries mysql '''

    from sqlalchemy.sql import text
    if isinstance(engine, basestring):
        engine = get_engine(engine)
    is_session = 'session' in repr(engine.__class__)
    q = text(query.format(**kwargs))
    result = engine.execute(q, params=kwargs) if is_session else engine.execute(q, **kwargs)
    return True

def insert_into(engine, table_name, values):
    '''For inserting data into DB, on duplicate key update '''
    import sqlalchemy
    engine = sqlalchemy.create_engine(engine)
    metadata = sqlalchemy.MetaData(bind=engine)
    table = sqlalchemy.Table(table_name, metadata, autoload=True)

    if not values: return
    table = metadata.tables[table_name]
    for row in values:
        columns = list(set(table._columns.keys()) & set(row.keys()))
        query = sqlalchemy.text("INSERT INTO `{}` ({}) VALUES ({}) ON DUPLICATE KEY UPDATE {}".format(table_name, ", ".join(columns), ", ".join(":" + c for c in columns), ", ".join("{}=VALUES({})".format(c, c) for c in columns)))
        engine.execute(query, row)
    return engine

def get_engine(e):
    '''fetch sql engine'''

    from sqlalchemy import create_engine
    conn = create_engine(e, pool_recycle=60, max_overflow=0, pool_timeout=30)
    return conn.connect()

def get_results_as_dict(*args, **kwargs):
    '''return sql data'''

    return list(get_results_as_dict_iter(*args, **kwargs))

def get_results_as_dict_iter(engine, query, dict=dict, engines={}, **kwargs):
    '''fetch results from sql read query '''

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
    engine.close()
    engine.engine.dispose()
    keys = result.keys()
    for r in result:
        yield dict((k, v) for k, v in zip(keys, r))

def write_to_db(db, table_name, trunc, records, *args, **kwargs):
    '''update data to mysql table'''
    import sqlalchemy

    conn = sqlalchemy.create_engine(db, pool_recycle=60, max_overflow=0, pool_timeout=30)
    engine = conn.connect()

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

    if trunc:
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

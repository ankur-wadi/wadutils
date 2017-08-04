class memoize(object):
   def __init__(self, cache=None, expiry_time=0, num_args=None, locked=False):
       import threading
       self.cache = {} if cache is None else cache
       self.expiry_time = expiry_time
       self.num_args = num_args
       self.lock = threading.Lock() if locked else None

   def __call__(self, func):
       import time
       def wrapped(*args):
           mem_args = args[:self.num_args]
           if mem_args in self.cache:
               result, timestamp = self.cache[mem_args]
               age = time.time() - timestamp
               if not self.expiry_time or age < self.expiry_time:
                   return result
           result = func(*args)
           self.cache[mem_args] = (result, time.time())
           return result
       def locked_wrapped(*args):
           with self.lock:
               return wrapped(*args)
       return wrapped if self.lock is None else locked_wrapped



def _format_query_tuple_list_key(key, query, params):
    values = params.pop(key[1:])
    new_keys = []
    for i, value in enumerate(values):
        new_key = '{}_{}'.format(key, i)
        assert isinstance(value, tuple)
        new_keys2 = []
        for i, tuple_val in enumerate(value):
            new_key2 = '{}_{}'.format(new_key, i)
            new_keys2.append(new_key2)
            params[new_key2[1:]] = tuple_val
        new_keys.append("({})".format(", ".join(new_keys2)))
    new_keys_str = ", ".join(new_keys) or "null"
    query = query.replace(key, "({})".format(new_keys_str))
    return query, params

def _format_query_list_key(key, query, params):
    values = params.pop(key[1:])
    new_keys = []
    for i, value in enumerate(values):
        new_key = '{}_{}'.format(key, i)
        new_keys.append(new_key)
        params[new_key[1:]] = value
    new_keys_str = ", ".join(new_keys) or "null"
    query = query.replace(key, "({})".format(new_keys_str))
    return query, params

def format_query_with_list_params(query, params):
    import re
    keys = set(re.findall("(?P<key>:[a-zA-Z_]+_list)", query))
    for key in keys:
        if key.endswith('_tuple_list'):
            query, params = _format_query_tuple_list_key(key, query, params)
        else:
            query, params = _format_query_list_key(key, query, params)
    return query, params

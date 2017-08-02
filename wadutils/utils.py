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

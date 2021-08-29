# -*- coding: utf-8 -*-
"""
Created on Sun Aug 15 12:37:29 2021

@author: Parviz.Asoodehfard
"""

from functools import wraps
import logging
level = 0

def my_logging(log_type, msg):
    print('>>>',log_type,msg)
    if log_type == 'info':
        logging.info(msg)
    elif log_type == 'error':
        logging.error(msg)   

        

def my_logger(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        global level
        if '__self__' in dir(func):
            func_class = func.__self__.__class__
        else:
            func_class = 'main'
        msg = ' '.join([func_class,func.__name__, '<__', 'input:']+[str(a) for a in args]+[str(kwa) for kwa in kwargs])
        try:
            print('  '*level,level,'\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\')
            my_logging('  '*level+'info',msg)
            level += 1
            result = func(*args,**kwargs)
            return result
        finally:
            level -= 1
            msg = ' '.join([func_class,func.__name__, '__>', 'result:',str(result)])
            my_logging('  '*level+'info',msg)
            print('  '*level,level,'/////////////////////////////////////')

    return wrapper
    


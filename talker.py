# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 10:44:02 2021

@author: Parviz.Asoodehfard
"""
try:
    import init
except:
    pass
import telepot
import os
try:
    bot = telepot.Bot(os.environ['tlg_token'])
    bot.sendMessage(91686406,'started')
    
    import time
    from io import StringIO
    import boto3
    import os 
    import pandas as pd
    #from datetime import date
    from pytz import timezone
    import datetime
    #from datetime import datetime
    import utility
    
    if __name__ == "__main__":
        bot = telepot.Bot(os.environ['tlg_token'])
        while True:
            curr_time = datetime.datetime.now().astimezone(timezone('America/Denver'))
            if 7 < curr_time.hour < 22:
                curr_date = curr_time.date()
                
                tasks_to_send = reading_task_to_send()
                
                for idx,row in tasks_to_send.iterrows():
                    bot.sendMessage(91686406,str(row['id'])+'  '+row['name'])
                    print(row['name'])
            time.sleep(3000)                   
    bot.sendMessage(91686406,'end') 
except Exception as e:
    bot = telepot.Bot(os.environ['tlg_token'])
    bot.sendMessage(91686406,str(e))

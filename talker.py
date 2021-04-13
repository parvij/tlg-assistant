# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 10:44:02 2021

@author: Parviz.Asoodehfard
"""
import telepot
import os

try:
    bot = telepot.Bot(os.environ['tlg_token'])
    bot.sendMessage(91686406,'started')
    
    import time
    import os 
    from pytz import timezone
    import datetime
    import utility
    
    if __name__ == "__main__":
        bot = telepot.Bot(os.environ['tlg_token'])
        while True:
            curr_time = datetime.datetime.now().astimezone(timezone('America/Denver'))
            if 7 < curr_time.hour < 22:
                curr_date = curr_time.date()
                
                tasks_to_send = utility.reading_task_to_send()
                
                for idx,row in tasks_to_send.iterrows():
                    bot.sendMessage(91686406,str(row['id'])+'  '+row['name'])
                    print(row['name'])
            time.sleep(3000)                   
    bot.sendMessage(91686406,'end') 
except Exception as e:
    bot = telepot.Bot(os.environ['tlg_token'])
    bot.sendMessage(91686406,str(e))

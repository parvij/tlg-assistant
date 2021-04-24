# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 10:44:02 2021

@author: Parviz.Asoodehfard
"""

try:
    import os
    import time
    import datetime
    import telepot
    bot = telepot.Bot(os.environ['tlg_token'])    
    def send_message(user_id,msg):
        bot.sendMessage(user_id,msg)

    send_message(91686406,'talker started')
    
    import business_layer as bl
    
    
    
    
    
    
    
    
    
    if __name__ == "__main__":
        while True:
            for user_id in bl.user_id_list():
               if datetime.datetime.strptime('6:00', '%H:%M').time() < bl.get_time() < datetime.datetime.strptime('23:59', '%H:%M').time():
                    busy_time_df = bl.reading_busy_time()
                    print('###',busy_time_df.apply(lambda r:r.start_time < bl.get_time() < r.end_time, axis=1).sum())
                    print(bl.get_time(),busy_time_df.start_time,busy_time_df.end_time)
                    if busy_time_df.apply(lambda r:r.start_time < bl.get_time() < r.end_time, axis=1).sum() == 0 :                    
                        tasks_to_send = bl.reading_task_to_send(user_id)
                        print('$$$',tasks_to_send)
                        msg1 = '\n'.join([str(row['id'])+'  '+row['name']   for idx,row in tasks_to_send[tasks_to_send.repeat != 'Once'].iterrows()])
                        if msg1!= '':
                            send_message(user_id,msg1)
                        msg2 = '\n'.join([str(row['id'])+'  '+row['name']   for idx,row in tasks_to_send[tasks_to_send.repeat == 'Once'].iterrows()])
                        if msg2!= '':
                            send_message(user_id,msg2)

            time.sleep(int(os.environ['sleep_time']))                   
except Exception as e:
    send_message(91686406,'Error :\n'+str(e))
    
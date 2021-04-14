# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 10:44:02 2021

@author: Parviz.Asoodehfard
"""

try:
    import utility
    utility.send_message('started')

    import time
    from pytz import timezone
    import datetime
    
    if __name__ == "__main__":
        while True:

            curr_time = datetime.datetime.now().astimezone(timezone('America/Denver'))
            
            if datetime.datetime.strptime('7:00', '%H:%M').time() < curr_time.time() < datetime.datetime.strptime('22:00', '%H:%M').time():
                busy_time_df = utility.reading_busy_time()
                print('###',busy_time_df.apply(lambda r:r.start_time < curr_time.time() < r.end_time, axis=1))
                if busy_time_df.apply(lambda r:r.start_time < curr_time.time() < r.end_time, axis=1).sum() == 0 :
                    curr_date = curr_time.date()
                    
                    tasks_to_send = utility.reading_task_to_send()
                    print('$$$',tasks_to_send)
                    for idx,row in tasks_to_send.iterrows():
                        utility.send_message(str(row['id'])+'  '+row['name'])
                        print(row['name'])
            time.sleep(3000)                   
except Exception as e:
    utility.send_message(str(e))
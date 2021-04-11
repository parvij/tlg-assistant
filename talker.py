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
    from datetime import date
    from datetime import datetime
    
    s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
    
    
    if __name__ == "__main__":
        bot = telepot.Bot(os.environ['tlg_token'])
        while True:
            s3_object = s3_resource.Object(bucket_name='parvij-assistance', key='tasks.csv')
            s3_data = StringIO(s3_object.get()['Body'].read().decode('utf-8'))
            tasks_df = pd.read_csv(s3_data)

            s3_object = s3_resource.Object(bucket_name='parvij-assistance', key='have_done.csv')
            s3_data = StringIO(s3_object.get()['Body'].read().decode('utf-8'))
            have_done_df = pd.read_csv(s3_data)


            #started
            tasks_to_send1 = tasks_df[tasks_df.start.apply(lambda x:datetime.strptime(x, '%m/%d/%Y').date()<=date.today())]
            done_tody = have_done_df[have_done_df.date.apply(lambda x:datetime.strptime(x, '%m/%d/%Y').date()==date.today())].task_id.to_list()
            tasks_to_send2 = tasks_to_send1[tasks_to_send1.id.apply(lambda x: x not in done_tody)]

            tasks_to_send = tasks_to_send2[tasks_to_send2.Periority == tasks_to_send2.Periority.min()]
            
            for idx,row in tasks_to_send.iterrows():
                bot.sendMessage(91686406,row['name'])
                print(row['name'])
            time.sleep(3000)                   
    bot.sendMessage(91686406,'end') 
except Exception as e:
    bot = telepot.Bot(os.environ['tlg_token'])
    bot.sendMessage(91686406,str(e))

try:
    import init
except:
    pass
import pandas as pd

import boto3
from io import StringIO  # python3 (or BytesIO for python2)
import os
from pytz import timezone
import datetime


import telepot
bot = telepot.Bot(os.environ['tlg_token'])


def writing_file(df,filename):
    print('writeing file')
    try:
        bucket = 'parvij-assistance'  # already created on S3
        csv_buffer = StringIO()
        df.to_csv(csv_buffer,index=False)
        s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
        s3_resource.Object(bucket, filename).put(Body=csv_buffer.getvalue())
    except:
        df.to_csv(filename,index=False)

def reading_file(filename):
    print('reading file')
    try:
        s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
        s3_object = s3_resource.Object(bucket_name='parvij-assistance', key=filename)
        s3_data = StringIO(s3_object.get()['Body'].read().decode('utf-8'))
        df = pd.read_csv(s3_data)
    except:
        df = pd.read_csv(filename)
    return df

################################################################



def reading_task_to_send():
    have_done_df = reading_file('have_done.csv')
    tasks_df = reading_file('tasks.csv')
    curr_date = datetime.datetime.now().astimezone(timezone('America/Denver')).date()

    #started
    tasks_to_send1 = tasks_df[tasks_df.start.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()<=curr_date)]
    done_today = have_done_df[have_done_df.date.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()==curr_date)].task_id.to_list()
    done_once = have_done_df.task_id.to_list()
    tasks_to_send2 = tasks_to_send1[tasks_to_send1.id.apply(lambda x: x not in done_today)]
    tasks_to_send3 = tasks_to_send2[(tasks_to_send1.repeat !='Once') | (tasks_to_send1.id.apply(lambda x: x not in done_once))]


    tasks_to_send = tasks_to_send3[(tasks_to_send3.Periority == tasks_to_send3.Periority.min())|(tasks_to_send3.repeat=='Once')]
    return tasks_to_send

def reading_busy_time():
    df = reading_file('busy_time.csv')
    curr_date = datetime.datetime.now().astimezone(timezone('America/Denver')).date()
    df = df[ df.apply(lambda r: (r.start_date!=r.start_date or r.start_date<curr_date )and (r.end_date!=r.end_date or r.end_date<curr_date ),axis=1) ]
    df.start_time = df.start_time.apply(lambda x: datetime.datetime.strptime(x if x == x else '0:0', '%H:%M').time())
    df.end_time = df.end_time.apply(lambda x: datetime.datetime.strptime(x if x==x else '23:59', '%H:%M').time())
    return df

#####################################################################################
def send_message(msg):
    bot.sendMessage(91686406,msg)
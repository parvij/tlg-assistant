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

def writing_file(df,filename, env = None):
    print('writeing file')
    
    if not env:
        env = os.environ['env']
        
    if env == 'heroku':
        bucket = 'parvij-assistance'  # already created on S3
        csv_buffer = StringIO()
        df.to_csv(csv_buffer,index=False)
        s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
        s3_resource.Object(bucket, filename).put(Body=csv_buffer.getvalue())
    elif env == 'local':
        df.to_csv(filename,index=False)
    else:
        print(f'problem with reading ENV. The ENV is {env}')
        raise

def reading_file(filename, env = None):
    print('reading file')
    if not env:
        env = os.environ['env']
        
    if env == 'heroku':
        s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
        s3_object = s3_resource.Object(bucket_name='parvij-assistance', key=filename)
        s3_data = StringIO(s3_object.get()['Body'].read().decode('utf-8'))
        df = pd.read_csv(s3_data)
    elif env == 'local':
        df = pd.read_csv(filename)
    else:
        print(f'problem with reading ENV. The ENV is {env}')
        raise
    
    for c in ['id','task_id','Priotory','']:
        try:
            df[c] = df[c].apply(int)
        except:
            pass
    
    return df

################################################################



def reading_task_to_send():
    have_done_df = reading_file('have_done.csv')
    tasks_df = reading_file('tasks.csv')
    
    done_today = have_done_df[have_done_df.date.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()==get_today())].task_id.to_list()

    done_once = have_done_df.task_id.to_list()
    
    how_many_time_done = have_done_df[have_done_df.date.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()>get_today()- datetime.timedelta(days=3))].task_id.value_counts().reset_index()
    how_many_time_done.columns = ['id','cnt_done']
    how_many_time_done.id = how_many_time_done.id.apply(int)

    # started
    df1 = tasks_df[tasks_df.start.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()<=get_today())]
    # have_not_done
    df2 = df1[df1.id.apply(lambda x: x not in done_today)]
    # filter the "Once" which have done
    df3 = df2[(df2.repeat !='Once') | (df2.id.apply(lambda x: x not in done_once))]
    # join with how_many_time_done
    df4 = pd.merge(df3,how_many_time_done,on='id',how='left')
    df4.cnt_done.fillna(0,inplace=True)

    # min periority or Once    
    tasks_to_send = pd.concat([df4.sort_values(['Periority','cnt_done']).head(5),df4[df4.repeat=='Once']]).drop_duplicates().reset_index(drop=True).sort_values(['Periority','cnt_done'])
    return tasks_to_send

def reading_busy_time():
    df = reading_file('busy_time.csv')
    df = df[ df.apply(lambda r: (r.start_date!=r.start_date or r.start_date<get_today() )and (r.end_date!=r.end_date or r.end_date<get_today() ),axis=1) ]
    df.start_time = df.start_time.apply(lambda x: datetime.datetime.strptime(x if x == x else '0:0', '%H:%M').time())
    df.end_time = df.end_time.apply(lambda x: datetime.datetime.strptime(x if x==x else '23:59', '%H:%M').time())
    return df

#####################################################################################
def send_message(msg):
    bot.sendMessage(91686406,msg)
    
def get_today():
    return (datetime.datetime.now().astimezone(timezone('America/Toronto'))+ datetime.timedelta(hours=-2)).date()

def get_time():
    return datetime.datetime.now().astimezone(timezone('America/Toronto')).time()




    
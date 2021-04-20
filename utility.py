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
from datetime import timedelta
import dateutil.parser

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
    for c in ['start','date','end']:
        try:
            df[c] = df[c].apply(lambda x:dateutil.parser.parse(x).date())
        except:
            print(f'{c} was not a date type')
    
    return df

################################################################

def done_period(val):
    rp_n = val.split('-')
    repeat = rp_n[0]
    n = 0
    if len(rp_n) >1:
        n = int(rp_n[1])-1
    
    if repeat == 'Once':
        return datetime.datetime.strptime('2000', '%Y').date()
    elif repeat == 'Daily':
        return get_today() - datetime.timedelta(days=n)
    elif repeat == 'Weekly':
        return get_today() - timedelta(days=get_today().weekday()) - datetime.timedelta(days=n*7)
    elif repeat == 'Monthly':
        return get_today() - timedelta(days=get_today().day) - datetime.timedelta(days=n*30)
    else:
        return get_today()

def unchecked_tasks():
    have_done_df = reading_file('have_done.csv')
    have_done_df = have_done_df[(have_done_df.type != 'Postponed') | (have_done_df.date == get_today())]
    last_have_done_df = have_done_df.groupby(['task_id']).date.max().reset_index()
    last_have_done_df.columns = ['id','done_date']
    
    tasks_df = reading_file('tasks.csv')
    times_df = reading_file('times.csv')
    
    tasks_times_df = pd.merge(tasks_df, times_df, left_on='duration', right_on='name', how='left', suffixes=('', '_y'))
    tasks_times_df['start time'] = tasks_times_df['start time'].apply(int)
    tasks_times_df['end time'] = tasks_times_df['end time'].apply(int)
    
    tasks_for_now = tasks_times_df[(get_time().hour >= tasks_times_df['start time']) & 
                                   (get_time().hour <= tasks_times_df['end time']) & 
                                   (tasks_times_df['days'].apply(lambda x: str(get_today().weekday()) in x))]
    
    tasks_df = tasks_for_now.drop(['id_y','name_y','start time','end time', 'days'],axis=1).drop_duplicates()
    
    
    started_tasks = tasks_df[tasks_df.start.apply(lambda x: x <= get_today())]
    
    
    tasks_df_with_done = pd.merge(started_tasks, last_have_done_df, how='left',on='id')
    tasks_df_with_done['done_date'].fillna(datetime.datetime.strptime('1900', '%Y').date(),inplace=True)
    full_tasks_df = tasks_df_with_done
    full_tasks_df['expect_to_done'] = full_tasks_df.repeat.apply(done_period)
        
    df_final = full_tasks_df[full_tasks_df.eval('done_date < expect_to_done')]
    
    return df_final 

def reading_task_to_send():
    df3 = unchecked_tasks()

    have_done_df = reading_file('have_done.csv')
    how_many_time_done = have_done_df[have_done_df.date.apply(lambda x: x >get_today()- datetime.timedelta(days=3))].task_id.value_counts().reset_index()
    how_many_time_done.columns = ['id','cnt_done']
    how_many_time_done.id = how_many_time_done.id.apply(int)

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




    
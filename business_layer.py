# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 18:21:07 2021

@author: Parviz.Asoodehfard
"""


from pytz import timezone
import datetime
from datetime import timedelta
import data_layer as dl
import pandas as pd
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

def get_tasks_list(user_id,category='not_done & current & start_end & short'):
    category = category.split(' & ')
    print('starting unchecked_tasks')
    
    tasks_df = dl.reading_file('tasks.csv',user_id = user_id)
    tasks_df = tasks_df[tasks_df.status=='active']
    print(len(tasks_df))

    if 'current' in category:
        times_df = dl.reading_file('times.csv')
        tasks_times_df = pd.merge(tasks_df, times_df, left_on='duration', right_on='name', how='left', suffixes=('', '_y'))
        tasks_times_df['start time'] = tasks_times_df['start time'].fillna(0).apply(int)
        tasks_times_df['end time'] = tasks_times_df['end time'].fillna(24).apply(int)
        tasks_for_now = tasks_times_df[(get_time().hour >= tasks_times_df['start time']) & 
                                       (get_time().hour <= tasks_times_df['end time']) & 
                                       (tasks_times_df['days'].apply(lambda x: str(get_today().weekday()) in str(x)))]
        tasks_df = tasks_for_now.drop(['id_y','name_y','start time','end time', 'days'],axis=1).drop_duplicates()
    
    if 'start_end' in category:
        tasks_df = tasks_df.loc[tasks_df.start_date.apply(lambda x: x <= get_today())]
    

    if 'not_done' in category:
        have_done_df = dl.reading_file('have_done.csv',user_id = user_id)
        have_done_df = have_done_df[(have_done_df.type != 'Postponed') | (have_done_df.date == get_today())]
        last_have_done_df = have_done_df.groupby(['task_id']).date.max().reset_index()
        last_have_done_df.columns = ['id','done_date']
        
        tasks_df_with_done = pd.merge(tasks_df, last_have_done_df, how='left',on='id')
        tasks_df_with_done['done_date'].fillna(datetime.datetime.strptime('1900', '%Y').date(),inplace=True)
        full_tasks_df = tasks_df_with_done
        full_tasks_df['expect_to_done'] = full_tasks_df.repeat.apply(done_period)
    
        tasks_df = full_tasks_df[full_tasks_df.eval('done_date < expect_to_done')]
    
    if 'short' in category:
        have_done_df = dl.reading_file('have_done.csv')
        how_many_time_done = have_done_df[have_done_df.date.apply(lambda x: x >get_today()- datetime.timedelta(days=3))].task_id.value_counts().reset_index()
        how_many_time_done.columns = ['id','cnt_done']
        how_many_time_done.id = how_many_time_done.id.apply(int)
    
        # join with how_many_time_done
        df4 = pd.merge(tasks_df,how_many_time_done,on='id',how='left')
        df4.cnt_done.fillna(0,inplace=True)
    
        # min periority or Once    
        tasks_df = pd.concat([df4[df4.repeat!='Once'].sort_values(['Periority','cnt_done']).head(5),
                                   df4[df4.repeat=='Once']]
                                  ).reset_index(drop=True).sort_values(['Periority','cnt_done'])    
    
    print('unchecked_tasks done.')
    return tasks_df[['id','name']]

def reading_busy_time():
    df = dl.reading_file('busy_time.csv')
    df = df[ df.apply(lambda r: (r.start_date!=r.start_date or r.start_date<get_today() )and (r.end_date!=r.end_date or r.end_date<get_today() ),axis=1) ]
    df.start_time = df.start_time.apply(lambda x: datetime.datetime.strptime(x if x == x else '0:0', '%H:%M').time())
    df.end_time = df.end_time.apply(lambda x: datetime.datetime.strptime(x if x==x else '23:59', '%H:%M').time())
    return df

def user_id_list():
    df = dl.reading_file('users.csv')
    return df.id.to_list()

def get_today():
    return (datetime.datetime.now().astimezone(timezone('America/Toronto'))+ datetime.timedelta(hours=-2)).date()

def get_time():
    #return datetime.datetime.strptime('8:0', '%H:%M').time()
    return datetime.datetime.now().astimezone(timezone('America/Toronto')).time()


def change_status(val,text,user_id):
    if text.isnumeric():
        df = dl.reading_file('have_done.csv')
        df = df.append({'task_id': int(text),'date':get_today(),'type':val,'group_id':user_id}, ignore_index=True)
        dl.writing_file(df,'have_done.csv')
        return 'Done'
    else:
        return 'It is not a number'
    
def adding_task(text,group_id,owner_id):
    
    df = dl.reading_file('tasks.csv')
    #id	name	time_cost	time	repeat	start	weekend	Why	Periority
    new_id = df.id.max()+1
    df = df[(df.status=='active') | (df.owner_id!= int(owner_id))]
    df = df.append({'id':new_id ,
                    'name':text,
                    'repeat':'Once', 
                    'start_date':get_today(),
                    'duration':'Free time',
                    'Periority':1,
                    'group_id':group_id, 
                    'status':'inactive',
                    'owner_id':owner_id,
                    }, ignore_index=True)
    dl.writing_file(df,'tasks.csv')
    
    return new_id

def updating_inactive_task(update_dict,owner_id):
    df = dl.reading_file('tasks.csv')
    #id	name	time_cost	time	repeat	start	weekend	Why	Periority
    new_task = df[(df.status=='inactive') & (df.owner_id == int(owner_id))].iloc[0]
    df = df[(df.status!='inactive') | (df.owner_id!=int(owner_id))]
    for c in update_dict.keys():
        new_task[c] = update_dict[c]
    print(new_task)
    df = df.append(new_task, ignore_index=True)
    dl.writing_file(df,'tasks.csv')
    return new_task.id
    


def all_task():
    return 'not available now'


def get_task_info(task_id):
    df = dl.reading_file('tasks.csv')
    df = df[df.id == task_id]
    df_group = dl.reading_file('user_group.csv')[['group_id','branch_name']].drop_duplicates()
    
    df = pd.merge(df,df_group,on = 'group_id')
    return df.iloc[0]


def get_groups(user_id):
    df = dl.reading_file('user_group.csv')
    df = df[df.user_id == user_id]
    return df[['group_id','branch_name']]
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
import logging

################################################################
def my_logging(log_type, msg):
    print(log_type,msg)
    if log_type == 'info':
        logging.info(msg)
    elif log_type == 'error':
        logging.error(msg)
        
        
        
def done_period(row):
    val = row['repeat']
    #my_logging('info',' __Business__  done_period __> val:'+str(val))
    rp_n = val.split('-')
    repeat = rp_n[0]
    n = 0
    if len(rp_n) >1:
        n = int(rp_n[1])-1
    
    today_val = row.current_date
    if repeat == 'Once':
        result = datetime.datetime.strptime('2000', '%Y').date()
    elif repeat == 'Daily':
        result = today_val - datetime.timedelta(days=n)
    elif repeat == 'Weekly':
        result = today_val - timedelta(days=today_val.weekday()) - datetime.timedelta(days=n*7)
    elif repeat == 'Monthly':
        result = today_val - timedelta(days=today_val.day) - datetime.timedelta(days=n*30)
    else:
        result = today_val
        
        
    #my_logging('info',' __Business__  done_period __> result:'+str(result))
    return result


#   get_tasks_list(owner_id = 91686406,category='not_done & current & start_end & short')
def get_tasks_list(owner_id,category='not_done & current & start_end & short'):
    my_logging('info',' __Business__  get_tasks_list __> owner_id:'+str(owner_id)+'| category:'+str(category))
    category = category.split(' & ')
    tasks_df = dl.reading_file('tasks.csv',user_id = owner_id)
    tasks_df = tasks_df[tasks_df.status=='active']
    today_val = get_today(owner_id = owner_id)
    hour_val = get_time(owner_id = owner_id)
    has_new = False
    if 'current' in category:
        times_df = dl.reading_file('times.csv')
        times_df = times_df.loc[times_df.owner_id == int(owner_id)]
        tasks_times_df = pd.merge(tasks_df, times_df, left_on='duration', right_on='title', how='left', suffixes=('', '_y'))
        tasks_times_df['start time'] = tasks_times_df['start time'].fillna(0).apply(int)
        tasks_times_df['end time'] = tasks_times_df['end time'].fillna(24).apply(int)
        tasks_for_now = tasks_times_df.loc[(hour_val.hour >= tasks_times_df['start time']) & 
                                           (hour_val.hour <= tasks_times_df['end time']) & 
                                           (tasks_times_df['days'].apply(lambda x: str(today_val.weekday()) in str(x)))]
        has_new = len(tasks_for_now.loc[hour_val.hour== tasks_times_df['start time']]) > 0
        tasks_df = tasks_for_now.drop(['id_y','title','start time','end time', 'days'],axis=1).drop_duplicates()
    if 'start_end' in category:
        tasks_df = tasks_df.loc[tasks_df.start_date.apply(lambda x: x <= today_val)]

    if 'not_done' in category and len(tasks_df)>0:
        have_done_df = dl.reading_file('have_done.csv')
        have_done_df = have_done_df.loc[(have_done_df.type == 'Done') | (have_done_df.date == today_val)]
        last_have_done_df = have_done_df.groupby(['task_id']).date.max().reset_index()
        last_have_done_df.columns = ['id','done_date']
        
        tasks_df_with_done = pd.merge(tasks_df, last_have_done_df, how='left',on='id')
        tasks_df_with_done['done_date'].fillna(datetime.datetime.strptime('1900', '%Y').date(),inplace=True)
        full_tasks_df = tasks_df_with_done
        full_tasks_df['current_date'] = get_today(owner_id = full_tasks_df.owner_id.max())
        full_tasks_df['expect_to_done'] = full_tasks_df.apply(done_period,axis=1)
    
        tasks_df = full_tasks_df[full_tasks_df.eval('done_date < expect_to_done')]
        
    if 'short' in category:
        have_done_df = dl.reading_file('have_done.csv')
        how_many_time_done = have_done_df.loc[have_done_df.date.apply(lambda x: x >today_val- datetime.timedelta(days=3))].task_id.value_counts().reset_index()
        how_many_time_done.columns = ['id','cnt_done']
        how_many_time_done.id = how_many_time_done.id.apply(int)
    
        # join with how_many_time_done
        df4 = pd.merge(tasks_df,how_many_time_done,on='id',how='left')
        df4.cnt_done.fillna(0,inplace=True)
    
        # min periority or Once    
        tasks_df = pd.concat([df4[df4.repeat!='Once'].sort_values(['Periority','cnt_done']).head(5),
                                   df4[df4.repeat=='Once']]
                                  ).reset_index(drop=True).sort_values(['Periority','cnt_done'])    
    result = tasks_df[['id','name']]
    my_logging('info',' __Business__  get_tasks_list __> result:'+str(result))
    return result, has_new

# def reading_busy_time():
#     today_val = get_today()
#     df = dl.reading_file('busy_time.csv')
#     df = df[ df.apply(lambda r: (r.start_date!=r.start_date or r.start_date<today_val )and (r.end_date!=r.end_date or r.end_date<get_today() ),axis=1) ]
#     df.start_time = df.start_time.apply(lambda x: datetime.datetime.strptime(x if x == x else '0:0', '%H:%M').time())
#     df.end_time = df.end_time.apply(lambda x: datetime.datetime.strptime(x if x==x else '23:59', '%H:%M').time())
#     my_logging('info',' __Business__  reading_busy_time __> result:'+str(df))
#     return df

def user_id_list():
    df = dl.reading_file('users.csv')
    
    result = df.id.to_list()
    my_logging('info',' __Business__  user_id_list __> result:'+str(result))
    return result

def get_today(owner_id=None,diff_time=None):
    if not diff_time:
        if owner_id:
            df_users = dl.reading_file('users.csv')
            diff_time = df_users.loc[df_users.id == int(owner_id)].local_time_diff.max()            
        else:
            my_logging('error',' __Business__  get_today __> Error: owner_id and diff_time are empty')
            raise
    result = (datetime.datetime.now().astimezone(timezone('Etc/GMT0'))+ datetime.timedelta(hours=int(diff_time))+ datetime.timedelta(hours=-2)).date()
    #my_logging('info',' __Business__  get_today __> result:'+str(result))
    return result

def get_time(owner_id=None,diff_time=None):
    if not diff_time:
        if owner_id:
            df_users = dl.reading_file('users.csv')
            diff_time = df_users[df_users.id == int(owner_id)].local_time_diff.max()            
        else:
            my_logging('error',' __Business__  get_time __> Error: owner_id and diff_time are empty')
            raise
    result = (datetime.datetime.now().astimezone(timezone('Etc/GMT0')) + 
              datetime.timedelta(hours=int(diff_time))).time()
    my_logging('info',' __Business__  get_time __> result:'+str(result))
    return result


def change_status(val,text,owner_id):
    if text.isnumeric():
        df = dl.reading_file('have_done.csv')
        df = df.append({'task_id': int(text),'date':get_today(owner_id = owner_id),'type':val,'owner_id':owner_id}, ignore_index=True)
        dl.writing_file(df,'have_done.csv')
        result = 'Done'
    else:
        result = 'input is not a number'
        
    my_logging('info',' __Business__  change_status __> result:'+str(result))
    return result
    
def adding_task(text,group_id,owner_id):
    my_logging('info',' __Business__  adding_task __> text:'+str(text)+'| group_id:'+str(group_id)+'| owner_id:'+str(owner_id))
    
    df = dl.reading_file('tasks.csv')
    #id	name	time_cost	time	repeat	start	weekend	Why	Periority
    new_id = 1 if len(df) == 0 else df.id.max()+1
    df = df[(df.status=='active') | (df.owner_id!= int(owner_id))]
    df = df.append({'id':new_id ,
                    'name':text,
                    'repeat':'Once', 
                    'start_date':get_today(owner_id = owner_id),
                    'duration':'Free time',
                    'Periority':1,
                    'group_id':group_id, 
                    'status':'inactive',
                    'owner_id':owner_id,
                    }, ignore_index=True)
    dl.writing_file(df,'tasks.csv')
    my_logging('info',' __Business__  adding_task __> result:'+str(new_id))
    return new_id


def editing_task(task_id,owner_id):
    my_logging('info',' __Business__  editing_task __> task_id:'+str(task_id)+'| owner_id:'+str(owner_id))
    df = dl.reading_file('tasks.csv')
    df = df[(df.status=='active') | (df.owner_id!= int(owner_id))]
    row = df[df.id == int(task_id)]
    row['status'] = 'inactive'
    df = df.append(row, ignore_index=True)
    dl.writing_file(df,'tasks.csv')
    my_logging('info',' __Business__  editing_task __> result: this row has been added:'+str(row))

def updating_setting(update_dict,owner_id):        
    my_logging('info',' __Business__  updating_setting __> update_dict:'+str(update_dict)+'| owner_id:'+str(owner_id))
    df = dl.reading_file('users.csv')

    for key in update_dict.keys():
        df.loc[df['id'] == int(owner_id), key] = update_dict[key]
    
    dl.writing_file(df,'users.csv')
    my_logging('info',' __Business__  updating_setting __> result:'+str(df.loc[df['id'] == int(owner_id)]))



def updating_inactive_task(update_dict,owner_id):        
    my_logging('info',' __Business__  updating_inactive_task __> update_dict:'+str(update_dict)+'| owner_id:'+str(owner_id))
    df = dl.reading_file('tasks.csv')
    #id	name	time_cost	time	repeat	start	weekend	Why	Periority
    new_task = df[(df.status=='inactive') & (df.owner_id == int(owner_id))].iloc[0]

    if 'status' in update_dict.keys() and update_dict['status']=='active':
        df = df[df.id!=new_task.id]
    else:
        df = df[(df.status!='inactive') | (df.owner_id!=int(owner_id))]

    for c in update_dict.keys():
        new_task[c] = update_dict[c]
    df = df.append(new_task, ignore_index=True)
    dl.writing_file(df,'tasks.csv')
    my_logging('info',' __Business__  updating_inactive_task __> result:'+str(new_task.id))
    return new_task.id
    

def all_task():
    result = 'not available now'
    my_logging('info',' __Business__  all_task __> result:'+str(result))
    return result


def get_task_info(task_id):
    my_logging('info',' __Business__  get_task_info __> task_id:'+str(task_id))
    df = dl.reading_file('tasks.csv')
    df = df[df.id == int(task_id)]
    len_df = len(df)
    df['action'] = 'Add' if len_df == 1 else 'Edit'
    df = df[df.status == 'inactive']
    df_group = dl.reading_file('user_group.csv')[['group_id','branch_name']].drop_duplicates()
    
    df = pd.merge(df,df_group,on = 'group_id')
    
    result = df.iloc[0]
    my_logging('info',' __Business__  get_task_info __> result:'+str(result))
    return result


def get_groups(user_id):
    my_logging('info',' __Business__  get_groups __> user_id:'+str(user_id))
    df = dl.reading_file('user_group.csv')
    df = df[df.user_id == int(user_id)]
    
    result = df[['group_id','branch_name']]
    my_logging('info',' __Business__  get_groups __> result:'+str(result))
    return result

def get_durations(user_id):
    my_logging('info',' __Business__  get_durations __> user_id:'+str(user_id))
    df = dl.reading_file('times.csv')
    df = df[df.owner_id == int(user_id)]
    result = df
    my_logging('info',' __Business__  get_durations __> result:'+str(result))
    return result

def add_user_if_not_exist(owner_id,name):
    my_logging('info',' __Business__  add_user_if_not_exist __> owner_id:'+str(owner_id)+'| name:'+str(name))
    df_user = dl.reading_file('users.csv')
    if int(owner_id) not in df_user.id.to_list():
        new_user_row = {'id':owner_id,'name':name,'local_time_diff':'-4'}
        df_user = df_user.append(new_user_row, ignore_index=True)
        dl.writing_file(df_user,'users.csv')
        
        df_usergroup = dl.reading_file('user_group.csv')
        new_row = {'group_id':'P_'+owner_id,'user_id':owner_id, 'branch_name':'Personal'}
        df_usergroup = df_usergroup.append(new_row, ignore_index=True)
        dl.writing_file(df_usergroup,'user_group.csv')
        
        df_times = dl.reading_file('times.csv')
        max_id = df_times.id.max() if len(df_times)>0 else 0
        new_row = [{'id':max_id+1,'title':'All time','start time':7, 'end time':23,'days':"0,1,2,3,4,5,6",'owner_id':owner_id},
                  {'id':max_id+2,'title':'Free time','start time':7, 'end time':23,'days':"5,6",          'owner_id':owner_id},
                  {'id':max_id+3,'title':'Free time','start time':17,'end time':23,'days':"0,1,2,3,4",    'owner_id':owner_id},
                  {'id':max_id+3,'title':'Free time','start time':7, 'end time':7, 'days':"0,1,2,3,4",    'owner_id':owner_id},
                  {'id':max_id+4,'title':'Weekend',  'start time':7, 'end time':23,'days':"5,6",          'owner_id':owner_id}]
        df_times = df_times.append(new_row, ignore_index=True)
        dl.writing_file(df_times,'times.csv')
        
        my_logging('info',' __Business__  add_user_if_not_exist __> result: this rows has been added:'+str(new_row)+'|\n and this row: '+str(new_user_row))
        
    my_logging('info',' __Business__  add_user_if_not_exist __> result: user was not new')
    
    
def get_settings_dict(user_id):
    my_logging('info',' __Business__  add_user_if_not_exist __> owner_id:'+str(user_id))
    df_user = dl.reading_file('users.csv')
    setting_dict = df_user.loc[df_user.id == int(user_id)].drop(['id', 'name'], axis=1).iloc[0]
    my_logging('info',' __Business__  add_user_if_not_exist __> result: '+str(setting_dict))
    return setting_dict

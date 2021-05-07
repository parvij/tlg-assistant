# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 18:20:51 2021

@author: Parviz.Asoodehfard
"""
try:
    import init
except:
    pass
import os

import boto3
from io import StringIO  # python3 (or BytesIO for python2)
import pandas as pd
import dateutil.parser


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

def reading_file(filename, env = None, user_id=None):
    print(f'reading file {filename}')
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
    for c in df.columns:
        if 'date' in c:
            try:
                df[c] = df[c].apply(lambda x:dateutil.parser.parse(x).date())
            except:
                print(f'{c} was not a date type. sample:\n',df.iloc[0])
    
    
    if user_id:
        user_group_df = reading_file('user_group.csv')
        user_group_df = user_group_df[user_group_df.user_id == int(user_id)]
        groups = user_group_df.group_id.to_list()
        print(groups)
        df = df[df.group_id.apply(str).isin(groups)]
        print(df)
    print('reading done.')
    return df

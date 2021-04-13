def write_have_done(df):
    print('write file')
    bucket = 'parvij-assistance'  # already created on S3
    csv_buffer = StringIO()
    df.to_csv(csv_buffer,index=False)
    s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
    s3_resource.Object(bucket, 'have_done.csv').put(Body=csv_buffer.getvalue())

def reading_have_done():
    print('read file')
    s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
    s3_object = s3_resource.Object(bucket_name='parvij-assistance', key='have_done.csv')
    s3_data = StringIO(s3_object.get()['Body'].read().decode('utf-8'))
    df = pd.read_csv(s3_data)
    return df

def reading_tasks():
    print('read file')
    s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
    s3_object = s3_resource.Object(bucket_name='parvij-assistance', key='tasks.csv')
    s3_data = StringIO(s3_object.get()['Body'].read().decode('utf-8'))
    df = pd.read_csv(s3_data)
    return df
################################################################


def reading_task_to_send():
    have_done_df=reading_have_done()
    tasks_df = reading_tasks()


    #started
    tasks_to_send1 = tasks_df[tasks_df.start.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()<=curr_date)]
    done_tody = have_done_df[have_done_df.date.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()==curr_date)].task_id.to_list()
    tasks_to_send2 = tasks_to_send1[tasks_to_send1.id.apply(lambda x: x not in done_tody)]

    tasks_to_send = tasks_to_send2[tasks_to_send2.Periority == tasks_to_send2.Periority.min()]
    return tasks_to_send
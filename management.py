# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 10:44:02 2021

@author: Parviz.Asoodehfard
"""
#import logging
try:
    import init
except:
    pass
import pandas as pd
#from datetime import date
from pytz import timezone
import datetime
#from datetime import datetime
#import math
import boto3
from io import StringIO  # python3 (or BytesIO for python2)
import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

SELECTING_COMMAND = range(1)

def start(update: Update, context: CallbackContext) -> int:
    print('start')
    reply_keyboard = [['List of all Tasks', 'List of Unchecked'],[ 'Sleep..', 'Checking..']]
    update.message.reply_text('',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return SELECTING_COMMAND

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

def checking(update: Update, context: CallbackContext) -> int:
    print('cat selecting')
    text = update.message.text
    if text.isnumeric():
        df = reading_have_done()
        curr_date = datetime.datetime.now().astimezone(timezone('America/Denver')).date()
        df = df.append({'task_id': text,'date':curr_date.strftime('%m/%d/%Y')}, ignore_index=True)
        write_have_done(df)
        update.message.reply_text('Done')
    else:
        update.message.reply_text('It is not a number')
    
    return SELECTING_COMMAND
    


def cancel(update: Update, context: CallbackContext) -> int:
    print('cancel')
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def all_tasks():
    tasks_df = reading_tasks()

    tasks_to_send = tasks_df[tasks_df.start.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()<=curr_date)]
    list_all_tasks = tasks_to_send.apply(lambda r: str(r.id)+'_'+r.name,axis=1).to_list()
    update.message.reply_text('\n'.join(list_all_tasks))

    return SELECTING_COMMAND

def unchecked_tasks():
    have_done_df=reading_have_done()
    tasks_df = reading_tasks()

    tasks_to_send1 = tasks_df[tasks_df.start.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()<=curr_date)]
    done_tody = have_done_df[have_done_df.date.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()==curr_date)].task_id.to_list()
    tasks_to_send2 = tasks_to_send1[tasks_to_send1.id.apply(lambda x: x not in done_tody)]
    
    list_unchecked_tasks = tasks_to_send2.apply(lambda r: str(r.id)+'_'+r.name,axis=1).to_list()
    update.message.reply_text('\n'.join(list_unchecked_tasks))

    return SELECTING_COMMAND

def cat_selecting(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text == 'List of all Tasks':
        all_tasks()
        return SELECTING_COMMAND
    elif text == 'List of Unchecked':
        unchecked_tasks()
        return SELECTING_COMMAND
    elif text == 'Sleep..':
        #fill later
        return SELECTING_COMMAND
    elif text == 'Checking..':
        update.message.reply_text('which tasks you have done?')
        return CHECKING

def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(os.environ['tlg_token'], use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_COMMAND: [MessageHandler(Filters.regex('^(List of all Tasks|List of Unchecked|Sleep..|Checking..)$'), cat_selecting)],
            CHECKING: [MessageHandler(Filters.text, checking)],
#            PHOTO: [MessageHandler(Filters.photo, photo), CommandHandler('skip', skip_photo)],
#            LOCATION: [
#                MessageHandler(Filters.location, location),
#                CommandHandler('skip', skip_location),
#            ],
#            BIO: [MessageHandler(Filters.text & ~Filters.command, bio)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

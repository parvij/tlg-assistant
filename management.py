# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 10:44:02 2021

@author: Parviz.Asoodehfard
"""

import utility
from pytz import timezone
import datetime

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


SELECTING_COMMAND, CHECKING, NEW_TASK = range(3)

def start(update: Update, context: CallbackContext) -> int:
    print('start')
    reply_keyboard = [['List of all Tasks', 'List of Unchecked'],[ 'New Task', 'Checking..']]
    update.message.reply_text('Select your command',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return SELECTING_COMMAND

def checking(update: Update, context: CallbackContext) -> int:
    print('cat selecting')
    text = update.message.text
    if text.isnumeric():
        df = utility.reading_file('have_done.csv')
        curr_date = datetime.datetime.now().astimezone(timezone('America/Denver')).date()
        df = df.append({'task_id': text,'date':curr_date.strftime('%m/%d/%Y')}, ignore_index=True)
        utility.writing_file(df,'have_done.csv')
        update.message.reply_text('Done')
    else:
        update.message.reply_text('It is not a number')
    
    return SELECTING_COMMAND

def adding_task(update: Update, context: CallbackContext) -> int:
    print('adding_task')
    text = update.message.text
    df = utility.reading_file('tasks.csv')
    curr_date = datetime.datetime.now().astimezone(timezone('America/Denver')).date()
    #id	name	time_cost	time	repeat	start	weekend	Why	Periority
    
    df = df.append({'id': df.id.max()+1,'name':text,'repeat':'Once', 'start':curr_date.strftime('%m/%d/%Y'),'Periority':1}, ignore_index=True)
    utility.writing_file(df,'tasks.csv')
    update.message.reply_text('Done')
    
    return SELECTING_COMMAND
    


def cancel(update: Update, context: CallbackContext) -> int:
    print('cancel')
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def all_tasks(update):
    tasks_df = utility.reading_file('tasks.csv')
    curr_date = datetime.datetime.now().astimezone(timezone('America/Denver')).date()

    tasks_to_send = tasks_df[tasks_df.start.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()<=curr_date)]
    list_all_tasks = tasks_to_send.apply(lambda r: str(r['id'])+'_'+r['name'],axis=1).to_list()

    return '\n'.join(list_all_tasks)

def unchecked_tasks(update: Update):
    have_done_df= utility.reading_file('have_done.csv')
    tasks_df = utility.reading_file('tasks.csv')
    curr_date = datetime.datetime.now().astimezone(timezone('America/Denver')).date()

    tasks_to_send1 = tasks_df[tasks_df.start.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()<=curr_date)]
    done_tody = have_done_df[have_done_df.date.apply(lambda x:datetime.datetime.strptime(x, '%m/%d/%Y').date()==curr_date)].task_id.to_list()
    tasks_to_send2 = tasks_to_send1[tasks_to_send1.id.apply(lambda x: x not in done_tody)]
    
    list_unchecked_tasks = tasks_to_send2.apply(lambda r: str(r['id'])+'_'+r['name'] ,axis=1).to_list()

    return '\n'.join(list_unchecked_tasks)

def cat_selecting(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    print('%',text)
    if text == 'List of all Tasks':
        msg = all_tasks(Update)
        update.message.reply_text(msg)
        return SELECTING_COMMAND
    elif text == 'List of Unchecked':
        msg = unchecked_tasks(update)
        update.message.reply_text(msg)
        return SELECTING_COMMAND
    elif text == 'New Task':
        update.message.reply_text('What is the task title?')
        return NEW_TASK
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
            SELECTING_COMMAND: [MessageHandler(Filters.regex('^(List of all Tasks|List of Unchecked|New Task|Checking..)$'), cat_selecting)],
            CHECKING: [MessageHandler(Filters.text, checking)],
            NEW_TASK: [MessageHandler(Filters.text, adding_task)],
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

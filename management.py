# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 10:44:02 2021

@author: Parviz.Asoodehfard
"""

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
import business_layer as bl


def log(e,msg):
    print('Error:',msg,'\n',str(e))


SELECTING_COMMAND, CHECKING, NEW_TASK, POSTPONING = range(4)


def msg_validate(msg):
    msg = str(msg)
    if msg=='':
        msg = 'No Result'
    return msg

def start(update: Update, context: CallbackContext) -> int:
    print('start')
    reply_keyboard = [['List of all Tasks', 'List of Unchecked'],[ 'New Task', 'Checking..'],['Postponing..']]
    update.message.reply_text('Select your command',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return SELECTING_COMMAND

def change_status(val,text,update):
    user_id = update['message']['chat']['id']
    try:
        msg = bl.change_status(val,text,user_id)
    except Exception as e:
        log(e,'change_status()')
        msg = 'Sorry, right now we faced a difficulty.'
    msg = msg_validate(msg)
    update.message.reply_text(msg)
    

def checking(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    change_status('Done',text,update)
    return SELECTING_COMMAND

def postponing(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    change_status('Postponed',text,update)    
    return SELECTING_COMMAND

def adding_task(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    user_id = update['message']['chat']['id']
    try:
        msg = bl.adding_task(text,user_id)
    except Exception as e:
        log(e,'adding_task()')
        msg = 'Sorry, right now we faced a difficulty.'
    msg = msg_validate(msg)
    update.message.reply_text(msg)
    
    return SELECTING_COMMAND
    


def cancel(update: Update, context: CallbackContext) -> int:
    print('cancel')
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def cat_selecting(update: Update, context: CallbackContext) -> int:
    user_id = update['message']['chat']['id']
    text = update.message.text
    print('%',text)
    if text == 'List of all Tasks':
        try:
            msg = bl.all_tasks()
        except Exception as e:
            log(e,'all_tasks() in List of all Tasks')
            msg = 'Sorry, right now we faced a difficulty.'        
        msg = msg_validate(msg)
        update.message.reply_text(msg)
        return SELECTING_COMMAND
    elif text == 'List of Unchecked':
        print('management ..')
        try:
            msg = bl.unchecked_tasks_msg(user_id)
        except Exception as e:
            log(e,'unchecked_tasks_msg() in List of Unchecked')
            msg = 'Sorry, right now we faced a difficulty.'
        msg = msg_validate(msg)
        update.message.reply_text(msg)
        return SELECTING_COMMAND
    elif text == 'New Task':
        update.message.reply_text('What is the task title?')
        return NEW_TASK
    elif text == 'Checking..':
        update.message.reply_text('which tasks you have done?')
        return CHECKING
    elif text == 'Postponing..':
        update.message.reply_text('which tasks you have done?')
        return POSTPONING
    

def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(os.environ['tlg_token'], use_context=True)
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),MessageHandler(Filters.regex('^(List of all Tasks|List of Unchecked|New Task|Checking..|Postponing..)$'), cat_selecting)],
        states={
            SELECTING_COMMAND: [MessageHandler(Filters.regex('^(List of all Tasks|List of Unchecked|New Task|Checking..|Postponing..)$'), cat_selecting)],
            CHECKING: [MessageHandler(Filters.text, checking)],
            POSTPONING: [MessageHandler(Filters.text, postponing)],
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

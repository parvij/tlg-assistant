# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 10:44:02 2021

@author: Parviz.Asoodehfard
"""

import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler
)
import business_layer as bl
import numpy as np

def log(e,msg):
    print('Error:',msg,'\n',str(e))


SELECTING_COMMAND, NEW_TASK, NEW_GROUP_TASK = range(3)


def msg_validate(msg):
    msg = str(msg)
    if msg=='':
        msg = 'No Result'
    return msg

def start(update: Update, context: CallbackContext) -> int:
    print('start')
    reply_keyboard = [['Show Tasks'],[ 'New Task', 'New Group Task'],]
    update.message.reply_text('Select your command',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return SELECTING_COMMAND

def change_status(val,text,update):
    user_id = update['callback_query']['message']['chat']['id']
    try:
        msg = bl.change_status(val,text,user_id)
    except Exception as e:
        log(e,'change_status()')
        msg = 'Sorry, right now we faced a difficulty.'
    return msg
    

def adding_task(update: Update, context: CallbackContext,task_type='Personal') -> int:
    text = update.message.text
    if task_type=='Personal':
        user_id = update['message']['chat']['id']
    elif task_type=='Group':
        user_id = 'G_1'
    
    try:
        msg = bl.adding_task(text,user_id)
    except Exception as e:
        log(e,'adding_task()')
        msg = 'Sorry, right now we faced a difficulty.'
    msg = msg_validate(msg)
    update.message.reply_text(msg)
    
    return SELECTING_COMMAND

def adding_group_task(update: Update, context: CallbackContext) -> int:
    return adding_task(update, context,'Group')
    


def cancel(update: Update, context: CallbackContext) -> int:
    print('cancel')
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def my_reshape(the_list):
    from math import sqrt
    the_list = np.array(the_list)
    ln = len(the_list)
    width = int(sqrt(ln))
    width = width if width<=4 else 4
    group = lambda flat, size: [flat[i:i+size] for i in range(0,len(flat), size)]
    return group(the_list,width)


def showing_tasks(user_id,category = 'Current suggestion'):
    if category == 'Current suggestion':    # 'short':1,'Today':1,'current':1, done:0
        task_list = bl.get_tasks_list(user_id,'not_done & current & start_end & short')
    elif category == 'All current':         # 'short':0,'Today':1,'current':1, done:0
        task_list = bl.get_tasks_list(user_id,'not_done & current & start_end')
    elif category == 'All today':           # 'short':0,'Today':1,'current':0, done:0
        task_list = bl.get_tasks_list(user_id,'not_done & start_end')
    # elif category == 'Done today':          # 'short':0, 'today':1, 'current':0, done:1
    #     task_list = bl.get_tasks_list(user_id,'current & start_end')
    # elif category == 'All repeating':       # short:0, today:0, current:0, done:all, repeating
    #     task_list = bl.get_tasks_list(user_id,'not_done & current & start_end & short')
    # elif category == 'All once':            # short:0, today:0, current:0, done:all, once
    #     task_list = bl.get_tasks_list(user_id,'not_done & current & start_end & short')
    # elif category == 'All once not done':   # short:0, today:0, current:0, done:0, repeating
    #     task_list = bl.get_tasks_list(user_id,'not_done & current & start_end & short')
    else:
        print(category)
    buttoms = [InlineKeyboardButton(row['name'], callback_data='Task,'+row['name']+','+str(row['id'])) for idx,row in task_list.head(15).iterrows()]
    keyboard =  my_reshape(buttoms)
    keyboard += [[InlineKeyboardButton('Back', callback_data='Task_categories')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

def cat_selecting(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    print('%',text)
    if text == 'Show Tasks':
        try:
            user_id = update['message']['chat']['id']
            reply_markup = showing_tasks(user_id)
            update.message.reply_text('Please choose:', reply_markup=reply_markup)
        except Exception as e:
            log(e,'unchecked_tasks_msg() in List of Unchecked')
            msg = 'Sorry, right now we faced a difficulty.'
            update.message.reply_text(msg)
        return SELECTING_COMMAND
    elif text == 'New Task':
        update.message.reply_text('What is the task title?')
        return NEW_TASK
    elif text == 'New Group Task':
        update.message.reply_text('What is the task title?')
        return NEW_GROUP_TASK
    
def changing_task(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    val = query.data.split(',')
    if val[0] == 'Task':
        keyboard = [[InlineKeyboardButton('Done', callback_data=f'Action,Done,{val[2]},{val[1]}')],
                    [InlineKeyboardButton('Postponed', callback_data=f'Action,Postpone,{val[2]},{val[1]}'),
                     InlineKeyboardButton('_Undo', callback_data=f'_Action,Undo,{val[2]},{val[1]}')],
                    [InlineKeyboardButton('Cancel', callback_data=f'Cancel,0,0,{val[1]}'),
                     InlineKeyboardButton('Delete (Once occurance)', callback_data=f'Action,Delete,{val[2]},{val[1]}')],
                    ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=f"You have selected {val[1]}. What is its status?",reply_markup=reply_markup)
        
        
    elif val[0] == 'Action':
        msg = change_status(val[1],val[2],update)
        if msg == 'Done':
            query.edit_message_text(text=f'{val[3]} has been {val[1]}')
        else:
            print('Error',val[1],val[2])
            raise
            
            
    elif val[0] == 'Cancel':
        query.edit_message_text(text='Canceled')
        
    elif val[0] == 'Task_categories':
         keyboard = [[InlineKeyboardButton('Current suggestion', callback_data=f'Category,Current suggestion')],
                    [InlineKeyboardButton('All current', callback_data=f'Category,All current'),
                     InlineKeyboardButton('All today', callback_data=f'Category,All today'),
                     #InlineKeyboardButton('Done today', callback_data=f'Category,Done today')
                     ],
                    #[InlineKeyboardButton('All repeating', callback_data=f'Category,All repeating'),
                    # InlineKeyboardButton('All once', callback_data=f'Category,All once'),
                    # InlineKeyboardButton('All once not done', callback_data=f'Category,All once not done')],
                    ]
         reply_markup = InlineKeyboardMarkup(keyboard)
         query.edit_message_text(text="Which category of task you would like to see",reply_markup=reply_markup)

    elif val[0] == 'Category':
        user_id = update['callback_query']['message']['chat']['id']
        reply_markup = showing_tasks(user_id,val[1])
        query.edit_message_text(text="Please choose a task",reply_markup=reply_markup)
        
    else:
        print(val)
    
    #update.message.reply_text('Select your command',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),)





def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(os.environ['tlg_token'], use_context=True)
    updater.dispatcher.add_handler(CallbackQueryHandler(changing_task))
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),MessageHandler(Filters.regex('^(Show Tasks|New Task|New Group Task)$'), cat_selecting)],
        states={
            SELECTING_COMMAND: [MessageHandler(Filters.regex('^(Show Tasks|New Task|New Group Task)$'), cat_selecting)],
            NEW_TASK: [MessageHandler(Filters.text, adding_task)],
            NEW_GROUP_TASK: [MessageHandler(Filters.text, adding_group_task)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    j= updater.job_queue
    




    def talker(update):
        for user_id in bl.user_id_list():
            reply_markup = showing_tasks(user_id)
            updater.bot.sendMessage(chat_id=user_id, text='would you like to do a task?', reply_markup=reply_markup)    
        
        
    j.run_repeating(talker,interval = 60*60  ,first= 0)
    updater.start_polling()




    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    

if __name__ == '__main__':
    main()



#updater.bot.sendMessage(chat_id=91686406, text='Hello there!')
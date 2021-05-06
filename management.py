# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 10:44:02 2021

@author: Parviz.Asoodehfard
"""

import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
import business_layer as bl
import numpy as np
import telepot


SELECTING_COMMAND, NEW_TASK, CHANGING_TASK, CHANGING_TASK_TITLE, CHANGING_TASK_INFO = range(5)

########################## extra function ##########################################################

def log(e,msg):
    print('Error:',msg,'\n',str(e))

''' if empty send back 'no result'''
def msg_validate(msg):
    msg = str(msg)
    if msg=='':
        msg = 'No Result'
    return msg

''' a wrapper for change status of business_layer to prevent of failing and keep program running'''
def change_status(val,text,update):
    user_id = update['callback_query']['message']['chat']['id']
    try:
        msg = bl.change_status(val,text,user_id)
    except Exception as e:
        log(e,'change_status()')
        msg = 'Sorry, right now we faced a difficulty.'
    return msg

''' for creating keyboard (in show tasks)'''
def my_reshape(the_list):
    from math import sqrt
    the_list = np.array(the_list)
    ln = len(the_list)
    width = int(sqrt(ln))
    width = width if width<=4 else 4
    group = lambda flat, size: [flat[i:i+size] for i in range(0,len(flat), size)]
    return group(the_list,width)


def get_tasks_as_keyboards(user_id,category = 'Current suggestion'):
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
    
    print('33333333333333',task_list.iloc[0])
    buttoms = [InlineKeyboardButton(row['name'], callback_data='Task,'+row['name']+','+str(row['id'])) for idx,row in task_list.iterrows()]
    keyboard =  my_reshape(buttoms)
    keyboard += [[InlineKeyboardButton('Back', callback_data='Task_categories')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_additional_task_info_as_keyboards(task_id):
    task_info = bl.get_task_info(task_id)
    reply_markup = [[InlineKeyboardButton('Title: '+str(task_info['name']), callback_data='Add,Title,')],
                                 [InlineKeyboardButton('#Repeating: '+str(task_info['repeat']), callback_data='Add,Repeating'),
                                  InlineKeyboardButton('Who: '+str(task_info['branch_name']), callback_data='Add,Who,')],
                                 [ InlineKeyboardButton('#Start Date: '+str(task_info['start_date']), callback_data='Add,Start Date,'), 
                                   InlineKeyboardButton('#Duration: '+str(task_info['duration']), callback_data='Add,Duration,')],
                                 [InlineKeyboardButton('Add', callback_data='Add,Add,'),
                                  InlineKeyboardButton('Cancel', callback_data='Add,Cancel,')]]
    return reply_markup

def get_user_id(update):
    if update['callback_query']:
        user_id = update['callback_query']['message']['chat']['id']
        return user_id
    elif update['message']:
        user_id = update['message']['chat']['id']
        return user_id
    raise
    
    
def get_who_keyboard(user_id):
    df_groups = bl.get_groups(user_id)
    reply_markup = [[InlineKeyboardButton(row.branch_name, callback_data='Who,'+row.group_id)] for idx,row in df_groups.iterrows()]
    return reply_markup
########################## main commands ###########################################################
def start(update: Update, context: CallbackContext) -> int:
    print('start')
    reply_keyboard = [['Show Tasks', 'New Task'],['#Setting']]
    update.message.reply_text('Select your command',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    #print(type(update), update)
    return SELECTING_COMMAND
def cancel(update: Update, context: CallbackContext) -> int:
    print('cancel')
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

    
'''both group and personal'''
def adding_task(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    owner_id = str(update['message']['chat']['id'])
    group_id = 'P_' + owner_id
    try:
        task_id = bl.adding_task(text,group_id,owner_id)
        was_successful = True
        msg = 'it was ok'
    except Exception as e:
        log(e,'adding_task()')
        msg = 'Sorry, right now we faced a difficulty.'
    msg = msg_validate(msg)
    reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
    reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
    update.message.reply_text(msg, reply_markup=reply_markup)
    
    if was_successful and False:
        user_ids = [91686406,96166505]#bl.get_user_ids_in_group('G_1')
        user_id = update['message']['chat']['id']
        bot = telepot.Bot(os.environ['tlg_token']) 
        for uid in user_ids:
            if uid != user_id:
                bot.sendMessage(uid,'"'+text+'" has been added to the group tasks')
    
    return CHANGING_TASK

''' keyboard to call function '''
def cat_selecting(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    print('%',text)
    if text == 'Show Tasks':
        try:
            user_id = get_user_id(update)
            reply_markup = get_tasks_as_keyboards(user_id)
            update.message.reply_text('Please choose:', reply_markup=reply_markup)
        except Exception as e:
            print(reply_markup)
            log(e,'unchecked_tasks_msg() in List of Unchecked')
            msg = 'Sorry, right now we faced a difficulty.'
            update.message.reply_text(msg)
        return SELECTING_COMMAND
    elif text == 'New Task':
        update.message.reply_text('What is the task title?')
        return NEW_TASK
    
def InlineKeyboardHandler(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    val = query.data.split(',')
    if val[0] == 'Task':
        keyboard = [[InlineKeyboardButton('Done', callback_data=f'Action,Done,{val[2]},{val[1]}')],
                    [InlineKeyboardButton('Postponed', callback_data=f'Action,Postpone,{val[2]},{val[1]}'),
                     InlineKeyboardButton('#Undo', callback_data=f'_Action,Undo,{val[2]},{val[1]}')],
                    [InlineKeyboardButton('Cancel', callback_data=f'Cancel,0,0,{val[1]}'),
                     InlineKeyboardButton('#Delete', callback_data=f'Action,Delete,{val[2]},{val[1]}')],
                    ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=f"You have selected {val[1]}. What is its status?",reply_markup=reply_markup)
        
        
    elif val[0] == 'Action':
        msg = change_status(val[1],val[2],update)
        if msg == 'Done':
            user_id = update['callback_query']['message']['chat']['id']
            reply_markup = get_tasks_as_keyboards(user_id)
            query.edit_message_text(text=f'<b>{val[3]} has been {val[1]}.</b>\n\nDo you want to change status of any other task?', 
                                    reply_markup = reply_markup, 
                                    parse_mode= ParseMode.HTML)
            
        else:
            print('Error',val[1],val[2])
            raise
            
            
    elif val[0] == 'Cancel':
        query.edit_message_text(text='Canceled')
        
    elif val[0] == 'Task_categories':
         keyboard = [[InlineKeyboardButton('Current suggestion', callback_data=f'Category,Current suggestion')],
                    [InlineKeyboardButton('All current', callback_data=f'Category,All current'),
                     InlineKeyboardButton('All today', callback_data=f'Category,All today'),
                     ],
                    ]
         reply_markup = InlineKeyboardMarkup(keyboard)
         query.edit_message_text(text="Which category of task you would like to see",reply_markup=reply_markup)

    elif val[0] == 'Category':
        user_id = update['callback_query']['message']['chat']['id']
        reply_markup = get_tasks_as_keyboards(user_id,val[1])
        query.edit_message_text(text="Please choose a task",reply_markup=reply_markup)
        
    # elif val[0] == 'Add':
    #     if val[1] == 'Title':
    #         pass
    #     elif val[1] == 'Repeating':
    #         pass
    #     elif val[1] == 'Who':
    #         pass
    #     elif val[1] == 'Start Date':
    #         pass
    #     elif val[1] == 'Start Date':
    #         pass
    #     elif val[1] == 'Add':
    #         query.edit_message_text(text="The task has been Added")
    #     elif val[1] == 'Cancel':
    #         query.edit_message_text(text="Adding task has been Canceled")
            
        
    else:
        print(val)


def changing_task(update: Update, _: CallbackContext) -> None:
    user_id = get_user_id(update)
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    val = query.data.split(',')
    print(val)
    if val[0] == 'Add':
        if val[1] == 'Title':
            query.edit_message_text(text="What is the new title for the task?")
            return CHANGING_TASK_TITLE
        elif val[1] == 'Repeating':
            pass
        elif val[1] == 'Who':
            keyboard = get_who_keyboard(user_id)
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=f"Who is going to do this?",reply_markup=reply_markup)
            return CHANGING_TASK
        elif val[1] == 'Start Date':
            pass
        elif val[1] == 'Start Date':
            pass
        elif val[1] == 'Add':
            owner_id = str(get_user_id(update))
            update_dict = {'status':'active'}
            task_id = bl.updating_inactive_task(update_dict,owner_id)
            query.edit_message_text(text="The task has been Added")
            return SELECTING_COMMAND
        elif val[1] == 'Cancel':
            query.edit_message_text(text="Adding task has been Canceled")
            return SELECTING_COMMAND
    elif val[0] == 'Who':
        owner_id = str(get_user_id(update))
        update_dict = {'group_id':val[1]}
        task_id = bl.updating_inactive_task(update_dict,owner_id)
        
        reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
        reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
        query.edit_message_text(text=f"Is it ok now?",reply_markup=reply_markup)
        return CHANGING_TASK
    
def changing_title(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    owner_id = str(get_user_id(update))
    try:
        update_dict = {'name':text}
        task_id = bl.updating_inactive_task(update_dict,owner_id)
        msg = 'it was ok'
    except Exception as e:
        log(e,'adding_task()')
        msg = 'Sorry, right now we faced a difficulty.'
    msg = msg_validate(msg)
    reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
    reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
    update.message.reply_text(msg, reply_markup=reply_markup)
    
    
    return CHANGING_TASK
########################## main function ##################################################################
def main() -> None:
    updater = Updater(os.environ['tlg_token'], use_context=True)
    #updater.dispatcher.add_handler(CallbackQueryHandler(InlineKeyboardHandler))
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      CommandHandler('menu', start),
                      MessageHandler(Filters.regex('^(Show Tasks|New Task|New Group Task)$'), cat_selecting)],
        states={
            SELECTING_COMMAND: [MessageHandler(Filters.regex('^(Show Tasks|New Task)$'), cat_selecting),
                                CallbackQueryHandler(InlineKeyboardHandler)],
            NEW_TASK: [MessageHandler(Filters.text, adding_task)],
            CHANGING_TASK: [CallbackQueryHandler(changing_task)],
            CHANGING_TASK_TITLE: [MessageHandler(Filters.text, changing_title)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()







    j= updater.job_queue
    # I can't put it outside since I should pass this function to another function and that another function just give update to it
    def talker(update):
        for user_id in bl.user_id_list():
            reply_markup = get_tasks_as_keyboards(user_id)
            updater.bot.sendMessage(chat_id=user_id, text='would you like to do a task?', reply_markup=reply_markup)    
        
        
    j.run_repeating(talker,interval = 60*60  ,first= 0)
    updater.start_polling()




    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    

if __name__ == '__main__':
    main()
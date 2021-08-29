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
import logging
import datetime as dt
from utils import my_logger
from utils import my_logging


SELECTING_COMMAND, NEW_TASK, CHANGING_TASK, CHANGING_TASK_TITLE, CHANGING_TASK_INFO, CHANGING_TASK_REPEATING_INTERVAL, CHANGING_SETTING, CHANGING_LOCAL_TIME = range(8)

########################## extra function ##########################################################

    
def time_plus_now(user_id,x):
    t = bl.get_time(owner_id=user_id)
    delta = dt.timedelta(minutes = x)
    tm = (dt.datetime.combine(dt.date(1,1,1),t) + delta).time()
    return  str(tm.hour)+':'+str(tm.minute)
    
@my_logger
def msg_validate(msg):
    ''' 
    if empty send back 'no result
    '''
    
    msg = str(msg)
    if msg=='':
        msg = 'No Result'
        
    return msg

@my_logger
def change_status(val,text,update):
    ''' 
    a wrapper for change status of business_layer to prevent of failing and keep program running
    '''
    user_id = get_user_id(update)
    try:
        msg = bl.change_status(val,text,user_id)
    except Exception as e:
        my_logging('error',' __Interface__  change_status __> Error:'+str(e))
        msg = 'Sorry, right now we faced a difficulty.(46)'
    return msg

@my_logger
def my_reshape(the_list):
    ''' 
    for creating keyboard (in show tasks)
    '''
    from math import sqrt
    the_list = np.array(the_list)
    ln = len(the_list)
    width = int(sqrt(ln))
    width = width if width<=4 else 4
    group = lambda flat, size: [flat[i:i+size] for i in range(0,len(flat), size)]
    result = group(the_list,width)
    return result

#get_tasks_as_keyboards(user_id=91686406,category = 'Current suggestion')
@my_logger
def get_tasks_as_keyboards(user_id,category = 'Current suggestion'):
    if category == 'Current suggestion':    # 'short':1,'Today':1,'current':1, done:0
        task_list,has_new = bl.get_tasks_list(user_id,'not_done & current & start_end')
    elif category == 'All current':         # 'short':0,'Today':1,'current':1, done:0
        task_list,has_new = bl.get_tasks_list(user_id,'not_done & current & start_end')
    elif category == 'All today':           # 'short':0,'Today':1,'current':0, done:0
        task_list,has_new = bl.get_tasks_list(user_id,'not_done & start_end')
    else:
        my_logging('error','Category is out of expectation ')
    if len(task_list) > 0 :
        buttoms = [InlineKeyboardButton((str(round(row['time_cost']))+'.' if row['time_cost']==row['time_cost'] else '') +row['name'], callback_data='Task,'+row['name']+','+str(row['id'])) for idx,row in task_list.iterrows()]
        keyboard =  my_reshape(buttoms)
        keyboard += [[InlineKeyboardButton('Back - '+str(time_plus_now(user_id,task_list.time_cost.apply(lambda x: (x+5+min(x,60)/6) if x==x else 0).sum())), callback_data='Task_categories')]]
    else:
        keyboard = [[InlineKeyboardButton('There is not any task to do, you can add new tasks. Back', callback_data='Task_categories')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    current_time_user = bl.time_to_num(bl.get_time(user_id))
    time_of_last_task_which_has_done = bl.get_last_time_a_task_has_done(user_id)
    sleep_time = int(os.environ['sleep_time'])
    
    trigger = len(task_list)>0 and ( has_new or time_of_last_task_which_has_done + sleep_time < current_time_user)
    
    
    return reply_markup, trigger

@my_logger
def get_settings_as_keyboards(user_id):
    setting_dict = bl.get_settings_dict(user_id)
    setting_list = [InlineKeyboardButton(key+': '+str(setting_dict[key]), callback_data='Setting,'+str(setting_dict[key])) for key in setting_dict.keys()]
    keyboard = my_reshape(setting_list)
    keyboard += [[InlineKeyboardButton('Back', callback_data='Back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


@my_logger
def get_additional_task_info_as_keyboards(task_id):
    task_info = bl.get_task_info(task_id)
    
    
    final_keyboard = 'Add' if task_info['action'] == 'Add' else 'Done'
    reply_markup = [[InlineKeyboardButton('Title: '+str(task_info['name']), callback_data='Add,Title,')],
                                 [InlineKeyboardButton('Repeating: '+str(task_info['repeat']), callback_data='Add,Repeating'),
                                  InlineKeyboardButton('Who: '+str(task_info['branch_name']), callback_data='Add,Who,')],
                                 [ InlineKeyboardButton('#Start Date: '+str(task_info['start_date']), callback_data='Add,Start Date,'), 
                                   InlineKeyboardButton('Duration: '+str(task_info['duration']), callback_data='Add,Duration,')],
                                 [InlineKeyboardButton(final_keyboard, callback_data=task_info['action']+','+task_info['action']),
                                  InlineKeyboardButton('Cancel', callback_data='Add,Cancel,')]]
    
    return reply_markup

@my_logger
def get_user_id(update):
    if update['callback_query']:
        user_id = update['callback_query']['message']['chat']['id']
        my_logging('info',' __Interface__  get_user_id __> result:'+str(user_id))
        return str(user_id)
    elif update['message']:
        user_id = update['message']['chat']['id']
        my_logging('info',' __Interface__  get_user_id __> result:'+str(user_id))
        return str(user_id)
    
    my_logging('error',' __Interface__  get_user_id __> there is not any user_id in the update')
    raise
    


    
@my_logger
def get_duration_keyboard(user_id):
    df_durations = bl.get_durations(user_id)
    df_durations = df_durations [['title']].drop_duplicates()
    reply_markup = [[InlineKeyboardButton(row.title, callback_data='Duration,'+row.title)] for idx,row in df_durations.iterrows()]
    return reply_markup


@my_logger
def get_who_keyboard(user_id):
    df_groups = bl.get_groups(user_id)
    reply_markup = [[InlineKeyboardButton(row.branch_name, callback_data='Who,'+row.group_id)] for idx,row in df_groups.iterrows()]
    return reply_markup
########################## main commands ###########################################################
@my_logger
def start(update: Update, context: CallbackContext) -> int:
    my_logging('info',' __Interface__  start __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
    name_tlg = update['message']['chat']['username']+' / '+update['message']['chat']['first_name']
    owner_id = get_user_id(update)
    bl.add_user_if_not_exist(owner_id,name_tlg)
    menu(update, context)
    my_logging('info',' __Interface__  start __> result: SELECTING_COMMAND')
    return SELECTING_COMMAND

@my_logger
def menu(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Show Tasks', 'New Task'],['Setting']]
    update.message.reply_text('Select your command',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),)
    return SELECTING_COMMAND

@my_logger
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

    
'''both group and personal'''
@my_logger
def adding_task(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    owner_id = get_user_id(update)
    group_id = 'P_' + owner_id
    try:
        task_id = bl.adding_task(text,group_id,owner_id)
        was_successful = True
        msg = 'it was ok'
    except Exception as e:
        my_logging('error',str(e))
        msg = 'Sorry, right now we faced a difficulty.(179)'
    msg = msg_validate(msg)
    reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
    reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
    update.message.reply_text(msg, reply_markup=reply_markup)
    
    if was_successful and False:
        user_ids = [91686406,96166505]#bl.get_user_ids_in_group('G_1')
        user_id = get_user_id(update)
        bot = telepot.Bot(os.environ['tlg_token']) 
        for uid in user_ids:
            if uid != user_id:
                bot.sendMessage(uid,'"'+text+'" has been added to the group tasks')
    
    return CHANGING_TASK

''' keyboard to call function '''
@my_logger
def cat_selecting(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text == 'Show Tasks':
        try:
            user_id = get_user_id(update)
            reply_markup,_ = get_tasks_as_keyboards(user_id)
            update.message.reply_text('Please choose:', reply_markup=reply_markup)
        except Exception as e:
            my_logging('error',' __Interface__  cat_selecting __>' + str(e))
            msg = 'Sorry, right now we faced a difficulty.(207)'
            update.message.reply_text(msg)
        return SELECTING_COMMAND
    elif text == 'New Task':
        update.message.reply_text('What is the task title?')
        return NEW_TASK
    elif text == 'Setting':
        user_id = get_user_id(update)
        reply_markup = get_settings_as_keyboards(user_id)
        update.message.reply_text('Please choose:', reply_markup=reply_markup)
        return CHANGING_SETTING
            
    else:
        update.message.reply_text(text=f"I confuesed, please try again.")
        return SELECTING_COMMAND
    
    
@my_logger
def InlineKeyboardHandler(update: Update, _: CallbackContext) -> None:
    print('clicked'*50)
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
                     InlineKeyboardButton('#Delete', callback_data=f'Action,Delete,{val[2]},{val[1]}'),
                     InlineKeyboardButton('Edit', callback_data=f'Action,Edit,{val[2]},{val[1]}')],
                    ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=f"You have selected {val[1]}. What is its status?",reply_markup=reply_markup)
        my_logging('info',' __Interface__  InlineKeyboardHandler __> result:'+str(reply_markup))
        return
    elif val[0] == 'Action':
        if val[1] == 'Edit':
            owner_id = get_user_id(update)
            task_id = val[2]
            try:
                bl.editing_task(task_id,owner_id)
                msg = 'Please Edit it:'
            except Exception as e:
                my_logging('error',str(e))
                msg = 'Sorry, right now we faced a difficulty.(245)'
            msg = msg_validate(msg)
            reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
            reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
            query.edit_message_text(msg, reply_markup=reply_markup)            
            return CHANGING_TASK
        else:
            msg = change_status(val[1],val[2],update)
            if msg == 'Done':
                user_id = get_user_id(update)
                reply_markup,_ = get_tasks_as_keyboards(user_id)
                msg = f'{val[3]} has been {val[1]}.'
                if val[1] == 'Done':
                    msg = '<b>' + msg + '</b>'
                query.edit_message_text( text=msg,parse_mode= ParseMode.HTML)
                updater.bot.sendMessage(chat_id=user_id, text=#f'<b>{val[3]} has been {val[1]}.</b>
                                             'Do you want to change status of any other task?', 
                                        reply_markup = reply_markup, 
                                        parse_mode= ParseMode.HTML)
            
                my_logging('info',' __Interface__  InlineKeyboardHandler __> result:'+str(reply_markup))
                return
            else:
                my_logging('error',' __Interface__  InlineKeyboardHandler __> this values are not expected:'+str(val))
                raise
            
            
    elif val[0] == 'Cancel':
        query.edit_message_text(text='Canceled')
        my_logging('info',' __Interface__  InlineKeyboardHandler __> result:Canceled')
        
    elif val[0] == 'Task_categories':
         keyboard = [[InlineKeyboardButton('Current suggestion', callback_data=f'Category,Current suggestion')],
                    [InlineKeyboardButton('All current', callback_data=f'Category,All current'),
                     InlineKeyboardButton('All today', callback_data=f'Category,All today'),
                     ],
                    ]
         reply_markup = InlineKeyboardMarkup(keyboard)
         query.edit_message_text(text="Which category of task you would like to see",reply_markup=reply_markup)
         my_logging('info',' __Interface__  InlineKeyboardHandler __> result:'+str(reply_markup))
         return

    elif val[0] == 'Category':
        user_id = update['callback_query']['message']['chat']['id']
        reply_markup,_ = get_tasks_as_keyboards(user_id,val[1])
        query.edit_message_text(text="Please choose a task",reply_markup=reply_markup)
        my_logging('info',' __Interface__  InlineKeyboardHandler __> result:'+str(reply_markup))
        return
            
        
    else:
        query.edit_message_text(text=f"I confuesed, please try again.")
        return SELECTING_COMMAND
    
    
@my_logger
def changing_setting(update: Update, _: CallbackContext) -> None:
    #owner_id = str(get_user_id(update))
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    val = query.data.split(',')
    my_logging('info',' __Interface__  changing_setting __>>> val: '+str(val))
    if val[0] == 'Back':
        query.edit_message_text(text="Done.")
        return SELECTING_COMMAND
    elif val[0] == 'Setting':
        query.edit_message_text(text="What is the new local time difference?")
        return CHANGING_LOCAL_TIME
    else:
        query.edit_message_text(text=f"I confuesed, please try again.")
        return SELECTING_COMMAND
    


@my_logger
def changing_task(update: Update, _: CallbackContext) -> None:
    owner_id = str(get_user_id(update))
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    val = query.data.split(',')
    my_logging('info',' __Interface__  changing_task __>>> val: '+str(val))
    if val[0] == 'Add':
        if val[1] == 'Title':
            query.edit_message_text(text="What is the new title for the task?")
            return CHANGING_TASK_TITLE
        elif val[1] == 'Repeating':
            keyboard = [[InlineKeyboardButton('Once', callback_data=f'Repeating,Once'),
                         InlineKeyboardButton('Daily', callback_data=f'Repeating,Daily'),],]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=f"How is it repeating?",reply_markup=reply_markup)
            return CHANGING_TASK
        elif val[1] == 'Duration':
            keyboard = get_duration_keyboard(owner_id)
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=f"what is the duration?",reply_markup=reply_markup)
            return CHANGING_TASK
        elif val[1] == 'Who':
            keyboard = get_who_keyboard(owner_id)
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=f"Who is going to do this?",reply_markup=reply_markup)
            return CHANGING_TASK
        elif val[1] == 'Start Date':
            pass
        elif val[1] == 'End Date':
            pass
        elif val[1] == 'Add':
            update_dict = {'status':'active'}
            task_id = bl.updating_inactive_task(update_dict,owner_id)
            query.edit_message_text(text="The task has been Added")
            return SELECTING_COMMAND
        elif val[1] == 'Cancel':
            query.edit_message_text(text="Adding task has been Canceled")
            return SELECTING_COMMAND
    elif val[0] == 'Who':
        update_dict = {'group_id':val[1]}
        task_id = bl.updating_inactive_task(update_dict,owner_id)
        
        reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
        reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
        query.edit_message_text(text=f"Is it ok now?",reply_markup=reply_markup)
        return CHANGING_TASK
    elif val[0] == 'Repeating':
        if val[1] == 'Once':
            update_dict = {'repeat':'Once'}
            task_id = bl.updating_inactive_task(update_dict,owner_id)
            
            reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
            reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
            query.edit_message_text(text=f"Is it ok now?",reply_markup=reply_markup)
            return CHANGING_TASK
        if val[1] == 'Daily':
            query.edit_message_text(text="Every how many day you want to do this task?")
            return CHANGING_TASK_REPEATING_INTERVAL
    elif val[0] == 'Duration':
        update_dict = {'duration':val[1]}
        task_id = bl.updating_inactive_task(update_dict,owner_id)
        
        reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
        reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
        query.edit_message_text(text=f"Is it ok now?",reply_markup=reply_markup)
        return CHANGING_TASK
    elif val[0] == 'Edit':
        
        update_dict = {'status':'active'}
        task_id = bl.updating_inactive_task(update_dict,owner_id)
        query.edit_message_text(text="The task has been Added")        
        return SELECTING_COMMAND
    
    else:
        query.edit_message_text(text=f"I confuesed, please try again.")
        return SELECTING_COMMAND
    

@my_logger
def changing_repeating_interval(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    owner_id = str(get_user_id(update))
    if text.isnumeric():
        try:
            if int(text) >0:
                update_dict = {'repeat':'Daily-'+str(text)}
            else:
                update_dict = {'repeat':'Once'}
            task_id = bl.updating_inactive_task(update_dict,owner_id)
            msg = 'it was ok'
        except Exception as e:
            my_logging('error',str(e))
            msg = 'Sorry, right now we faced a difficulty.(396)'
        msg = msg_validate(msg)
        reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
        reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
        update.message.reply_text(msg, reply_markup=reply_markup)
        
        return CHANGING_TASK
    else:
        update.message.reply_text('I expect a number, please give me a number or 0 for "without repeating"')
        my_logging('info',' __Interface__  changing_repeating_interval __> result: Noting. Stay at this status')
        
    
@my_logger
def changing_local_time  (update: Update, context: CallbackContext) -> int:
    text = update.message.text
    owner_id = str(get_user_id(update))
    try:
        if text.isnumeric():
            update_dict = {'local_time_diff':text}
            _ = bl.updating_setting(update_dict,owner_id)
            msg = 'ok, it changed'
        else:
            msg = 'it was not a number'
    except Exception as e:
        my_logging('error',str(e))
        msg = 'Sorry, right now we faced a difficulty.(419)'
    msg = msg_validate(msg)

    reply_markup = get_settings_as_keyboards(owner_id)
    update.message.reply_text(msg, reply_markup=reply_markup)

    return CHANGING_SETTING
    
@my_logger
def changing_title(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    owner_id = str(get_user_id(update))
    try:
        update_dict = {'name':text}
        task_id = bl.updating_inactive_task(update_dict,owner_id)
        msg = 'it was ok'
    except Exception as e:
        my_logging('error',str(e))
        msg = 'Sorry, right now we faced a difficulty.(419)'
    msg = msg_validate(msg)
    reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
    reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
    update.message.reply_text(msg, reply_markup=reply_markup)
    
    return CHANGING_TASK








########################## main function ##################################################################
# def main() -> None:
logging.basicConfig(format='%(asctime)s  %(levelname)s:  %(message)s',
                    handlers=[logging.FileHandler('logfile.log', 'w', 'utf-8')],
                    level=logging.INFO)
my_logging('info',' __Interface__  main __>\n\n\n')

updater = Updater(os.environ['tlg_token'], use_context=True)
#updater.dispatcher.add_handler(CallbackQueryHandler(InlineKeyboardHandler))
# Get the dispatcher to register handlers
dispatcher = updater.dispatcher

# Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start),
                  CommandHandler('menu', menu),
                  MessageHandler(Filters.regex('^(Show Tasks|New Task|Setting)$'), cat_selecting)],
    states={
        SELECTING_COMMAND: [MessageHandler(Filters.regex('^(Show Tasks|New Task|Setting)$'), cat_selecting),
                            CallbackQueryHandler(InlineKeyboardHandler),
                            CommandHandler('menu', menu)],
        NEW_TASK: [MessageHandler(Filters.text, adding_task),
                   CommandHandler('menu', menu)],
        CHANGING_TASK: [CallbackQueryHandler(changing_task),
                        CommandHandler('menu', menu)],
        CHANGING_TASK_TITLE: [MessageHandler(Filters.text, changing_title),
                              CommandHandler('menu', menu)],
        CHANGING_TASK_REPEATING_INTERVAL: [MessageHandler(Filters.text, changing_repeating_interval),
                                           CommandHandler('menu', menu)],
        CHANGING_SETTING : [CallbackQueryHandler(changing_setting),
                            CommandHandler('menu', menu)],
        CHANGING_LOCAL_TIME: [MessageHandler(Filters.text, changing_local_time),
                              CommandHandler('menu', menu)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

dispatcher.add_handler(conv_handler)

# Start the Bot
#updater.start_polling()







j= updater.job_queue
# I can't put it outside since I should pass this function to another function and that another function just give update to it
@my_logger
def talker(update):    
    for user_id in bl.user_id_list():
        reply_markup, trigger = get_tasks_as_keyboards(user_id)
        if  trigger:
            update.bot.sendMessage(chat_id=user_id, text='would you like to do a task?', reply_markup=reply_markup)
    
    
j.run_repeating(talker,interval = int(os.environ['sleep_time'])  ,first= 0)
updater.start_polling()




# Run the bot until you press Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.
updater.idle()


# if __name__ == '__main__':
#     main()
    
    
    
    
    
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


SELECTING_COMMAND, NEW_TASK, CHANGING_TASK, CHANGING_TASK_TITLE, CHANGING_TASK_INFO, CHANGING_TASK_REPEATING_INTERVAL, CHANGING_SETTING, CHANGING_LOCAL_TIME = range(8)

########################## extra function ##########################################################

    
    
    
    
''' if empty send back 'no result'''
def msg_validate(msg):
    logging.info(' __Interface__  msg_validate __> msg:'+str(msg))
    
    msg = str(msg)
    if msg=='':
        msg = 'No Result'
        
    logging.info(' __Interface__  msg_validate __> result:'+str(msg))
    return msg

''' a wrapper for change status of business_layer to prevent of failing and keep program running'''
def change_status(val,text,update):
    logging.info(' __Interface__  change_status __> val:'+str(val)+'| text:'+str(text)+'| update:'+str(update))

    user_id = get_user_id(update)
    try:
        msg = bl.change_status(val,text,user_id)
    except Exception as e:
        logging.error(' __Interface__  change_status __> Error:'+str(e))
        msg = 'Sorry, right now we faced a difficulty.(46)'

    logging.info(' __Interface__  change_status __> result:'+str(msg))
    return msg

''' for creating keyboard (in show tasks)'''
def my_reshape(the_list):
    logging.info(' __Interface__  my_reshape __> the_list:'+str(the_list))
    from math import sqrt
    the_list = np.array(the_list)
    ln = len(the_list)
    width = int(sqrt(ln))
    width = width if width<=4 else 4
    group = lambda flat, size: [flat[i:i+size] for i in range(0,len(flat), size)]
    result = group(the_list,width)
    logging.info(' __Interface__  my_reshape __> result:'+str(result))
    return result

#get_tasks_as_keyboards(user_id=91686406,category = 'Current suggestion')
def get_tasks_as_keyboards(user_id,category = 'Current suggestion'):
    logging.info(' __Interface__  get_tasks_as_keyboards __> user_id:'+str(user_id)+'| category:'+str(category))
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
        logging.error('Category is out of expectation ')
    if len(task_list) > 0 :
        buttoms = [InlineKeyboardButton(row['name'], callback_data='Task,'+row['name']+','+str(row['id'])) for idx,row in task_list.iterrows()]
        keyboard =  my_reshape(buttoms)
        keyboard += [[InlineKeyboardButton('Back', callback_data='Task_categories')]]
    else:
        keyboard = [[InlineKeyboardButton('There is not any task to do, you can add new tasks. Back', callback_data='Task_categories')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    
    logging.info(' __Interface__  get_tasks_as_keyboards __> result:'+str(reply_markup))    
    return reply_markup

def get_settings_as_keyboards(user_id):
    logging.info(' __Interface__  get_settings_as_keyboards __> user_id:'+str(user_id))
    setting_dict = bl.get_settings_dict(user_id)
    setting_list = [InlineKeyboardButton(key+': '+str(setting_dict[key]), callback_data='Setting,'+str(setting_dict[key])) for key in setting_dict.keys()]
    keyboard = my_reshape(setting_list)
    keyboard += [[InlineKeyboardButton('Back', callback_data='Back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    logging.info(' __Interface__  get_settings_as_keyboards __> result:'+str(reply_markup))    
    return reply_markup


def get_additional_task_info_as_keyboards(task_id):
    logging.info(' __Interface__  get_additional_task_info_as_keyboards __> task_id:'+str(task_id))
    task_info = bl.get_task_info(task_id)
    
    
    final_keyboard = 'Add' if task_info['action'] == 'Add' else 'Done'
    reply_markup = [[InlineKeyboardButton('Title: '+str(task_info['name']), callback_data='Add,Title,')],
                                 [InlineKeyboardButton('Repeating: '+str(task_info['repeat']), callback_data='Add,Repeating'),
                                  InlineKeyboardButton('Who: '+str(task_info['branch_name']), callback_data='Add,Who,')],
                                 [ InlineKeyboardButton('#Start Date: '+str(task_info['start_date']), callback_data='Add,Start Date,'), 
                                   InlineKeyboardButton('Duration: '+str(task_info['duration']), callback_data='Add,Duration,')],
                                 [InlineKeyboardButton(final_keyboard, callback_data=task_info['action']+','+task_info['action']),
                                  InlineKeyboardButton('Cancel', callback_data='Add,Cancel,')]]
    
    logging.info(' __Interface__  get_additional_task_info_as_keyboards __> result:'+str(reply_markup))    
    return reply_markup

def get_user_id(update):
    logging.info(' __Interface__  get_user_id __> update:'+str(update))
    if update['callback_query']:
        user_id = update['callback_query']['message']['chat']['id']
        logging.info(' __Interface__  get_user_id __> result:'+str(user_id))
        return str(user_id)
    elif update['message']:
        user_id = update['message']['chat']['id']
        logging.info(' __Interface__  get_user_id __> result:'+str(user_id))
        return str(user_id)
    
    print('ffffffffffffffffffffuck')
    raise
    


    
def get_duration_keyboard(user_id):
    logging.info(' __Interface__  get_duration_keyboard __> user_id:'+str(user_id))
    df_durations = bl.get_durations(user_id)
    df_durations = df_durations [['title']].drop_duplicates()
    reply_markup = [[InlineKeyboardButton(row.title, callback_data='Duration,'+row.title)] for idx,row in df_durations.iterrows()]
    logging.info(' __Interface__  get_duration_keyboard __> result:'+str(reply_markup))
    return reply_markup


def get_who_keyboard(user_id):
    logging.info(' __Interface__  get_who_keyboard __> user_id:'+str(user_id))
    df_groups = bl.get_groups(user_id)
    reply_markup = [[InlineKeyboardButton(row.branch_name, callback_data='Who,'+row.group_id)] for idx,row in df_groups.iterrows()]
    logging.info(' __Interface__  get_who_keyboard __> result:'+str(reply_markup))
    return reply_markup
########################## main commands ###########################################################
def start(update: Update, context: CallbackContext) -> int:
    print('started')
    logging.info(' __Interface__  start __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
    name_tlg = update['message']['chat']['username']+' / '+update['message']['chat']['first_name']
    owner_id = get_user_id(update)
    bl.add_user_if_not_exist(owner_id,name_tlg)
    
    reply_keyboard = [['Show Tasks', 'New Task'],['Setting']]
    update.message.reply_text('Select your command',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    #print(type(update), update)
    logging.info(' __Interface__  start __> result: SELECTING_COMMAND')
    return SELECTING_COMMAND
def cancel(update: Update, context: CallbackContext) -> int:
    logging.info(' __Interface__  cancel __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    logging.info(' __Interface__  cancel __> result: ConversationHandler.END')
    return ConversationHandler.END

    
'''both group and personal'''
def adding_task(update: Update, context: CallbackContext) -> int:
    logging.info(' __Interface__  adding_task __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
    text = update.message.text
    owner_id = get_user_id(update)
    group_id = 'P_' + owner_id
    try:
        task_id = bl.adding_task(text,group_id,owner_id)
        was_successful = True
        msg = 'it was ok'
    except Exception as e:
        #log(e,'adding_task()')
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
    
    logging.info(' __Interface__  adding_task __> result: CHANGING_TASK')    
    return CHANGING_TASK

''' keyboard to call function '''
def cat_selecting(update: Update, context: CallbackContext) -> int:
    logging.info(' __Interface__  cat_selecting __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
    text = update.message.text
    if text == 'Show Tasks':
        try:
            user_id = get_user_id(update)
            reply_markup = get_tasks_as_keyboards(user_id)
            update.message.reply_text('Please choose:', reply_markup=reply_markup)
        except Exception as e:
            #log(e,'unchecked_tasks_msg() in List of Unchecked')
            msg = 'Sorry, right now we faced a difficulty.(207)'
            update.message.reply_text(msg)
        logging.info(' __Interface__  cat_selecting __> result: SELECTING_COMMAND')
        return SELECTING_COMMAND
    elif text == 'New Task':
        update.message.reply_text('What is the task title?')
        logging.info(' __Interface__  cat_selecting __> result: NEW_TASK')
        return NEW_TASK
    elif text == 'Setting':
        user_id = get_user_id(update)
        reply_markup = get_settings_as_keyboards(user_id)
        update.message.reply_text('Please choose:', reply_markup=reply_markup)
        return CHANGING_SETTING
    
def InlineKeyboardHandler(update: Update, _: CallbackContext) -> None:
    logging.info(' __Interface__  InlineKeyboardHandler __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
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
        logging.info(' __Interface__  InlineKeyboardHandler __> result:'+str(reply_markup))
        return
    elif val[0] == 'Action':
        if val[1] == 'Edit':
            owner_id = get_user_id(update)
            task_id = val[2]
            try:
                bl.editing_task(task_id,owner_id)
                msg = 'Please Edit it:'
            except Exception as e:
                #log(e,'adding_task()')
                msg = 'Sorry, right now we faced a difficulty.(245)'
            msg = msg_validate(msg)
            reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
            reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
            query.edit_message_text(msg, reply_markup=reply_markup)            
            logging.info(' __Interface__  InlineKeyboardHandler __> result: CHANGING_TASK')
            return CHANGING_TASK
        else:
            msg = change_status(val[1],val[2],update)
            if msg == 'Done':
                user_id = get_user_id(update)
                reply_markup = get_tasks_as_keyboards(user_id)
                query.edit_message_text(text=f'<b>{val[3]} has been {val[1]}.</b>\n\nDo you want to change status of any other task?', 
                                        reply_markup = reply_markup, 
                                        parse_mode= ParseMode.HTML)
            
                logging.info(' __Interface__  InlineKeyboardHandler __> result:'+str(reply_markup))
                return
            else:
                print('Error',val[1],val[2])
                raise
            
            
    elif val[0] == 'Cancel':
        query.edit_message_text(text='Canceled')
        logging.info(' __Interface__  InlineKeyboardHandler __> result:Canceled')
        
    elif val[0] == 'Task_categories':
         keyboard = [[InlineKeyboardButton('Current suggestion', callback_data=f'Category,Current suggestion')],
                    [InlineKeyboardButton('All current', callback_data=f'Category,All current'),
                     InlineKeyboardButton('All today', callback_data=f'Category,All today'),
                     ],
                    ]
         reply_markup = InlineKeyboardMarkup(keyboard)
         query.edit_message_text(text="Which category of task you would like to see",reply_markup=reply_markup)
         logging.info(' __Interface__  InlineKeyboardHandler __> result:'+str(reply_markup))
         return

    elif val[0] == 'Category':
        user_id = update['callback_query']['message']['chat']['id']
        reply_markup = get_tasks_as_keyboards(user_id,val[1])
        query.edit_message_text(text="Please choose a task",reply_markup=reply_markup)
        logging.info(' __Interface__  InlineKeyboardHandler __> result:'+str(reply_markup))
        return
            
        
    else:
        logging.error(' __Interface__  InlineKeyboardHandler __> val:'+str(val))
    
    
def changing_setting(update: Update, _: CallbackContext) -> None:
    logging.info(' __Interface__  changing_setting __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
    owner_id = str(get_user_id(update))
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    val = query.data.split(',')
    logging.info(' __Interface__  changing_setting __>>> val: '+str(val))
    if val[0] == 'Back':
        query.edit_message_text(text="Done.")
        logging.info(' __Interface__  changing_setting __> result: SELECTING_COMMAND')
        return SELECTING_COMMAND
    elif val[0] == 'Setting':
        query.edit_message_text(text="What is the new local time difference?")
        return CHANGING_LOCAL_TIME


def changing_task(update: Update, _: CallbackContext) -> None:
    logging.info(' __Interface__  changing_task __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
    owner_id = str(get_user_id(update))
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    val = query.data.split(',')
    logging.info(' __Interface__  changing_task __>>> val: '+str(val))
    if val[0] == 'Add':
        if val[1] == 'Title':
            query.edit_message_text(text="What is the new title for the task?")
            return CHANGING_TASK_TITLE
        elif val[1] == 'Repeating':
            keyboard = [[InlineKeyboardButton('Once', callback_data=f'Repeating,Once'),
                         InlineKeyboardButton('Daily', callback_data=f'Repeating,Daily'),],]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=f"How is it repeating?",reply_markup=reply_markup)
            logging.info(' __Interface__  changing_task __> result: CHANGING_TASK')
            return CHANGING_TASK
        elif val[1] == 'Duration':
            keyboard = get_duration_keyboard(owner_id)
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=f"what is the duration?",reply_markup=reply_markup)
            logging.info(' __Interface__  changing_task __> result: CHANGING_TASK')
            return CHANGING_TASK
        elif val[1] == 'Who':
            keyboard = get_who_keyboard(owner_id)
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=f"Who is going to do this?",reply_markup=reply_markup)
            logging.info(' __Interface__  changing_task __> result: CHANGING_TASK')
            return CHANGING_TASK
        elif val[1] == 'Start Date':
            pass
        elif val[1] == 'End Date':
            pass
        elif val[1] == 'Add':
            update_dict = {'status':'active'}
            task_id = bl.updating_inactive_task(update_dict,owner_id)
            query.edit_message_text(text="The task has been Added")
            logging.info(' __Interface__  changing_task __> result: SELECTING_COMMAND')
            return SELECTING_COMMAND
        elif val[1] == 'Cancel':
            query.edit_message_text(text="Adding task has been Canceled")
            logging.info(' __Interface__  changing_task __> result: SELECTING_COMMAND')
            return SELECTING_COMMAND
    elif val[0] == 'Who':
        update_dict = {'group_id':val[1]}
        task_id = bl.updating_inactive_task(update_dict,owner_id)
        
        reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
        reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
        query.edit_message_text(text=f"Is it ok now?",reply_markup=reply_markup)
        logging.info(' __Interface__  changing_task __> result: CHANGING_TASK')
        return CHANGING_TASK
    elif val[0] == 'Repeating':
        if val[1] == 'Once':
            update_dict = {'repeat':'Once'}
            task_id = bl.updating_inactive_task(update_dict,owner_id)
            
            reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
            reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
            query.edit_message_text(text=f"Is it ok now?",reply_markup=reply_markup)
            logging.info(' __Interface__  changing_task __> result: CHANGING_TASK')
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
        logging.info(' __Interface__  changing_task __> result: CHANGING_TASK')
        return CHANGING_TASK
    elif val[0] == 'Edit':
        
        update_dict = {'status':'active'}
        task_id = bl.updating_inactive_task(update_dict,owner_id)
        query.edit_message_text(text="The task has been Added")        
        logging.info(' __Interface__  changing_task __> result: SELECTING_COMMAND')
        return SELECTING_COMMAND

def changing_repeating_interval(update: Update, context: CallbackContext) -> int:
    logging.info(' __Interface__  changing_repeating_interval __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
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
            #log(e,'adding_task()')
            msg = 'Sorry, right now we faced a difficulty.(396)'
        msg = msg_validate(msg)
        reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
        reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
        update.message.reply_text(msg, reply_markup=reply_markup)
        
        logging.info(' __Interface__  changing_repeating_interval __> result: CHANGING_TASK')
        return CHANGING_TASK
    else:
        update.message.reply_text('I expect a number, please give me a number or 0 for "without repeating"')
        logging.info(' __Interface__  changing_repeating_interval __> result: Noting. Stay at this status')
        
    
def changing_local_time  (update: Update, context: CallbackContext) -> int:
    logging.info(' __Interface__  changing_local_time __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
    text = update.message.text
    owner_id = str(get_user_id(update))
    try:
        if text.isnumeric():
            update_dict = {'local_time_diff':text}
            task_id = bl.updating_setting(update_dict,owner_id)
            msg = 'ok, it changed'
        else:
            msg = 'it was not a number'
    except Exception as e:
        #log(e,'adding_task()')
        msg = 'Sorry, right now we faced a difficulty.(419)'
    msg = msg_validate(msg)

    reply_markup = get_settings_as_keyboards(owner_id)
    update.message.reply_text(msg, reply_markup=reply_markup)

    logging.info(' __Interface__  changing_local_time __> result: CHANGING_TASK')
    return CHANGING_SETTING
    
def changing_title(update: Update, context: CallbackContext) -> int:
    logging.info(' __Interface__  changing_title __> update:'+str(update)+'| CallbackContext:'+str(CallbackContext))
    text = update.message.text
    owner_id = str(get_user_id(update))
    try:
        update_dict = {'name':text}
        task_id = bl.updating_inactive_task(update_dict,owner_id)
        msg = 'it was ok'
    except Exception as e:
        #log(e,'adding_task()')
        msg = 'Sorry, right now we faced a difficulty.(419)'
    msg = msg_validate(msg)
    reply_keyboard_additional = get_additional_task_info_as_keyboards(task_id)    
    reply_markup = InlineKeyboardMarkup(reply_keyboard_additional)
    update.message.reply_text(msg, reply_markup=reply_markup)
    
    logging.info(' __Interface__  changing_title __> result: CHANGING_TASK')
    return CHANGING_TASK
########################## main function ##################################################################
def main() -> None:
    logging.basicConfig(format='%(asctime)s  %(levelname)s:  %(message)s',
                        handlers=[logging.FileHandler('logfile.log', 'w', 'utf-8')],
                        level=logging.INFO)
    logging.info(' __Interface__  main __>\n\n\n')
    
    updater = Updater(os.environ['tlg_token'], use_context=True)
    #updater.dispatcher.add_handler(CallbackQueryHandler(InlineKeyboardHandler))
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      CommandHandler('menu', start),
                      MessageHandler(Filters.regex('^(Show Tasks|New Task|Setting)$'), cat_selecting)],
        states={
            SELECTING_COMMAND: [MessageHandler(Filters.regex('^(Show Tasks|New Task|Setting)$'), cat_selecting),
                                CallbackQueryHandler(InlineKeyboardHandler)],
            NEW_TASK: [MessageHandler(Filters.text, adding_task)],
            CHANGING_TASK: [CallbackQueryHandler(changing_task)],
            CHANGING_TASK_TITLE: [MessageHandler(Filters.text, changing_title)],
            CHANGING_TASK_REPEATING_INTERVAL: [MessageHandler(Filters.text, changing_repeating_interval)],
            CHANGING_SETTING : [CallbackQueryHandler(changing_setting)],
            CHANGING_LOCAL_TIME: [MessageHandler(Filters.text, changing_local_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()







    j= updater.job_queue
    # I can't put it outside since I should pass this function to another function and that another function just give update to it
    def talker(update):
        logging.info(' __Interface__  talker __> update:'+str(update))
        for user_id in bl.user_id_list():
            reply_markup = get_tasks_as_keyboards(user_id)
            updater.bot.sendMessage(chat_id=user_id, text='would you like to do a task?', reply_markup=reply_markup)    
        
        
    j.run_repeating(talker,interval = 60*60*2  ,first= 0)
    updater.start_polling()




    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    

if __name__ == '__main__':
    main()
    
    
    
    
    
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

CAT_SELECTING = range(1)

def start(update: Update, context: CallbackContext) -> int:
    print('start')
    #reply_keyboard = [['Boy', 'Girl', 'Other']]
    #reply_keyboard = [["Bakery, Cake and Cookies","Auto Repair","Banking Services"],                      ["Barber Shop","Business Consultation","Car Dealership"],                      ["Certified Translator","Childcare Services","Cleaning Services"],                      ["Construction / Home Renovation Services","Counseling Services","Currency Exchange"],                      ["Dentist","Digital Marketing & Advertisement","Driving School"],                      ["Electronics / Laptop & Mobile Rapair","Food Catering","Graphic Design"],                      ["Hand-Made Jewelry","Heating, Cooling, Ventilation and Air Conditioner Services","Home Maintenance / Repair Services"],                      ["Immigration Services","Insurance & Financial Services","Interior Design and Home Staging"],                      ["Iranian Food Market","Lawyer / Paralegal","Local Farsi Radio Station"],                      ["Makeup, Hair Style and Beauty","Massage Therapy","Moving & Delivery Services"],                      ["Music Lessons","Newcomers Services","Optometrist / Optician"],                      ["Photography Services","Physician","Physiotherapy & Chiropractic"],                      ["Printing Services","Psychotherapist","Publication"],                      ["Real Estate","Restaurants","TAX & Accounting Services"],                      ["Travel Agency","Tutor / Instructor & Trainer","Website Development Services"]]
    
    
    # make a matrix with col_n columns from categories

    update.message.reply_text('کدوم تسک رو انجام دادی؟'
        #reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return CAT_SELECTING

def write_file(df):
    print('write file')
    bucket = 'parvij-assistance'  # already created on S3
    csv_buffer = StringIO()
    df.to_csv(csv_buffer,index=False)
    s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
    s3_resource.Object(bucket, 'have_done.csv').put(Body=csv_buffer.getvalue())

def read_file():
    print('read file')
    s3_resource = boto3.resource('s3',aws_access_key_id=os.environ['aws_access_key_id'],aws_secret_access_key=os.environ['aws_secret_access_key'])
    s3_object = s3_resource.Object(bucket_name='parvij-assistance', key='have_done.csv')
    s3_data = StringIO(s3_object.get()['Body'].read().decode('utf-8'))
    df = pd.read_csv(s3_data)
    return df

def cat_selecting(update: Update, context: CallbackContext) -> int:
    print('cat selecting')
    text = update.message.text
    if text.isnumeric():
        df = read_file()
        curr_date = datetime.datetime.now().astimezone(timezone('America/Denver')).date()
        df = df.append({'task_id': text,'date':curr_date.strftime('%m/%d/%Y')}, ignore_index=True)
        write_file(df)
    update.message.reply_text('Done')
    
    return CAT_SELECTING
    


def cancel(update: Update, context: CallbackContext) -> int:
    print('cancel')
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


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
            CAT_SELECTING: [MessageHandler(Filters.text, cat_selecting)],
#            GENDER: [MessageHandler(Filters.regex('^(Boy|Girl|Other)$'), gender)],
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

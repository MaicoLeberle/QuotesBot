import logging
import sys
from random import randint
import pandas
import datetime

from telegram import Update, ForceReply, ParseMode
from telegram.ext import \
        Updater, CommandHandler, MessageHandler, Filters, CallbackContext



# Enable logging, mostly for debugging
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)



""" Send our greetings to the user. """
def start_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(fr'Hi {user.mention_markdown_v2()}\!')
    update.message.reply_text("Type /help to list commands.",\
                                                parse_mode=ParseMode.MARKDOWN)


""" Clear all scheduled quotes. """
def finish_command(update: Update, context: CallbackContext) -> None:
    for job in context.job_queue.jobs():
        job.schedule_removal()
    update.message.reply_text(
        "The schedule has been *cleared*.", parse_mode=ParseMode.MARKDOWN)


""" List all commands and their specifications. """
def help_command(update: Update, context: CallbackContext) -> None:    
    msg = ""
    msg += "*/start* - welcomes you.\n"
    msg += "*/now* - prints the current date and time " \
        "(in *YYYY:MM:DD - HH:MM:SS* format).\n"   
    msg += "*/random_quote* - immediately sends a quote.\n"
    msg += "*/set_period* <PARAMETER> - schedule periodic quotes. " \
        " Supported format for PARAMETER: *HH:MM:SS*.\n"
    msg += "*/once* <PARAMETER> - schedules a one-time-only quote."\
        "Supported format for PARAMETER: *HH:MM:SS*.\n"
    msg += "*/set_quotes* <PARAMETER> - used to resume or pause the scheduler"\
        " (note: pausing the scheduler does not remove the scheduled quotes)."\
                                    "PARAMETER must be either *on* or *off*.\n"
    msg += "*/finish* clears the schedule, removing all pending quotes.\n"
    msg += "\n*/help* prints this message.\n"
    update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


""" Non-command messages will be echoed. """
def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)


""" Send date and time in YYYY:MM:DD - HH:MM:SS format. """
def now_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(\
        datetime.datetime.now().strftime("%Y.%m.%d - %H:%M:%S"))


""" Enable or disable all scheduled jobs. """
def set_quotes_command(update: Update, context: CallbackContext) -> None:
    params = context.args
    if len(params) != 1:
        update.message.reply_text(
            "The set_quotes command takes a parameter, either \"on\" or "
                                                                    "\"off\".")
    else:
        toggle = params[0].upper().strip()
        if toggle == "ON":
            for job in context.job_queue.jobs():
                job.enabled = True
            context.job_queue.start()
            update.message.reply_text(\
                "Schedule is *active*.", parse_mode=ParseMode.MARKDOWN)
        elif toggle == "OFF":
            for job in context.job_queue.jobs():
                job.enabled = False
            update.message.reply_text(\
                "The whole schedule has been *paused*.",\
                parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text("The set_quotes command takes a \
                                        parameter, either \"on\" or \"off\".")


""" Schedule a new job to be issued periodically. """
def set_period_command(update: Update, context: CallbackContext) -> None:
    period_param = context.args
    if len(period_param) != 1:
        update.message.reply_text(\
                                "The set\_period command takes a parameter."\
                    " Supported format: *HH:MM:SS*, where 00 <= *HH* <= 99, "\
                                    "00 <= *MM* <= 59 and 00 <= *SS* <= 59.",\
                                                parse_mode=ParseMode.MARKDOWN)
    else:   
        context.job_queue.start()
        # Split the time parameter in hours, minutes and seconds
        param = period_param[0].strip().split(':',3)
        if not valid_time(param):
            update.message.reply_text(\
                                            "The set_period command takes a " \
                        "parameter representing the time between quotes. " \
                    "Supported format: *HH:MM:SS*, where 00 <= *HH* <= 99, " \
                                    "00 <= *MM* <= 59 and 00 <= *SS* <= 59.",\
                                                parse_mode=ParseMode.MARKDOWN)
        else:
            hours = int(param[0])
            minutes = int(param[1])
            seconds = int(param[2])
            
            # Finally, we schedule the job.
            period = datetime.timedelta(hours=hours,minutes=minutes,\
                                                            seconds=seconds)
            context.job_queue.run_repeating(\
                random_quote, period, context=update.message.chat_id)
            update.message.reply_text(\
                                    "A random quote will be issued every *" + \
                period_param[0].strip() + "*.", parse_mode=ParseMode.MARKDOWN)


""" Schedule a one-time-only quote. """
def once_command(update: Update, context: CallbackContext) -> None:
    period_param = context.args
    if len(period_param) != 1:
        update.message.reply_text(\
            "The */once* command takes a time parameter. Supported format: "\
                "*HH:MM:SS*, where 00 <= *HH* <= 99, 00 <= *MM* <= 59 and "\
                            "00 <= *SS* <= 59.", parse_mode=ParseMode.MARKDOWN)
    else:
        context.job_queue.start()
        # Split the time parameter in hours, minutes and seconds
        param = period_param[0].strip().split(':',3)
        if not valid_time(param):
            update.message.reply_text(\
                                    "The once command takes a time parameter."\
                        " Supported format: HH:MM:SS, where 00 <= HH <= 99, "\
                                        "00 <= MM <= 59 and 00 <= SS <= 59.")
        else:
            hours = int(param[0])
            minutes = int(param[1])
            seconds = int(param[2])

            # Finally, we schedule the job.
            period = datetime.timedelta(\
                                hours=hours, minutes=minutes,seconds=seconds)
            context.job_queue.run_once(\
                        random_quote, period, context=update.message.chat_id)
            update.message.reply_text(\
                                    "A random quote will be issued in *" + \
                period_param[0].strip() + "*.", parse_mode=ParseMode.MARKDOWN)


""" Auxiliary function for once_command and set_period_command. """
def random_quote(context: CallbackContext) -> None:
    # Open the JSON file containing the quotes, and convert it to a Pandas 
    # DataFrame (iterable). 
    data_frame = pandas.read_json("quotes.json")
    quote_number = randint(0,len(data_frame))
    msg = '\"' + str(data_frame["quoteText"][quote_number]) + '\" - ' + \
                                str(data_frame["quoteAuthor"][quote_number])
    context.bot.send_message(chat_id=context.job.context,text=msg)
        

""" Check that the input parameter has the right format. """
def valid_time(param: str) -> (str, str, str):
    # First, check that we exactly three elements (hours, minutes, seconds).
    if not (len(param) == 3):
        return False
    # Second, check if these elements are made of digits.
    if not (param[0].isdigit() and param[1].isdigit() and param[2].isdigit()):
        return False
    # Next, cast these elements to integerss, and check that they belong in the
    # appropriate range.
    hours = int(param[0])
    minutes = int(param[1])
    seconds = int(param[2])
    if 0 > hours or hours > 99 or \
        0 > minutes or minutes > 59 \
            or 0 > seconds or seconds > 59:
        return False

    return True


""" Send a random quote. """
def random_quote_command(update: Update, context: CallbackContext) -> None:
    params = context.args
    if len(params) != 0:
        update.message.reply_text("Discarding the provided parameters - the "
            "random_quote command takes none.")
    # Open the JSON file containing the quotes, and convert it to a Pandas 
    # DataFrame (iterable). 
    data_frame = pandas.read_json("quotes.json")
    quote_number = randint(0,len(data_frame))
    msg = '\"' + str(data_frame["quoteText"][quote_number]) + '\" - ' + \
                                str(data_frame["quoteAuthor"][quote_number])
    update.message.reply_text(msg)


def main() -> None:
    if len(sys.argv) != 2:
        print("Only supported usage: BaseBot.py <TOKEN>")
        sys.exit()

    # Start the bot by creating the Updater and passing it the input token.
    token = sys.argv[1]
    try:
        updater = Updater(token)
    except telegram.error.InvalidToken:
        print(\
            "The given token does not correspond to any working Telegram bot.")
        sys.exit()

    # Get the dispatcher and register the handlers corresponding to the 
    # commands recognized by the bot.
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CommandHandler("start", start_command))
    dispatcher.add_handler(
        CommandHandler("finish", finish_command))
    dispatcher.add_handler(
        CommandHandler("help", help_command))
    dispatcher.add_handler(
        CommandHandler("now", now_command))
    dispatcher.add_handler(
        CommandHandler("set_quotes", set_quotes_command))
    dispatcher.add_handler(
        CommandHandler("set_period", set_period_command))
    dispatcher.add_handler(
        CommandHandler("once", once_command))
    dispatcher.add_handler(
        CommandHandler("random_quote", random_quote_command))

    # Echo all non-command messages.
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot.
    updater.start_polling()

    # Run the bot until pressing Ctrl-C.
    updater.idle()


if __name__ == '__main__':
    main()
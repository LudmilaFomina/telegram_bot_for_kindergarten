#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

import logging
import csv
import datetime
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Unique token (Add your information here)
token = ""
# Path to the list file of all children (Add your information here)
path_to_file = ''
# Path to the directory in which files with absent children will be created (Add your information here)
dir_path = ''


# Creating a class and methods for working with children's data
class Child:
    def __init__(self, group, last_name, first_name, bd):
        self.group = group
        self.last_name = last_name
        self.first_name = first_name
        self.bd = bd

    def check_last_name(self, children):
        for i in children:
            if (self.group == i.group and
                    self.last_name == i.last_name):
                return True
        return False

    def check_first_name(self, children):
        for i in children:
            if (self.group == i.group and
                    self.last_name == i.last_name and
                    self.first_name == i.first_name):
                return True
        return False

    def check_bd(self, children):
        for i in children:
            if (self.group == i.group and
                self.last_name == i.last_name and
                self.first_name == i.first_name and
                    self.bd == i.bd):
                return True
        return False

# Create object which contains current child's data
child = Child('', '', '', '')


# Initialize all children's data from file
def parse_csv_file(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile)
        children = []
        for row in reader:
            children += [Child(row[0], row[1], row[2], row[3])]
    return children


# Create a list with all children
children = parse_csv_file(path_to_file)


# Functions for creating files in a directory with lists of absent children.
# A separate file is created for each date. The file name contains the date.
def get_today_as_str():
    """Return today date in string"""
    today = datetime.date.today()
    today_str = today.strftime('%Y_%m_%d')
    return today_str


def get_filename_for_today(dir_path, today_str):
    """Return file name which contains date"""
    filename = 'absent_children_' + today_str + '.csv'
    full_filename = os.path.join(dir_path, filename)
    return full_filename


def check_if_file_exists(full_filename):
    """Check if file with today's date already exists in directory"""
    file_exist = os.path.exists(full_filename)
    return file_exist


def append_child_to_file(child, full_filename):
    """Append absent child to file with today's data. File already exists"""
    data = [child.group, child.last_name, child.first_name, child.bd]
    with open(full_filename, 'a') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(data)


def create_file_with_child(child, full_filename):
    """Create file with today's date and append absent child to file. File not exists"""
    data = [['Group', 'Last name', 'First name', 'Birth date']]
    with open(full_filename, 'w') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(data)
    append_child_to_file(child, full_filename)


def append_absent_child(child, dir_path):
    """Combining all functions for creating a list of absent children into one function"""
    today = get_today_as_str()
    full_filename = get_filename_for_today(dir_path, today)
    if check_if_file_exists(full_filename):
        append_child_to_file(child, full_filename)
    else:
        create_file_with_child(child, full_filename)


# Determine the states by which the dialogue in the telegram bot moves
ST1, ST2, ST3, ST4, ST5 = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and offers to note the child’s absence"""
    reply_keyboard = [['Inform that the child will not come']]
    await update.message.reply_text(
        "Welcome to the Kindergarten bot!",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Please tap the button in menu"))

    return ST1


async def st1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores previous selection.
    Offers to select a kindergarten group"""
    user = update.message.from_user
    logger.info("%s wants to %s", user.first_name, update.message.text)

    reply_keyboard = [["Group 1", "Group 2"]]
    await update.message.reply_text(
        "Ok! Which group is your child in?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Please tap the button in menu"))

    return ST2


async def st2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores previous selection (group).
    Asks to enter the child's last name"""
    user = update.message.from_user
    if update.message.text == 'Group 1':
        child.group = '1'
    else:
        child.group = '2'
    logger.info("Group of %s: %s", user.first_name, child.group)

    await update.message.reply_text(
        "Ok! Write the child's last name please",
        reply_markup=ReplyKeyboardRemove())

    return ST3


async def st3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores previous selection (last name).
    Check if last name in base.
    Asks to enter the child's first name or end the conversation"""
    user = update.message.from_user
    child.last_name = update.message.text
    logger.info("Last name of %s: %s", user.first_name, child.last_name)

    if child.check_last_name(children):
        await update.message.reply_text(
            "Write the child's first name please")
        return ST4
    else:
        logger.info("Last name of %s: %s not in base", user.first_name, child.last_name)
        await update.message.reply_text(
            "I can’t find this child, try again with /start, please")
        return ConversationHandler.END


async def st4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores previous selection (first name).
    Check if first name in base.
    Asks to enter the child's birthdate or end the conversation"""
    user = update.message.from_user
    child.first_name = update.message.text
    logger.info("First name of %s: %s", user.first_name, child.first_name)

    if child.check_first_name(children):
        await update.message.reply_text("Write the child's birthdate (dd.mm.yy)")
        return ST5
    else:
        logger.info("First name of %s: %s not in base", user.first_name, child.first_name)
        await update.message.reply_text(
            "I can’t find this child, try again with /start, please")
        return ConversationHandler.END


async def st5(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores previous selection (birthdate).
    Check if birthdate in base.
    Ends the conversation with success or not"""
    user = update.message.from_user
    child.bd = update.message.text
    logger.info("Birthdate of %s: %s", user.first_name, child.bd)

    if child.check_bd(children):
        append_absent_child(child, dir_path)
        await update.message.reply_text("Successfully! Goodbye! Or /start again")
        return ConversationHandler.END
    else:
        logger.info("Birthdate of %s: %s not in base", user.first_name, child.bd)
        await update.message.reply_text(
            "I can’t find this child, try again with /start, please")
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation"""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Bye!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main() -> None:
    """Run the bot"""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # Add conversation handler with the states ST1, ST2, ST3, ST4, ST5
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ST1: [MessageHandler(filters.Regex("^(Inform that the child will not come)$"), st1)],
            ST2: [MessageHandler(filters.Regex("^(Group 1|Group 2)$"), st2)],
            ST3: [MessageHandler(filters.TEXT & ~filters.COMMAND, st3)],
            ST4: [MessageHandler(filters.TEXT & ~filters.COMMAND, st4)],
            ST5: [MessageHandler(filters.TEXT & ~filters.COMMAND, st5)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

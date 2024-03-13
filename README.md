# telegram_bot_for_kindergarten
A Telegram bot for kindergarten allows parents to send information that their child will not come to kindergarten today. 

The parent, in a dialogue with the bot, gives information: group number, last name, first name, date of birth of the child. At each stage, the data is checked against the group list, which allows us to weed out random people who do not have the correct information.

The bot uses a list of all children in the kindergarten.
The bot creates a list of children entered by parents in a separate file, the name of which contains today's date.
Samples of these files are in a separate directory.

________
Send /start to initiate the conversation. 

/cansel will end the conversation in every stage.

The bot runs until we press Ctrl-C on the command line.

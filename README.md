# QuotesBot
Configurable Telegram bot that schedules random motivational quotes. Implemented with the [python-telegram-bot](https://python-telegram-bot.readthedocs.io/en/stable/) API library.

Usage is QuotesBot.py <TOKEN>, where TOKEN must be a valid access token provided by [@BotFather](https://telegram.me/botfather).


QuotesBot accepts the following commmands:

+ **/start** - welcomes you.

+ **/now** - prints the current date and time (in **YYYY:MM:DD - HH:MM:SS** format).

+ **/random_quote** - immediately sends a quote.

+ **/set_period** *PARAMETER* - schedules periodic quotes. Supported format for *PARAMETER*: **HH:MM:SS**.

+ **/once** *PARAMETER* - schedules a one-time-only quote. Supported format for *PARAMETER*: **HH:MM:SS**.

+ **/set_quotes** *PARAMETER* - used to resume or pause the scheduler (note: pausing the scheduler does not remove the scheduled quotes). *PARAMETER* is either **on** or **off**.

+ **/finish** - clears the schedule, removing all pending quotes.

+ **/help** - prints commands and their usage.


All non-command messages are simply echoed.

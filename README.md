# Discord bot and web application for Epic 7 PvP stats

The repository contains both a discord bot (bot.py) as well as a web application (web.py) for looking up information as well as getting insights into Epic 7 RTA (real time arena) statistics.

## Instructions

To run the bot, create a .env file containing "TOKEN=MY_TOKEN" where MY_TOKEN is your Discord bot token. You can get link to add the bot to your Discord server as well as the bot token from Discord's official site: https://discord.com/developers/applications To use commands /legendstats and /legendherostats you will need to run get_legend_data.py once to fetch the data used. If you want the commands to have up-to-date data, run the file once a day. After the initial setup, you can run the bot simply by running the file bot.py; while the bot is running, you can use slash commands in any discord servers the bot is in. List of commands as well as short descriptions can be seen simply by typing "/" in discord and selecting the bot.

To run the web application you will similiarly need to run get_legend_data.py once (if not done already) and then run it once a day to keep the data updated. With this done, web application can be launched by running web.py and going to the localhost address shown. To host the application on a third party platform you will need to figure out how to host Flask web applications there.
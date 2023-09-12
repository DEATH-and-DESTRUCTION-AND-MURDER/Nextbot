# imports
import asyncio
import inspect
import platform
import time
from os import getcwd, getenv, makedirs, path, system

from discord.ext.commands import is_owner
import discord
from typing import Literal
from colorama import Back, Fore, Style
from discord.ext import commands

from dotenv import load_dotenv ; load_dotenv()

import settings
import platform
import cpuinfo

import traceback

#Disable discord.py's info logging
import logging ; logging.disable(30)

import xyn_locale

class Bot(commands.Bot):
    """Initializes the bot and it's modules, as well as the error handler"""
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('>.<'), intents=discord.Intents().all())

        # @self.tree.command(name="reload_cogs",description="Reloads all cogs!")
        # @is_owner()
        # async def reload_cogs(interaction: discord.Interaction,resync:Literal["No","Yes"]):
        #     await interaction.response.defer(thinking=True)
        #     for key, value in settings.modules.items():
        #         if value:
        #             if path.isfile(f"modules/{key}.py"):
        #                 await self.reload_extension(f"modules.{key}")
        #             elif path.isdir(f"modules/{key}"):
        #                 await self.reload_extension(f"modules.{key}.{key}")
        #             else:
        #                 print(f"The module {key} files are missing!")

        #     if resync == "Yes":
        #         await self.tree.sync()
            
        #     await interaction.followup.send("All cogs were reloaded!")

        # Error handler
        @self.tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.CommandInvokeError):
            try:
                raise error.original  # Re-raise the original exception to capture its traceback
            except Exception as e:
                traceback_str = traceback.format_exc()

                # Extract the relevant information from the traceback
                filename = None
                line_number = None

                for line in traceback_str.split("\n"):
                    if line.startswith("  File "):
                        filename_line = line.strip()
                        full_filename = filename_line[7:filename_line.rfind(",")]
                        filename = path.basename(full_filename)  # Get just the filename
                        line_number = filename_line[filename_line.rfind(",") + 1:].strip()

                timestamp = time.strftime('%d/%m/%Y %H:%M:%S MST')
                command_info = f"{interaction.command.module}.{interaction.command.name}"

                log = (
                    f"{timestamp}\nException: {command_info}:\nFile: {filename}, line {line_number}\n{error}"
                )

                if isinstance(error.original, discord.errors.InteractionResponded):
                    print(f"Interaction already acknowledged, {command_info}")
                elif isinstance(error.original, discord.app_commands.MissingPermissions):
                    await interaction.channel.send("You don't have permission to run that command!", ephemeral=True)
                elif isinstance(error.original, discord.app_commands.BotMissingPermissions):
                    await interaction.channel.send("I don't have permission to do that!", ephemeral=True)
                elif isinstance(error, discord.app_commands.CommandOnCooldown):
                    await interaction.channel.send(f"This command is in cooldown! Try again in {round(error.retry_after, 2)}", ephemeral=True)
                else:
                    await interaction.channel.send(
                        f"An uncaught exception has occurred, this occurrence has been automatically reported to your maintainer!:\nHere's the log:\n```{log}```"
                    )

                    log_filename = f"./logs/UncaughtException_{timestamp.replace(':', '-').replace('/','')}.txt"
                    logger = open(log_filename, "w")
                    logger.write(log)
                    logger.close()

    #Loads all the modules before starting up Xyn :3
    async def setup_hook(self):
        prfx = (Back.BLACK + Fore.MAGENTA + time.strftime("%H:%M:%S MST", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(prfx + " " + xyn_locale.internal.locale("loading_modules",settings.language))
        for key, value in settings.modules.items():
            if value: #If the module in the settings is actually enabled
                if path.isfile(f"modules/{key}.py"): #checks for single .py files that match current key iteration
                    await self.load_extension(f"modules.{key}") #Loads it
                elif path.isdir(f"modules/{key}"): #checks for folders matching the current key iteration
                    await self.load_extension(f"modules.{key}.{key}") #loads the .py file inside of it
                else:
                    print(f"The module {key} files are missing!") #Alert the user they did a fucky-wucky >.<
        print(prfx + " " + xyn_locale.internal.locale("loaded_modules",settings.language))
        await self.tree.sync() #Only uncomment this when implementing new commands, or Discord *will* rate limit you very quickly!

    async def on_ready(self):
        #Status task, updates the bot's presence every minute
        async def status_task(self):
            while True:
                await self.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming,name="past you nerds!",url="https://www.youtube.com/watch?v=HZCKddHYgPM"))
                await asyncio.sleep(60)
                await self.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,name="with you nerds!"))
                await asyncio.sleep(60)

        #Starts the status task
        bot.loop.create_task(status_task(self))
        prfx = (Back.BLACK + Fore.MAGENTA + time.strftime("%H:%M:%S MST", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(prfx + " " + xyn_locale.internal.locale("logged_in",settings.language).format(Fore.MAGENTA,self.user.name,Fore.RESET))
        print(prfx + " " + xyn_locale.internal.locale("running_mode",settings.language).format(Fore.GREEN,settings.mode.lower(),Fore.RESET))
        print(prfx + f" {Fore.CYAN}{xyn_locale.internal.locale('OS',settings.language)}: {platform.platform()} / {platform.release()}{Fore.RESET}")
        print(prfx + f" {Fore.CYAN}{xyn_locale.internal.locale('CPU',settings.language)}: {cpuinfo.get_cpu_info()['brand_raw']}{Fore.RESET}")
        print(prfx + " " + xyn_locale.internal.locale("python_version",settings.language) + Fore.YELLOW + str(platform.python_version()) + Fore.WHITE)
        print(prfx + " " + xyn_locale.internal.locale("discord_py.version",settings.language) + Fore.YELLOW + discord.__version__ + Fore.RESET)
        
bot = Bot()
#Checks for the runtime mode to initialize
if settings.mode.lower() == "retail":
    bot.run(getenv("token"))
elif settings.mode.lower() == "development":
    bot.run(getenv("development_token"))
else:
    print(xyn_locale.internal.locale("no_mode",settings.language))

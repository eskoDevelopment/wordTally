# ===================================================================
#  Project:       wordTally
#  Developer:     eskoDevelopment
#  License:       MIT License
# ===================================================================
#  Copyright (c) 2026 eskoDevelopment

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ===================================================================

# ===================================================================
#   Project:       wordTally
#   Developer:     eskoDevelopment
#   License:       MIT License
# ===================================================================
#   Copyright (c) 2026 eskoDevelopment

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ===================================================================

import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class WordTallyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.counters = {}

    async def setup_hook(self):
        await self.tree.sync()

bot = WordTallyBot()

@bot.event
async def on_ready():
    print(f"wordTally Bot is ready! Logged in as {bot.user} (ID: {bot.user.id})")
    
    # Broadcast startup message to available channels across all joined servers
    for guild in bot.guilds:
        target_channel = guild.system_channel

        if not target_channel or not target_channel.permissions_for(guild.me).send_messages:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    target_channel = channel
                    break

        if target_channel:
            try:
                await target_channel.send("wordTally active")
            except discord.Forbidden:
                pass

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = message.guild.id
    if guild_id not in bot.counters:
        return

    content_lower = message.content.lower()

    for name, config in bot.counters[guild_id].items():
        groups = config["groups"]
        
        all_groups_satisfied = all(
            any(alias in content_lower for alias in group) 
            for group in groups
        )

        if all_groups_satisfied:
            config["count"] += 1

            if config["instant"]:
                try:
                    await message.channel.send(f"Counter '{name}' triggered! Current count: {config['count']}")
                except discord.Forbidden:
                    pass

    await bot.process_commands(message)

@bot.tree.command(name="createtally", description="Create a custom multi-word tally counter with aliases.")
@app_commands.describe(
    name="The unique name of this counter",
    words="Comma-separated groups. Use '|' for aliases (e.g., 'cant wait,please|pleasing,david')",
    initial_count="The starting count number (default 0)",
    instant_notify="Send a message instantly when triggered? (True or False)"
)
async def createtally(
    interaction: discord.Interaction, 
    name: str, 
    words: str, 
    initial_count: int = 0, 
    instant_notify: bool = True
):
    guild_id = interaction.guild.id
    counter_name = name.lower().strip()

    if guild_id not in bot.counters:
        bot.counters[guild_id] = {}

    if counter_name in bot.counters[guild_id]:
        await interaction.response.send_message(f"Counter '{counter_name}' already exists.", ephemeral=True)
        return

    groups = []
    for part in words.split(","):
        aliases = [a.strip().lower() for a in part.split("|") if a.strip()]
        if aliases:
            groups.append(aliases)

    bot.counters[guild_id][counter_name] = {
        "groups": groups,
        "count": initial_count,
        "instant": instant_notify
    }

    await interaction.response.send_message(f"Successfully created tally '{counter_name}'.")

@bot.tree.command(name="edittally", description="Edit an existing tally counter's settings.")
@app_commands.describe(
    name="The name of the counter to edit",
    words="New comma/pipe separated words",
    new_count="Set a specific count number",
    instant_notify="Change instant notification setting"
)
async def edittally(
    interaction: discord.Interaction, 
    name: str, 
    words: str = None, 
    new_count: int = None, 
    instant_notify: bool = None
):
    guild_id = interaction.guild.id
    counter_name = name.lower().strip()

    counter = bot.counters.get(guild_id, {}).get(counter_name)
    if not counter:
        await interaction.response.send_message(f"Counter '{counter_name}' does not exist.", ephemeral=True)
        return

    if words:
        groups = []
        for part in words.split(","):
            aliases = [a.strip().lower() for a in part.split("|") if a.strip()]
            if aliases:
                groups.append(aliases)
        counter["groups"] = groups

    if new_count is not None:
        counter["count"] = new_count

    if instant_notify is not None:
        counter["instant"] = instant_notify

    await interaction.response.send_message(f"Successfully updated tally '{counter_name}'.")

@bot.tree.command(name="deletetally", description="Delete an existing tally counter.")
@app_commands.describe(name="The name of the counter to delete")
async def deletetally(interaction: discord.Interaction, name: str):
    guild_id = interaction.guild.id
    counter_name = name.lower().strip()

    if guild_id in bot.counters and counter_name in bot.counters[guild_id]:
        del bot.counters[guild_id][counter_name]
        await interaction.response.send_message(f"Successfully deleted counter '{counter_name}'.")
    else:
        await interaction.response.send_message(f"Counter '{counter_name}' does not exist.", ephemeral=True)

@bot.tree.command(name="tally", description="Check the current count and config for a tally.")
@app_commands.describe(name="The name of the counter")
async def tally(interaction: discord.Interaction, name: str):
    guild_id = interaction.guild.id
    counter_name = name.lower().strip()

    counter = bot.counters.get(guild_id, {}).get(counter_name)
    
    if not counter:
        await interaction.response.send_message(f"Counter '{counter_name}' does not exist.", ephemeral=True)
        return

    groups_text = ", ".join(
        "|".join(group) if len(group) > 1 else group[0]
        for group in counter["groups"]
    ) if counter["groups"] else "No words configured"

    await interaction.response.send_message(
        f"Tally Stats for '{counter_name}':\n"
        f"Words looking for: {groups_text}\n"
        f"• Current Count: {counter['count']}\n"
    )

@bot.tree.command(name="tallylist", description="List all tally counters in this server.")
async def tallylist(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    counters = bot.counters.get(guild_id, {})

    if not counters:
        await interaction.response.send_message("No tally counters found in this server.", ephemeral=True)
        return

    counter_list = "\n".join(f"• {name}" for name in counters.keys())
    await interaction.response.send_message(f"Tally Counters in this server:\n{counter_list}")

bot.run(token)
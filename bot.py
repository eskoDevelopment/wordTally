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

# ===================================================================
#   Project:       wordTally
#   Developer:     eskoDevelopment
#   License:       MIT License
# ===================================================================
#   Copyright (c) 2026 eskoDevelopment

import os
import sqlite3
import json
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

def init_db():
    conn = sqlite3.connect("tallies.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tallies (
            guild_id INTEGER,
            name TEXT,
            groups TEXT,
            count INTEGER,
            instant INTEGER,
            PRIMARY KEY (guild_id, name)
        )
    """)
    conn.commit()
    conn.close()

init_db()

class WordTallyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = WordTallyBot()

@bot.event
async def on_ready():
    print(f"wordTally Bot is ready! Logged in as {bot.user} (ID: {bot.user.id})")
    
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

    # Debug print: Verify message text is being captured in your terminal
    print(f"[{message.guild.name}] {message.author}: {message.content}")

    guild_id = message.guild.id
    content_lower = message.content.lower()

    conn = sqlite3.connect("tallies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, groups, count, instant FROM tallies WHERE guild_id = ?", (guild_id,))
    rows = cursor.fetchall()

    for row in rows:
        name, groups_json, count, instant = row
        groups = json.loads(groups_json)
        
        all_groups_satisfied = all(
            any(alias in content_lower for alias in group) 
            for group in groups
        )

        if all_groups_satisfied:
            new_count = count + 1
            cursor.execute(
                "UPDATE tallies SET count = ? WHERE guild_id = ? AND name = ?",
                (new_count, guild_id, name)
            )
            conn.commit()

            if instant:
                try:
                    await message.channel.send(f"Counter '{name}' triggered! Current count: {new_count}")
                except discord.Forbidden:
                    pass

    conn.close()
    await bot.process_commands(message)

@bot.tree.command(name="createtally", description="Create a custom multi-word tally counter with aliases.")
@app_commands.describe(
    name="The unique name of this counter",
    words="Comma-separated groups. Use '|' for aliases (e.g., 'cant wait,please|pleasing,david')",
    initial_count="The starting count number (default 0)",
    instant_notify="Send a message instantly when triggered? (True or False)"
)
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def createtally(
    interaction: discord.Interaction, 
    name: str, 
    words: str, 
    initial_count: int = 0, 
    instant_notify: bool = True
):
    guild_id = interaction.guild.id
    counter_name = name.lower().strip()

    groups = []
    for part in words.split(","):
        aliases = [a.strip().lower() for a in part.split("|") if a.strip()]
        if aliases:
            groups.append(aliases)

    conn = sqlite3.connect("tallies.db")
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM tallies WHERE guild_id = ? AND name = ?", (guild_id, counter_name))
    if cursor.fetchone():
        conn.close()
        await interaction.response.send_message(f"Counter '{counter_name}' already exists.", ephemeral=True)
        return

    cursor.execute(
        "INSERT INTO tallies (guild_id, name, groups, count, instant) VALUES (?, ?, ?, ?, ?)",
        (guild_id, counter_name, json.dumps(groups), initial_count, 1 if instant_notify else 0)
    )
    conn.commit()
    conn.close()

    await interaction.response.send_message(f"Successfully created tally '{counter_name}'.")

@bot.tree.command(name="edittally", description="Edit an existing tally counter's settings.")
@app_commands.describe(
    name="The name of the counter to edit",
    words="New comma/pipe separated words",
    new_count="Set a specific count number",
    instant_notify="Change instant notification setting"
)
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def edittally(
    interaction: discord.Interaction, 
    name: str, 
    words: str = None, 
    new_count: int = None, 
    instant_notify: bool = None
):
    guild_id = interaction.guild.id
    counter_name = name.lower().strip()

    conn = sqlite3.connect("tallies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT groups, count, instant FROM tallies WHERE guild_id = ? AND name = ?", (guild_id, counter_name))
    row = cursor.fetchone()

    if not row:
        conn.close()
        await interaction.response.send_message(f"Counter '{counter_name}' does not exist.", ephemeral=True)
        return

    current_groups, current_count, current_instant = row

    if words:
        groups = []
        for part in words.split(","):
            aliases = [a.strip().lower() for a in part.split("|") if a.strip()]
            if aliases:
                groups.append(aliases)
        current_groups = json.dumps(groups)

    if new_count is not None:
        current_count = new_count

    if instant_notify is not None:
        current_instant = 1 if instant_notify else 0

    cursor.execute(
        "UPDATE tallies SET groups = ?, count = ?, instant = ? WHERE guild_id = ? AND name = ?",
        (current_groups, current_count, current_instant, guild_id, counter_name)
    )
    conn.commit()
    conn.close()

    await interaction.response.send_message(f"Successfully updated tally '{counter_name}'.")

@bot.tree.command(name="deletetally", description="Delete an existing tally counter.")
@app_commands.describe(name="The name of the counter to delete")
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def deletetally(interaction: discord.Interaction, name: str):
    guild_id = interaction.guild.id
    counter_name = name.lower().strip()

    conn = sqlite3.connect("tallies.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tallies WHERE guild_id = ? AND name = ?", (guild_id, counter_name))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted > 0:
        await interaction.response.send_message(f"Successfully deleted counter '{counter_name}'.")
    else:
        await interaction.response.send_message(f"Counter '{counter_name}' does not exist.", ephemeral=True)

@bot.tree.command(name="tally", description="Check the current count and config for a tally.")
@app_commands.describe(name="The name of the counter")
async def tally(interaction: discord.Interaction, name: str):
    guild_id = interaction.guild.id
    counter_name = name.lower().strip()

    conn = sqlite3.connect("tallies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT groups, count FROM tallies WHERE guild_id = ? AND name = ?", (guild_id, counter_name))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await interaction.response.send_message(f"Counter '{counter_name}' does not exist.", ephemeral=True)
        return

    groups_json, count = row
    groups = json.loads(groups_json)

    groups_text = ", ".join(
        "|".join(group) if len(group) > 1 else group[0]
        for group in groups
    ) if groups else "No words configured"

    await interaction.response.send_message(
        f"Tally Stats for '{counter_name}':\n"
        f"Words looking for: {groups_text}\n"
        f"Current Count: {count}"
    )

@bot.tree.command(name="listtallies", description="List all tally counters in this server.")
async def listtallies(interaction: discord.Interaction):
    guild_id = interaction.guild.id

    conn = sqlite3.connect("tallies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM tallies WHERE guild_id = ?", (guild_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await interaction.response.send_message("No tally counters found in this server.", ephemeral=True)
        return

    counter_list = "\n".join(f"- {row[0]}" for row in rows)
    await interaction.response.send_message(f"Tally Counters in this server:\n{counter_list}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message("You do not have permission to manage tallies. Requires 'Manage Messages'.", ephemeral=True)
        else:
            await interaction.followup.send("You do not have permission to manage tallies. Requires 'Manage Messages'.", ephemeral=True)
    else:
        raise error

bot.run(token)
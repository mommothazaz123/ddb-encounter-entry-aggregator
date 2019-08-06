import collections
import os

from discord.ext.commands import Bot

import ddb
from constants import ENTRY_CHANNEL, LOG_CHANNEL, SERVER_ID, URL_RE, VOTING_REACTION
from entries import Entry

TOKEN = os.getenv("TOKEN")

bot = Bot('.')


@bot.event
async def on_ready():
    print(f"Ready! Logged in as {bot.user} ({bot.user.id})")


@bot.event
async def on_message(message):
    if not message.channel.id == ENTRY_CHANNEL:
        return await bot.process_commands(message)
    match = URL_RE.search(message.content)
    if not match:
        return

    await log_entry(message.author, match.group(1))


# ===== COMMANDS =====

@bot.command()
async def verify(ctx, url):
    match = URL_RE.search(url)
    if not match:
        return await ctx.send("No URL found.")

    await log_entry(ctx.author, match.group(1), ctx.channel)


@bot.command()
async def check_dupes(ctx):
    entries = collections.defaultdict(lambda: [])
    async with ctx.typing():
        async for message in entry_channel_history(limit=None):
            match = URL_RE.search(message.content)
            if not match:
                continue
            entries[message.author.id].append(Entry(message.author.id, match.group(1), message.id))

    out = []
    for user, chars in entries.items():
        if len(chars) < 2:
            continue
        member = bot.get_guild(SERVER_ID).get_member(user)
        warn = f"__{member} has {len(chars)} entries__\nin order (newest first):\n"
        for char in chars:
            warn += f"{char.message_link}\n"
        out.append(warn.strip())

    await ctx.send('\n\n'.join(out))


@bot.command()
async def setup_reactions(ctx):
    i = 0
    async with ctx.typing():
        async for message in entry_channel_history(limit=None):
            match = URL_RE.search(message.content)
            if not match:
                continue
            await message.add_reaction(VOTING_REACTION)
            i += 1
    await ctx.send(f"Set up reactions on {i} messages!")


@bot.command()
async def get_reactions(ctx):
    entries = collections.defaultdict(lambda: [])
    async with ctx.typing():
        async for message in entry_channel_history(limit=None):
            match = URL_RE.search(message.content)
            if not match:
                continue
            if message.reactions:
                entries[message.author.id].append(
                    Entry(message.author.id, match.group(1), message.id, message.reactions[0].count - 1))  # -1 for bot

    to_sort = list(entries.items())
    sorted_entries = sorted(to_sort, key=lambda e: e[1][0].votes, reverse=True)

    top_10 = []
    for top in sorted_entries[:10]:
        user, entries = top
        entry = entries[0]
        top_10.append(f"<@{user}> ({entry.votes}): <{entry.char_link}>")

    out = '\n'.join(top_10)
    await ctx.send(f"__Top 10__\n{out}")


# ===== HELPERS =====

async def log_entry(author, char_id, destination=None):
    print(f"Logging entry for {author.id}")
    if not destination:
        destination = bot.get_channel(LOG_CHANNEL)
        if not destination:
            return

    url = f"https://ddb.ac/characters/{char_id}/"
    try:
        warnings, info = await ddb.validate_character(char_id)
    except ddb.ExternalImportError as e:
        warnings = [f"Unable to access character: {e}"]
        info = []
    except Exception as e:
        warnings = [f"Unable to validate: {e}"]
        info = []

    warn_out = [f":exclamation: {warn}" for warn in warnings]
    out = '\n'.join(info + warn_out)

    await destination.send(f"`{author.id}` ({author.mention}): <{url}>\n"
                           f"{out}")


async def entry_channel_history(**kwargs):
    entry_chan = bot.get_channel(ENTRY_CHANNEL)
    if not entry_chan:
        raise RuntimeError("Could not find entry channel.")

    async for message in entry_chan.history(**kwargs):
        yield message


if __name__ == '__main__':
    bot.run(TOKEN)

import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
import asyncio
import random
import datetime
import smtplib
import typing
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

from bans_db import BansDB
from validation import classify_email_input, VALID_EMAIL_DOMAINS

# --- Logging setup ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("roaree")

# Set working directory to project root
os.chdir(Path(__file__).resolve().parent.parent)

load_dotenv()
intents = discord.Intents.all()
intents.typing = False
intents.presences = False
intents.guilds = True
intents.members = True

prefix = '?'
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWD = os.getenv('EMAIL_PASSWD')
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
VERIF_CHANNEL = int(os.getenv('VERIF_CHANNEL'))
BOOT_CHANNEL = int(os.getenv('BOOT_CHANNEL'))
ALERT_CHANNEL = int(os.getenv('ALERT_CHANNEL'))
POLITICS_CHANNEL = int(os.getenv('POLITICS_CHANNEL'))
GURU = int(os.getenv('GURU'))
COMMAND_DEL_CHANNEL = int(os.getenv('COMMAND_DEL_CHANNEL'))
LOG_CHANNEL = int(os.getenv('LOG_CHANNEL'))

client = commands.Bot(command_prefix=prefix, intents=intents)

# Timeout for user responses during verification (5 minutes)
VERIFY_TIMEOUT = 300

# --- Ban database ---

bans_db = BansDB()

# Migrate bans.txt to SQLite on first run (idempotent)
_migrated = bans_db.import_from_text("bans.txt")
if _migrated:
    logger.info("Migrated %d bans from bans.txt to SQLite", _migrated)


# --- Helpers ---

def get_guild():
    return client.get_guild(GUILD_ID)


def get_guru_role(guild):
    return discord.utils.find(lambda r: r.id == GURU, guild.roles)


def is_privileged(member, guild):
    """Check if a member is an admin or has the guru role."""
    guru = get_guru_role(guild)
    return member.guild_permissions.administrator or guru in member.roles


def user_tag(user):
    """Return 'Username (ID)' string for logging."""
    return f"{user} ({user.id})"


async def log(logchannel, msg, *, level=logging.INFO):
    """Log to both Python logger and the Discord log channel."""
    logger.log(level, msg)
    if logchannel:
        await logchannel.send(msg)


# --- Permission check decorator ---

def privileged():
    """commands.check that requires admin or guru role."""
    async def predicate(ctx):
        guild = get_guild()
        return is_privileged(ctx.author, guild)
    return commands.check(predicate)


# --- Events ---

@client.event
async def on_ready():
    bootchannel = client.get_channel(BOOT_CHANNEL)
    await bootchannel.send('Booted.')
    logger.info("Bot is ready. Logged in as %s", client.user.display_name)


@client.event
async def on_message(message):
    logger.debug("#%s: %s: %s", message.channel, message.author, message.content)

    try:
        await client.process_commands(message)
    except Exception as e:
        logger.error("Command processing failed for '%s': %s", message.content, e)

    try:
        if message.channel.id == COMMAND_DEL_CHANNEL and not message.author.bot:
            await message.delete()
            logger.info("Deleted message in #%s from %s", message.channel, message.author)
    except discord.NotFound:
        logger.debug("Message already deleted.")
    except discord.Forbidden:
        logger.warning("Missing permissions to delete message in #%s", message.channel)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        return  # Silently ignore unprivileged users
    raise error


# --- Ban management commands ---

@client.command(name='banemail')
@privileged()
async def banemail(ctx, email):
    """Bans a user by email."""
    if not bans_db.add(email, banned_by=str(ctx.author)):
        await ctx.send(f'{email} is already banned.')
        return

    verifchannel = client.get_channel(VERIF_CHANNEL)
    msg = f'{email} banned by {ctx.author}'
    await verifchannel.send(msg)
    await ctx.send(msg)
    logger.info(msg)


@client.command(name='unbanemail')
@privileged()
async def unbanemail(ctx, email):
    """Unbans a user by email."""
    if bans_db.remove(email):
        msg = f'{email} unbanned by {ctx.author}'
        verifchannel = client.get_channel(VERIF_CHANNEL)
        await verifchannel.send(msg)
        await ctx.send(msg)
        logger.info(msg)
    else:
        await ctx.send(f'{email} was not found in the ban list.')


@client.command(name='bans')
@privileged()
async def bans(ctx):
    """Lists all banned emails."""
    ban_list = bans_db.list_all()
    if not ban_list:
        await ctx.send("No banned emails.")
    else:
        await ctx.send("Banned emails:\n" + "\n".join(ban_list))


@client.command(name='isbanned')
@privileged()
async def isbanned(ctx, email):
    """Checks if an email is banned."""
    if bans_db.is_banned(email):
        await ctx.send(f'{email} is banned.')
    else:
        await ctx.send(f'{email} is not banned.')


# --- Verification commands ---

@client.command(name='unverify')
async def unverify(ctx):
    f"""Unverifies the user. To access verified channels again, type {prefix}verify."""
    logchannel = client.get_channel(LOG_CHANNEL)

    roleids = [870233517156597800, 871156035845509121, 871152677835386900, 871172200881848361]
    roleadd = [870555161007902781]
    guild = get_guild()
    roles_to_remove = [discord.utils.find(lambda r, rid=rid: r.id == rid, guild.roles) for rid in roleids]
    roles_to_add = [discord.utils.find(lambda r, rid=rid: r.id == rid, guild.roles) for rid in roleadd]
    user = guild.get_member(ctx.author.id)

    for role in roles_to_remove:
        if role:
            await user.remove_roles(role)
    for role in roles_to_add:
        if role:
            await user.add_roles(role)

    await ctx.send(f"I have removed your verified roles. Type {prefix}verify to add them again.")
    await log(logchannel, f"{user_tag(ctx.author)} unverified themself.")


@client.command(name='verify')
async def verify(ctx):
    """Completes the verification process. Sends an email with a verification code to your Columbia/Barnard email address. Your name and discord handle are never shared."""
    guild = get_guild()
    logchannel = client.get_channel(LOG_CHANNEL)

    roleids = [870233517156597800, 871156035845509121, 871152677835386900, 871172200881848361]
    rolerem = [870555161007902781, 1124826215337955328]
    verified_role = discord.utils.find(lambda r: r.id == 870233517156597800, guild.roles)
    roles_to_add = [discord.utils.find(lambda r, rid=rid: r.id == rid, guild.roles) for rid in roleids]
    roles_to_remove = [discord.utils.find(lambda r, rid=rid: r.id == rid, guild.roles) for rid in rolerem]
    user = guild.get_member(ctx.author.id)
    channel = await ctx.author.create_dm()

    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass

    if verified_role in user.roles and not is_privileged(ctx.author, guild):
        await channel.send("You are already verified. If this is a mistake, please contact staff.")
        return

    # Prompt for email
    await channel.send(
        "Send your Columbia or Barnard email to verify your identity. "
        "You will receive an email to your school inbox with a six-digit verification code."
    )
    await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} started verification from #{ctx.channel}")

    if channel != ctx.channel:
        sentmessage = await ctx.channel.send("DM Sent.")
        await asyncio.sleep(5)
        await sentmessage.delete()

    # Wait for email input
    try:
        rcs_msg = await client.wait_for(
            'message',
            check=lambda m: m.channel == channel and m.author.id == ctx.author.id,
            timeout=VERIFY_TIMEOUT,
        )
    except asyncio.TimeoutError:
        await channel.send(f"Verification timed out. Type {prefix}verify to try again.")
        await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} timed out waiting for email")
        return

    email_input = str(rcs_msg.content).strip()
    await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} provided email: {email_input}")

    # Validate email
    status, detail = classify_email_input(email_input, prefix=prefix)

    if status == "valid":
        email = detail
    elif status == "invalid_domain":
        await channel.send(detail)
        await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} invalid email domain: {email_input}")
        return
    elif status == "cancelled":
        await channel.send("Verification cancelled.")
        await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} cancelled verification")
        return
    else:
        await channel.send(f"An error occurred. Please type {prefix}verify to try again.")
        await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} invalid input: {email_input}")
        return

    # Check if email is banned
    if bans_db.is_banned(email):
        await channel.send("You have been banned from the server. If you think this is a mistake, please contact staff.")
        await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} attempted with banned email: {email}")
        return

    # Send verification email
    await channel.send(f"Sending verification email to {email}...")
    code = str(random.randint(0, 999999)).zfill(6)
    await log(logchannel, f"[VERIFY] Sending code to {user_tag(ctx.author)} at {email}")

    content = (
        f"Dear community member,\n\n"
        f"Your verification code is {code}.\n\n"
        f"If you did not request a code, please disregard this email.\n\n"
        f"Sincerely,\n\nthe mod team."
    )

    try:
        msg = MIMEText(content, 'plain')
        msg['Subject'] = 'Columbia Student Discord Verification'
        msg['From'] = f'Columbia Community Discord Verification <{EMAIL_USER}>'
        msg['To'] = f'<{email}>'
        msg['Date'] = formatdate(usegmt=True)

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.set_debuglevel(False)
        server.login(EMAIL_USER, EMAIL_PASSWD)

        try:
            server.sendmail(EMAIL_USER, email, msg.as_string())
        except Exception as e:
            await log(logchannel, f"[VERIFY] ERROR: Failed to send email to {user_tag(ctx.author)}: {e}", level=logging.ERROR)
            await channel.send("Failed to send email. Please try again later or contact staff.")
            return
        finally:
            server.close()

    except Exception as e:
        await log(logchannel, f"[VERIFY] ERROR: SMTP connection failed for {user_tag(ctx.author)}: {e}", level=logging.ERROR)
        await channel.send("Failed to send email. Please try again later or contact staff.")
        return

    await channel.send(
        "Verification email sent. Please enter the six-digit code you received. "
        "If you don't receive an email, check your spam folder."
    )

    # Wait for verification code
    try:
        code_msg = await client.wait_for(
            'message',
            check=lambda m: m.channel == channel and m.author.id == ctx.author.id,
            timeout=VERIFY_TIMEOUT,
        )
    except asyncio.TimeoutError:
        await channel.send(f"Verification timed out. Type {prefix}verify to try again.")
        await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} timed out waiting for code")
        return

    code_input = str(code_msg.content).strip()
    await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} entered code")

    if code_input != code:
        await channel.send(f"Incorrect code. Type {prefix}verify to try again.")
        await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} entered incorrect code")
        return

    # Verification successful — assign roles
    for role in roles_to_add:
        if role:
            await user.add_roles(role)
    for role in roles_to_remove:
        if role:
            await user.remove_roles(role)

    await channel.send(
        "Thank you for verifying your student status. Your identity will never be shared "
        "with the University or the public. You now have access to the server."
    )
    verifchannel = client.get_channel(VERIF_CHANNEL)
    await log(logchannel, f"[VERIFY] {user_tag(ctx.author)} verified as {email}")
    await verifchannel.send(f"{email} = <@{user.id}> ({user.id})")


# --- Admin utility commands ---

@client.command(name='delete')
async def delete(ctx, msgID: int):
    """Deletes a message by ID."""
    if ctx.author.id != 140951260323905537:
        return
    msg = await ctx.fetch_message(msgID)
    await msg.delete()


@client.command(name='ban')
async def ban(ctx, member: discord.Member, *, reason=None):
    """Bans a member."""
    if ctx.author.id != 140951260323905537:
        return
    await member.ban(reason=reason)


@client.command(name='update')
@privileged()
async def update(ctx):
    """Pulls from source and restarts."""
    await ctx.send('Pulling from source...')
    os.system('git pull')
    await asyncio.sleep(5)
    await ctx.send('Restarting...')
    os.system('sudo systemctl restart roaree.service')


@client.command(name='restart')
@privileged()
async def restart(ctx):
    """Restarts the bot."""
    await ctx.send('Restarting...')
    os.system('sudo systemctl restart roaree.service')


@client.command(name='echo')
@privileged()
async def echo(ctx):
    """Echoes your message."""
    await ctx.send(str(ctx.message.content)[6:])
    await ctx.message.delete()


@client.command(name='clear')
async def clear(ctx, number: typing.Union[int, str] = 0):
    f"""{prefix}clear N deletes your last N messages. {prefix}clear all deletes all your messages in the channel."""
    def is_requester(msg):
        return msg.author == ctx.author

    async with ctx.typing():
        if isinstance(number, str):
            if number.lower() != 'all':
                response = await ctx.send(f'Not a valid clear command. Did you mean `{prefix}clear all`?')
                await asyncio.sleep(5)
                await ctx.message.delete()
                await response.delete()
                return

            deleted = await ctx.channel.purge(limit=None, check=is_requester)
        else:
            deleted = await ctx.channel.purge(limit=number + 1, check=is_requester)

    await ctx.send(f':white_check_mark: deleted {len(deleted)} messages')


# --- Help ---

class NewHelp(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)


client.help_command = NewHelp()
client.run(TOKEN)

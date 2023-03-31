from tokenize import String
import discord
from discord.ext import commands
import os
import sys
from dotenv import load_dotenv
import asyncio
import json
import random
import datetime
# from locallib import directorysearch
import re
import datetime
import smtplib
import typing
from email.mime.text import MIMEText
from email.utils import formatdate
import aiohttp
from bs4 import BeautifulSoup
import html2text

# os.environ['TZ'] = 'America/New_York'
# os.system("TZ='America/New_York'; export TZ")
print(os.getcwd())
os.chdir(str(__file__)[:-6] + '..')
print(os.getcwd())

# scoredict = {}
load_dotenv()
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.guilds = True
intents.members = True
# intents.channels = True

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
client = commands.Bot(command_prefix = prefix, intents=intents)
currentguild = 'rpi'
id = str(random.randint(0,999999999)).zfill(9)

@client.event
async def on_ready():
    bootchannel = client.get_channel(BOOT_CHANNEL)
    await bootchannel.send('Booted.')
    # global scoredict
    print("Bot is ready.")
    print("Logged in as", client.user.display_name)
    # try:
    #     x = datetime.datetime
    #     os.system('sudo cp data/scores.json data/scores.json.' + str(x.now()).replace(' ','-') + '.bak')
    #     with open("data/scores.json", 'r') as f:
    #         scoredict = json.load(f)
    # except Exception as e:
    #     print(e)
    # # print("Scores:")
    # # print(scoredict)
             

@client.event
async def on_message(message):
    # global scoredict
    global id
    # Triggers whenever a message is sent in a channel the bot has access to view, in all guilds.
    print(str(message.channel) + ': ' + str(message.author) + ':',message.content)

    try:
        await client.process_commands(message)
    except Exception as e:
        print(e)
        print(f"command in message {str(message.content)} failed.")
    try:
        if message.channel.id == COMMAND_DEL_CHANNEL and not message.author.bot:
            await message.delete()
            print(f'deleted message {str(message.content)} in {str(message.channel)}')
    except:
        print('message already deleted.')

# class WelcomeBot(commands.Cog):
#     def __init__(self, bot):
#         self.client = client
#         self._last_member = None
#         self.messages = ["I am the one true welcome bot.",]
#         self.time = 0

#     @commands.Cog.listener()
#     async def on_member_join(self, member):
#         channel = member.guild.system_channel
#         if channel is not None:
#             await channel.send(f"Hello {member.mention}! Welcome to the /r/RPI Discord server. Most of the talk happens in student and alumni-only channels. Go to #welcome and follow the steps posted at the top of the channel to get verified. If you're an incoming student, just say so and we will give you the role.")


#     @commands.command(name='welcome')
#     async def welcome(self, ctx):
#         """Welcomes the new user"""
#         if time.time() - self.time() < 60:
#             await ctx.send('I am the superior welcome bot.')
#             self.time = time.time()

# async def update_stats():
#     await client.wait_until_ready()
#     await asyncio.sleep(15)
#     print('stats updater running')
#     global scoredict
#     while True:
#         print('log set')
#         try:
#             with open("data/scores.json", 'w') as f:
#                 # print(scoredict)
#                 json.dump(scoredict,f)
#         except Exception as e:
#             print(e)
#         await asyncio.sleep(1800)

# async def update_alerts():
#     await client.wait_until_ready()
#     await asyncio.sleep(20)
#     print("alerts updater running")
#     alerturl = r'https://alert.rpi.edu/'
#     lastalert = ""
#     while True:
#         await asyncio.sleep(600)
#         async with aiohttp.ClientSession() as session:
#             async with session.get(alerturl) as alerttxt:
#                 content = await alerttxt.text()
#                 soup = BeautifulSoup(content, "lxml")
#                 incident_type = "incident"
#                 alert = None
#                 for incident in soup.findAll("div", {"class": incident_type}):
#                     alert = html2text.html2text(str(incident))

#                 if alert == "":
#                     continue
#                 elif alert == None:
#                     continue
#                 elif alert == lastalert:
#                     continue
#                 else:
#                     # A new RPI alert has been posted.
#                     lastalert = alert
#                     alertchannel = client.get_channel(ALERT_CHANNEL)
#                     embed=discord.Embed(color=0xd6001c)
#                     embed.add_field(name="A new RPI alert has been posted", value=alert.replace('\n',' '), inline=True)
#                     embed.set_image(url=r"https://cdn.discordapp.com/attachments/792649866416881678/820760056395595776/Screenshot_from_2021-03-14_16-46-37.png")
#                     message1 = await alertchannel.send(embed=embed)
#                     await message1.publish()

# @client.command(name="testalert")
# async def testalert(ctx):
#     """
#     Sends a test alert in the alerts channel.
#     """
#     guild = client.get_guild(GUILD_ID)
#     user = discord.utils.find(lambda m: m.id == ctx.message.author.id, guild.members)
#     if not user.guild_permissions.administrator:
#         await ctx.send("Permission denied")
#         return
#     alertchannel = client.get_channel(ALERT_CHANNEL)
#     embed=discord.Embed(color=0xd6001c)
#     embed.add_field(name="A new RPI alert has been posted", value="This is a test of the alert system. You may safely disregard this message.", inline=True)
#     embed.set_image(url=r"https://cdn.discordapp.com/attachments/792649866416881678/820760056395595776/Screenshot_from_2021-03-14_16-46-37.png")
#     message1 = await alertchannel.send(embed=embed)
#     await message1.publish()
#     await ctx.send("Test complete.")
    

# @client.command(name='code')
# async def code(ctx):
#     """
#     Sends a github link with my source code.
#     """
#     await ctx.message.channel.send('https://github.com/rshin7/roaree')

# @client.command(name='source')
# async def source(ctx):
#     """
#     An alias for command 'code.'
#     """
#     await ctx.message.channel.send('https://github.com/rshin7/roaree')

@client.command(name='unverify')
async def unverify(ctx):
    f"""
    Unverifies the user. To access verified channels again, type {prefix}verify.
    """
    
    roleids = [870233517156597800, 871156035845509121, 871152677835386900, 871172200881848361]
    roleadd = [870555161007902781]
    guild = client.get_guild(GUILD_ID)
    roles_to_remove = [discord.utils.find(lambda r: r.id == roleid, guild.roles) for roleid in roleids]
    roles_to_add = [discord.utils.find(lambda r: r.id == roleid, guild.roles) for roleid in roleadd]
    user = discord.utils.find(lambda m: m.id == ctx.message.author.id, guild.members)
    for role in roles_to_remove:
        await user.remove_roles(role)
    for role in roles_to_add:
        await user.add_roles(role)
    await ctx.send(f"I have removed your verified roles. Type {prefix}verify to add them again.")


@client.command(name='verify')
async def verify(ctx):
    """
    Completes the verification process for unverified users. Checks the directory to ensure user is a student, then sends an email with a verification code to user's Columbia/Barnard email address. Your name or discord handle are never shared with the public or the University.
    """

    ## Checks that the user is not already verified in the operating server:

    guild = client.get_guild(GUILD_ID)
    roleids = [870233517156597800, 871156035845509121, 871152677835386900, 871172200881848361]
    rolerem = [870555161007902781]
    verified = discord.utils.find(lambda r: r.id == 870233517156597800, guild.roles)
    roles_to_add = [discord.utils.find(lambda r: r.id == roleid, guild.roles) for roleid in roleids]
    roles_to_remove = [discord.utils.find(lambda r: r.id == roleid, guild.roles) for roleid in rolerem]
    user = discord.utils.find(lambda m: m.id == ctx.message.author.id, guild.members)
    channel = await ctx.message.author.create_dm()
    try:
        await ctx.message.delete()
    except:
        print("Message was in a DM. Could not delete.")

    guru = discord.utils.find(lambda r: r.id == GURU, guild.roles)

    if verified in user.roles and not user.guild_permissions.administrator and not guru in ctx.message.author.roles:# and False:
        await channel.send("You are already verified. If this is a mistake, please contact staff.")
        return
    
    ## Sends an instructional DM to the user:

    mymessage = await channel.send('Send your Columbia or Barnard email to verify your identity. You will recieve an email to your school inbox with a six-digit verificaion code.')
    
    if channel != ctx.message.channel:
        sentmessage = await ctx.message.channel.send("DM Sent.")
        await asyncio.sleep(5)
        await sentmessage.delete()

    print('verifying ' + str(ctx.message.author))

    ## Waits for user to send their rcs id or email. Checks that the next message is not from the bot:
    print("awaiting rcs_msg")
    rcs_msg = await client.wait_for('message', check = lambda message: \
        (message.channel == channel) and (message.author.id == ctx.author.id))
    if rcs_msg.author == mymessage.author:
        print("ERROR 1")
        return
    print("rcs_msg found")
    email_msg = str(rcs_msg.content).strip()
    
    ## Processes the message and determines whether it is a valid ID/email: 
    emails = ["@columbia.edu", 
    "@barnard.edu", 
    "@tc.columbia.edu", 
    "@cumc.columbia.edu",
    "@ldeo.columbia.edu",
    "@gsb.columbia.edu",
    "@cs.columbia.edu",
    "@caa.columbia.edu"]
    print("email = " + email_msg)
    if re.findall(r'@[\w\.-]+', email_msg)[0].lower() in emails:
        email = email_msg
    elif '@' in email_msg:
        print('invalid email address ' + str(user))
        await channel.send(str(rcs_msg.content) + ' is an invalid e-mail address. You must use an email address ending in ```' + '\n'.join(emails) + '``` If you think your email should be valid, please contact staff. Type ' + prefix + 'verify to try again.')
        return
    elif email_msg[0] == prefix:
        print(str(user) + ' quit verification')
        return
    else:
        print(str(user) + ' inputted invalid id')
        await channel.send(f'An error ocurred. Please type {prefix}verify to try again.')
        return

    ## Searches the directory and checks whether the given RCS id is a student:

    # with open('data/directory.json','r') as f:
        # directory = json.load(f)

    # if email in directory.keys():
        # for future implementation
        # pass          
    
    # dsearch = await directorysearch.check_is_student(rcs)

    # if not dsearch[0]:
    #     role = dsearch[1].replace('&amp;','&')
    #     name = dsearch[2]
    #     print(str(user) + ' inputted non-student id')
    #     await channel.send(name + ' is not a student. Your role is ' + role + '.')
    #     return

    await channel.send("Sending verification email to " + email + ".\n\nPlease type in the recieved six-digit verification code.")
    
    ## Generates a code and email content:

    code = str(random.randint(0,999999)).zfill(6)
    print('code:', code)
    text_subtype = 'plain'
    content = "Dear community member,\n\nYour verification code is %s. \n\nIf you did not request a code, please disregard this email.\n\nSincerely,\n\nthe mod team." % code
    
    sender = EMAIL_USER
    destination = email
    subject = 'Columbia Student Discord Verification'

    ## MIME formats and sends the email using the given email username and password:

    try:
        # print(EMAIL_USER,EMAIL_PASSWD)
        msg = MIMEText(content,text_subtype)
        msg['Subject'] = subject
        msg['From'] = 'Columbia Community Discord Verification <' + sender + '>'
        msg['To'] = '<' + destination + '>'
        msg['Date'] = formatdate(usegmt=True)

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.set_debuglevel(False)
        server.login(EMAIL_USER,EMAIL_PASSWD)
        


        try:
            server.sendmail(sender,destination,msg.as_string())
        
        finally:
            server.close()
        
        print('Email sent.')

    except Exception as e1:
        print(e1)
        print('email not sent to ' + str(user))
        # return

    print('waiting...')

    ## Waits for verification code and checks that the code is correct:
    code_msg = await client.wait_for('message', check = lambda message: \
        (message.channel == channel) and (message.author.id == ctx.author.id))
    print("code recieved")
    if code_msg.author == mymessage.author:
        print(str(user) + ": UNKNOWN ERROR. ABORT")
        return
    code_msg = str(code_msg.content).strip()
    if code_msg != code:
        print("invalid code")
        await channel.send("Incorrect code. Type " + prefix + "verify to try again.")
        return
    ## Verifies the user:
    else:
        print('code valid')
        # studentrole = discord.utils.find(lambda r: r.name == 'Students', guild.roles)
        for role in roles_to_add:
            print(role)
            await user.add_roles(role)
        for role in roles_to_remove:
            print(role)
            await user.remove_roles(role)
        await channel.send("Thank you for verifying your student status. Your identity will never be shared with the University or the public. You now have access to the server.")

        newchannel = client.get_channel(VERIF_CHANNEL)
        await newchannel.send(str(email) + " = <@" + str(user.id) + "> (" + str(user.id) + ")")
        print(f'user {str(user)} verified as {email}.')
    
    return

@client.command(name='delete')
async def delete(ctx,msgID: int):
    """
    Deletes a comment.
    """
    if ctx.author.id != 140951260323905537:
        return
    msg = await ctx.fetch_message(msgID)
    await msg.delete()
    return 

@client.command(name='ban')
async def ban(self, ctx, member: discord.Member, *, reason=None):
    """
    Bans a member.
    """
    if ctx.author.id != 140951260323905537:
        return
    await member.ban(reason=reason)
    return


@client.command(name='update')
async def update(ctx):
    """
    Pulls from source.
    """

    guild = client.get_guild(GUILD_ID)
    guru = discord.utils.find(lambda r: r.id == GURU, guild.roles)

    if ctx.message.author.guild_permissions.administrator == True or guru in ctx.message.author.roles:
        await ctx.send('Pulling from source...')
        os.system('git pull')
        await asyncio.sleep(5)
        await ctx.send('Restarting...')
        os.system('sudo systemctl restart roaree.service')
        return

@client.command(name='restart')
async def restart(ctx):
    """
    Restarts the bot.
    """

    guild = client.get_guild(GUILD_ID)
    guru = discord.utils.find(lambda r: r.id == GURU, guild.roles)

    if ctx.message.author.guild_permissions.administrator == True or guru in ctx.message.author.roles:
        await ctx.send('Restarting...')
        os.system('sudo systemctl restart roaree.service')
        return
    # else:
    #     guild = client.get_guild(GUILD_ID)
    #     banned = discord.utils.find(lambda r: r.name == 'banned by computerman', guild.roles)
    #     user = discord.utils.find(lambda m: m.id == ctx.message.author.id, guild.members)

    #     await ctx.send('Enter password:')
    #     msg = await client.wait_for('message', check = lambda message: (message.channel == ctx.channel and message.author == ctx.author))
    #     await ctx.send('Incorrect password. Expelling intruders...')
    #     await user.add_roles(banned)
        

@client.command(name='clear')
async def clear(ctx, number: typing.Union[int, str] = 0):
    f"""
    {prefix}clear N checks the N past messages in the channel. If they are the user's, they are deleted. To clear all messages in the channel, type {prefix}clear all.
    """
    def is_requester(msg):
        return msg.author == ctx.author

    async with ctx.typing():
        if isinstance(number, str):
            # If an invalid command
            if number.lower() != 'all':
                # Send a response and then delete command call + response after 5 seconds
                response = await ctx.send(f'Not a valid clear command. Did you mean `{prefix}clear all`?')
                await asyncio.sleep(5)
                await ctx.message.delete()
                await response.delete()
                return

            # Delete all messages sent by invoker in channel
            print(f'clearing all messages from {ctx.author} in channel ({ctx.channel}, {ctx.guild})')
            deleted = await ctx.channel.purge(limit=None, check=is_requester)
            print(f'done clearing all messages from {ctx.author} in channel ({ctx.channel}, {ctx.guild})')

        else:
            print(f'clearing {ctx.author} in channel ({ctx.channel}, {ctx.guild}) times {number}')
            deleted = await ctx.channel.purge(limit=number + 1, check=is_requester)
            print(f'done clearing {ctx.author} in channel ({ctx.channel}, {ctx.guild}) times {number}')

    await ctx.send(f':white_check_mark: deleted {len(deleted)} messages')


# @client.command(name='purge')
# async def purge(ctx):
#     """
#     Clears all messages sent by author in guild

#     :param ctx: Context object
#     """
#     def is_requester(msg):
#         return msg.author == ctx.author

#     deleted = []
#     async with ctx.typing():
#         print(f'clearing all messages from {ctx.author} in guild {ctx.guild}')
#         for channel in ctx.guild.text_channels:
#             deleted.append(await channel.purge(limit=None, check=is_requester))
#         print(f'done clearing all messages from {ctx.author} in guild {ctx.guild}')

#         await ctx.send(f':white_check_mark: deleted {len(deleted)} messages')


# @client.command(name='isstudent')
# async def isstudent(ctx,rcs):
#     """
#     Checks an RCS id or email for studenthood using the directory.
#     """
#     if ctx.message.author.guild_permissions.administrator:
#         # print()
#         studenthood = await directorysearch.check_is_student(rcs.split('@rpi.edu')[0])
#         print(studenthood,rcs)
#         if studenthood[0]:
#             s1 = 'Student'
#         else:
#             s1 = studenthood[1].replace('&amp;','&')
#         message = await ctx.send(rcs + '\'s role is ' + s1 + '.')
#         await asyncio.sleep(10)
#         await message.delete()
#         await ctx.message.delete()
#     else:
#         message = await ctx.send('Permission denied.')
#         await asyncio.sleep(10)
#         await message.delete()
#         await ctx.message.delete()

# @client.command(name='botclear')
# async def botclear(ctx,number):
#     """
#     Clears bot messages. Only for administrative use. Currently broken, do not use.
#     """
#     if ctx.message.author.guild_permissions.administrator:
#         ms1 = await ctx.send('Clearing ' + str(number) + ' of my own messages...')
#         print('clearing ' + str(ms1.author) + ' in channel (' + str(ctx.channel) + ', ' + str(ctx.guild) + ') times ' + str(number))
#         def is_requester(msg):
#             if msg.author == ms1.author:
#                 return True
#             else:
#                 return False
        
#         async with ctx.typing():
#             deleted = await ctx.channel.purge(limit=(number+1),check=is_requester,bulk=True)
        
#         print('done clearing ' + str(ms1.author) + ' in channel (' + str(ctx.channel) + ', ' + str(ctx.guild) + ') times ' + str(number))
#         await ctx.send(r':white_check_mark: deleted ' + str(len(deleted)) + ' messages')
#     else:
#         ctx.send("Permission Denied.")

class NewHelp(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)

@client.command(name='echo')
async def echo(ctx):
    """
    ECHO ECHo ECho Echo echo ...........
    """
    guild = client.get_guild(GUILD_ID)
    guru = discord.utils.find(lambda r: r.id == GURU, guild.roles)

    if ctx.message.author.guild_permissions.administrator or guru in ctx.message.author.roles:
        await ctx.send(str(ctx.message.content)[6:])
        await ctx.message.delete()

@client.command(name='date')
async def date(ctx):
    """
    For testing purposes
    """
    
    guild = client.get_guild(GUILD_ID)
    guru = discord.utils.find(lambda r: r.id == GURU, guild.roles)
    if ctx.message.author.guild_permissions.administrator or guru in ctx.message.author.roles:
        tz = datetime.timezone(offset=datetime.timedelta(hours=-4))
        date = datetime.datetime.now(tz=tz)
        day = date.day
        print(day)
        await ctx.send(str(day))

@client.command(name='aprilfools')
async def aprilfools(ctx, channel, day0=datetime.datetime.now(tz=datetime.timezone(offset=datetime.timedelta(hours=-4))).day):
    """
    Teehee
    """

    memenames = ["NiccoDubs (bad at counting)",
                 "patrick | seas | physics '22",
                 "David",
                 'Eric "Drax"',
                 "Gift",
                 "Jeff | MSCS '22 CompE '16",
                 "lucas | MS BME",
                 "Blappo (2?)",
                 "vengeance",
                 "kekyoin",
                 "Dawson | CC'23",
                 "Raghav | MS CE",
                 "Carl | SEAS'26",
                 "DaDukki",
                 "Dam258",
                 "TheOneLlama",
                 ]
    


    if channel is None:
        channel = ctx
    elif type(channel) == str:
        channel = client.get_channel(int(channel.strip('<#').strip('>')))

    # ch = client.get_channel(channel)
    alertchannel = client.get_channel(ALERT_CHANNEL)
    # tz = datetime.timezone(offset=datetime.timedelta(hours=-4))
    # date = datetime.datetime.now(tz=tz)
    # day0 = date.day
    print("date is " + str(day0))
    tz = datetime.timezone(offset=datetime.timedelta(hours=-4))
    try:
        daycheck = True
        dayseen = False
        while daycheck:

            name = random.choice(memenames)
            await ctx.message.guild.me.edit(nick=name)

            typing = random.random()*10
            nottyping = random.random()*10+5
            async with channel.typing():
                # do expensive stuff here
                await asyncio.sleep(typing)
            await asyncio.sleep(nottyping)

            date = datetime.datetime.now(tz=tz)
            day = date.day
            print("date is " + str(day))
            
            if dayseen:
                if day != day0:
                    daycheck = False
                else:
                    continue
            else:
                if day == day0:
                    dayseen = True
                continue



        await alertchannel.send('April fools has concluded!')
    except Exception as e:
        await alertchannel.send("```" + str(e) + "```")
        await alertchannel.send("```" + str(channel) + "```")
        print(e)
        






# client.add_cog(WelcomeBot(client))
client.help_command = NewHelp()
# client.loop.create_task(update_alerts())
# client.loop.create_task(update_stats())
client.run(TOKEN)

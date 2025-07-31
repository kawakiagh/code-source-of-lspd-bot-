import discord
from discord.ext import commands, tasks
import json
import os
import datetime
import asyncio
from discord.ui import View, Button


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
STATUS_CHANNEL_NAME = "lspd-status"
STATUS_MESSAGE_FILE = "status_message.json"

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# 🔐 Role checker


def has_role(member, role_names):
    # Full access overrides all
    if any(role.name == "Full acces to commands" for role in member.roles):
        return True
    return any(role.name in role_names for role in member.roles)


# 📄 Log actions
async def log_action(guild, title: str, user: discord.Member, details: str):
    log_channel = discord.utils.get(guild.text_channels, name="📄・bot-logs")
    if log_channel:
        embed = discord.Embed(title=title,
                              description=details,
                              color=discord.Color.green())
        embed.set_footer(text=f"Used by {user}",
                         icon_url=user.display_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)


# ⚠️ Log errors
async def log_error(guild, title: str, user: discord.Member,
                    error_details: str):
    log_channel = discord.utils.get(guild.text_channels, name="📄・bot-logs")
    if log_channel:
        embed = discord.Embed(title=f"⚠️ {title}",
                              description=error_details,
                              color=discord.Color.red())
        embed.set_footer(text=f"By {user}", icon_url=user.display_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)


@bot.event
async def on_ready():
    print(f"✅ LSPD Bot is online as {bot.user}")

    for guild in bot.guilds:
        # Check or create Logs-access role
        logs_role = discord.utils.get(guild.roles, name="Logs-access")
        if logs_role is None:
            logs_role = await guild.create_role(
                name="Logs-access", reason="Role for viewing bot logs")
            print(f"Created role 'Logs-access' in guild {guild.name}")

        # Check or create 📄・bot-logs channel
        log_channel = discord.utils.get(guild.text_channels, name="📄・bot-logs")
        if log_channel is None:
            overwrites = {
                guild.default_role:
                discord.PermissionOverwrite(read_messages=False),
                logs_role:
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=False),
                guild.me:
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=True)
            }
            log_channel = await guild.create_text_channel(
                "📄・bot-logs",
                overwrites=overwrites,
                reason="Channel for bot logs")
            print(f"Created channel '📄・bot-logs' in guild {guild.name}")
        else:
            # Update channel permissions in case they differ
            overwrite = log_channel.overwrites_for(guild.default_role)
            if overwrite.read_messages != False:
                await log_channel.set_permissions(guild.default_role,
                                                  read_messages=False)
            overwrite = log_channel.overwrites_for(logs_role)
            if overwrite.read_messages != True or overwrite.send_messages != False:
                await log_channel.set_permissions(logs_role,
                                                  read_messages=True,
                                                  send_messages=False)
            overwrite = log_channel.overwrites_for(guild.me)
            if overwrite.read_messages != True or overwrite.send_messages != True:
                await log_channel.set_permissions(guild.me,
                                                  read_messages=True,
                                                  send_messages=True)


@bot.event
async def on_ready():
    print(f"✅ LSPD Bot is online as {bot.user}")

    for guild in bot.guilds:
        # 📘 Create User manual role
        manual_role = discord.utils.get(guild.roles, name="User manual")
        if manual_role is None:
            manual_role = await guild.create_role(
                name="User manual", reason="Role for reading the bot manual")
            print(f"✅ Created role 'User manual' in guild: {guild.name}")

        # 📘 Create User manual channel
        manual_channel = discord.utils.get(guild.text_channels,
                                           name="📘・user-manual")
        if manual_channel is None:
            overwrites = {
                guild.default_role:
                discord.PermissionOverwrite(view_channel=False),
                manual_role:
                discord.PermissionOverwrite(view_channel=True,
                                            send_messages=False),
                guild.me:
                discord.PermissionOverwrite(view_channel=True,
                                            send_messages=True),
            }
            manual_channel = await guild.create_text_channel(
                "📘・user-manual",
                overwrites=overwrites,
                reason="Bot User Manual")
            print(f"✅ Created channel '📘・user-manual' in guild: {guild.name}")

            # 📝 Send manual in parts
            manual_parts = [
                "**📘 Welcome to the LSPD Bot Manual!**\nThis bot helps manage law enforcement RP commands.",
                "**🔐 Roles & Permissions:**\n- Full acces to commands: All commands\n- Access: Announcement & Broadcast\n- Law Enforcement Officer: BOLO, Status\n- Logs-access: Can view bot logs\n- User manual: Can read this channel",
                "**📢 Commands:**\n`!announce #channel message`\n`!bolo message`\n`!status officer status`\n`!broadcast message`\n`!help`\n`!rollcall`\n`!report`\n`!permissions`",
                "**📄 Logs:**\nAll activity logs are sent to `📄・bot-logs`, only visible to the `Logs-access` role.",
                "**🛠 Admin Notes:**\nThis bot auto-creates channels/roles and sets permissions. Bot needs `Manage Roles`, `Manage Channels`, `Send Messages`, and `Embed Links` permissions.",
                "**❓ Support:**\nContact your server admin or developer for help using the bot."
            ]

            for part in manual_parts:
                await manual_channel.send(part)


# 📢 Announce command with channel targeting
@bot.command(name="announce")
async def announce(ctx,
                   channel: discord.TextChannel = None,
                   *,
                   message: str = None):
    if not has_role(ctx.author, ["Access", "Full acces to commands"]):
        await log_error(ctx.guild, "Permission Denied", ctx.author,
                        "Tried !announce without Access role.")
        return await ctx.send(
            "❌ You don't have permission to use this command.")

    if not channel or not message:
        return await ctx.send("❌ Usage: `!announce #channel <message>`")

    role_id = 1392870773768851614  # Replace with your real tag role ID
    mention = f"<@&{role_id}>"

    embed = discord.Embed(title="📢 LSPD Announcement",
                          description=message,
                          color=discord.Color.blue())
    embed.set_footer(text=f"Announced by {ctx.author}",
                     icon_url=ctx.author.display_avatar.url)
    await channel.send(content=mention, embed=embed)
    await log_action(ctx.guild, "📢 Announcement Sent", ctx.author,
                     f"In {channel.mention}: {message}")
    await ctx.send(f"✅ Announcement sent to {channel.mention}")


# 🚨 BOLO alert
@bot.command(name="bolo")
async def bolo(ctx, *, message: str = None):
    if not has_role(ctx.author,
                    ["Law Enforcement Officer", "Full acces to commands"]):
        await log_error(ctx.guild, "Permission Denied", ctx.author,
                        "Attempted !bolo without proper role.")
        return await ctx.send(
            "❌ You don't have permission to use this command.")
    if not message:
        return await ctx.send("❌ Usage: `!bolo <message>`")

    embed = discord.Embed(title="🚨 BOLO Alert 🚨",
                          description=message,
                          color=discord.Color.red())
    await ctx.send(embed=embed)
    await log_action(ctx.guild, "🚨 BOLO Alert Sent", ctx.author,
                     f"Message: {message}")


#status

# Your known message IDs for the On Duty/Off Duty status messages
STATUS_MESSAGES = {
    123456789012345678: {  # Guild ID 1   Los Santos Police Departement
        "channel_id": 1399749330373443607,  # duty-status channel ID for this guild
        "message_id": 1400384847796506665
    },
    234567890123456789: {  # Guild ID 2   test servers
        "channel_id": 1400384851026382908,
        "message_id": 1400384853136117842
    },
    345678901234567890: {  # Guild ID 3    
        "channel_id": 1272212089196384286,
        "message_id": 1400384831736512623
    }
}

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    await setup_roles_and_channel()

async def setup_roles_and_channel():
    for guild in bot.guilds:
        # Create roles if not exist
        on_duty = discord.utils.get(guild.roles, name="On Duty")
        off_duty = discord.utils.get(guild.roles, name="Off Duty")
        if not on_duty:
            on_duty = await guild.create_role(name="On Duty", colour=discord.Colour.green())
        if not off_duty:
            off_duty = await guild.create_role(name="Off Duty", colour=discord.Colour.red())

        # Create category and channel
        category = discord.utils.get(guild.categories, name="LSPD Bot")
        if not category:
            category = await guild.create_category("LSPD Bot")

        channel = discord.utils.get(guild.text_channels, name="duty-status")
        if not channel:
            channel = await guild.create_text_channel("duty-status", category=category)

        # Send initial status message if not already
        messages = [msg async for msg in channel.history(limit=5)]
        if messages:
            global duty_message_id
            duty_message_id = messages[0].id
        else:
            message = await channel.send(embed=await build_duty_embed(guild))
            duty_message_id = message.id

async def build_duty_embed(guild):
    on_duty_role = discord.utils.get(guild.roles, name="On Duty")
    off_duty_role = discord.utils.get(guild.roles, name="Off Duty")

    on_duty_members = [m.mention for m in on_duty_role.members] if on_duty_role else []
    off_duty_members = [m.mention for m in off_duty_role.members] if off_duty_role else []

    embed = discord.Embed(title="🚨 Duty Status", color=discord.Color.dark_blue())
    embed.add_field(name="🟢 On Duty", value="\n".join(on_duty_members) or "No one", inline=False)
    embed.add_field(name="🔴 Off Duty", value="\n".join(off_duty_members) or "No one", inline=False)
    embed.set_footer(text="Use !onduty or !offduty to update your status.")
    return embed

async def update_duty_message(guild):
    channel = discord.utils.get(guild.text_channels, name="duty-status")
    if channel and duty_message_id:
        try:
            message = await channel.fetch_message(duty_message_id)
            await message.edit(embed=await build_duty_embed(guild))
        except:
            pass

@bot.command()
async def onduty(ctx):
    guild = ctx.guild
    member = ctx.author

    on_duty = discord.utils.get(guild.roles, name="On Duty")
    off_duty = discord.utils.get(guild.roles, name="Off Duty")

    await member.add_roles(on_duty)
    await member.remove_roles(off_duty)
    await ctx.send(f"✅ {member.mention} is now **On Duty**.")

    await update_duty_message(guild)

@bot.command()
async def offduty(ctx):
    guild = ctx.guild
    member = ctx.author

    on_duty = discord.utils.get(guild.roles, name="On Duty")
    off_duty = discord.utils.get(guild.roles, name="Off Duty")

    await member.add_roles(off_duty)
    await member.remove_roles(on_duty)
    await ctx.send(f"🛑 {member.mention} is now **Off Duty**.")

    await update_duty_message(guild)

# 📢 Broadcast
@bot.command(name="broadcast")
async def broadcast(ctx, *, message: str = None):
    if not has_role(ctx.author, ["Access", "Full acces to commands"]):
        await log_error(ctx.guild, "Permission Denied", ctx.author,
                        "Tried !broadcast without Access role.")
        return await ctx.send(
            "❌ You don't have permission to use this command.")

    if not message:
        return await ctx.send("❌ Usage: `!broadcast <message>`")

    embed = discord.Embed(title="📢 LSPD Broadcast",
                          description=message,
                          color=discord.Color.gold())
    await ctx.send(embed=embed)
    await log_action(ctx.guild, "📢 Broadcast Sent", ctx.author, message)

#ticket system and history

class TicketButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Declaration", style=discord.ButtonStyle.primary, custom_id="ticket_declaration"))
        self.add_item(Button(label="Application", style=discord.ButtonStyle.success, custom_id="ticket_application"))

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.command()
async def opentickets(ctx):
    embed = discord.Embed(
        title="Open a Ticket",
        description="Choose the type of ticket you want to open:",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed, view=TicketButtonView())

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    user = interaction.user
    guild = interaction.guild
    custom_id = interaction.data["custom_id"]

    if custom_id.startswith("ticket_"):
        ticket_type = custom_id.split("_")[1]
        category_name = "📢 Declarations" if ticket_type == "declaration" else "📝 Applications"
        channel_name = f"{ticket_type}-{user.name}".replace(" ", "-").lower()
        history_channel_name = f"📜-{ticket_type}-history"

        # Check/create category
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(name=category_name)

        # Check if ticket already exists
        existing = discord.utils.get(category.text_channels, name=channel_name)
        if existing:
            await interaction.response.send_message(
                f"{user.mention}, you already have an open **{ticket_type}** ticket: {existing.mention}",
                ephemeral=True
            )
            return

        # Set permissions and create ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)

        # Send message depending on type
        if ticket_type == "application":
            application_embed = discord.Embed(
                title="📝 Application Form",
                description=(
                    f"{user.mention}, please answer the following questions:\n\n"
                    "**First Name:**\n"
                    "**Last Name:**\n"
                    "**Age:**\n"
                    "**Region:**\n"
                    "**Gender:**\n"
                    "**Languages:**\n"
                    "**Phone Number:**\n"
                    "**Adresse:**\n"
                    "**Experiences / Diplomas:**"
                ),
                color=discord.Color.blue()
            )
            await ticket_channel.send(embed=application_embed)
        else:
            await ticket_channel.send(f"{user.mention}, please describe your **{ticket_type}** in detail.")

        # Create or get history channel
        history_channel = discord.utils.get(guild.text_channels, name=history_channel_name)
        if not history_channel:
            history_channel = await guild.create_text_channel(history_channel_name)

        # Log to history
        log_embed = discord.Embed(
            title=f"📩 New {ticket_type.capitalize()} Ticket",
            description=f"**User:** {user.mention}\n**Channel:** {ticket_channel.mention}",
            color=discord.Color.green()
        )
        await history_channel.send(embed=log_embed)

        await interaction.response.send_message(
            f"✅ Your **{ticket_type}** ticket has been created: {ticket_channel.mention}",
            ephemeral=True
        )



# Rules
@bot.command(name="rules")
async def rules(ctx):
    if not has_role(ctx.author,
                    ["Law Enforcement Officer", "Full acces to commands"]):
        return await ctx.send(
            "❌ You don't have permission to use this command.")
    rules_text = """
**1. Recruitment & Training**
- Mandatory Application
- Initial RP Training
- Probation Period

**2. Behavior & Uniform**
- Respect Chain of Command
- Wear Regulation Uniform
- Show Exemplary Conduct

**3. Use of Weapons & Equipment**
- Proportional Use Only
- Always Give Warnings
- Follow Equipment Rules

**4. Intervention Procedures**
- Obey Traffic Laws
- Use Radio Communication
- Justify All Arrests

**5. Use of Force**
- Escalate Slowly (Talk > Taser > Weapon)
- No “Cop Baiting”

**6. Special Interventions**
- Call Reinforcements
- Prioritize Negotiation
- Avoid Public Shootouts

**7. Relations with Civilians**
- Show Respect
- Offer Help

**8. Corruption & Abuse**
- Zero Tolerance
- Report Misconduct

**9. OOC & Confidentiality**
- No Metagaming
- Keep Info Confidential

**10. Sanctions**
- Warnings to Bans
- Regular Checks
"""
    embed = discord.Embed(title="📘 LSPD Rules",
                          description=rules_text,
                          color=discord.Color.blue())
    await ctx.send(embed=embed)

    try:
        await ctx.author.send(
            "👮‍♂️ **Daily Report Form**\nPlease answer the following questions:"
        )

        questions = [
            "1️⃣ What is your **Name and Badge Number**?",
            "2️⃣ What is your **Unit Assignment**?",
            "3️⃣ What was your **Shift Time** (e.g., 21h - 01h)?",
            "4️⃣ What was your **Attendance Status** (Present / Absent / Late)?",
            "5️⃣ Any **Additional Comments**?"
        ]

        answers = []

        for question in questions:
            await ctx.author.send(question)
            msg = await bot.wait_for("message", check=check, timeout=300.0)
            answers.append(msg.content)

        # Updated report channel name
        report_channel = discord.utils.get(ctx.guild.text_channels,
                                           name="📂・ᴅᴀɪʟʏ-ʀᴇᴘᴏʀᴛs")
        if not report_channel:
            return await ctx.author.send(
                "❌ Couldn't find the `📂・ᴅᴀɪʟʏ-ʀᴇᴘᴏʀᴛs` channel.")

        embed = discord.Embed(title="📋 Roll Call Report",
                              color=discord.Color.blue())
        embed.add_field(name="👤 Name / Badge", value=answers[0], inline=False)
        embed.add_field(name="🚔 Unit", value=answers[1], inline=False)
        embed.add_field(name="🕘 Shift Time", value=answers[2], inline=False)
        embed.add_field(name="✅ Attendance", value=answers[3], inline=False)
        embed.add_field(name="📝 Comments", value=answers[4], inline=False)
        embed.set_footer(text=f"Submitted by {ctx.author}",
                         icon_url=ctx.author.display_avatar.url)

        await report_channel.send(embed=embed)
        await ctx.author.send("✅ Your Daily report has been submitted.")

    except discord.Forbidden:
        await ctx.send("❌ I couldn't DM you. Please enable DMs and try again.")
    except asyncio.TimeoutError:
        await ctx.author.send(
            "⌛ Time's up. Please try the `!report` command again when you're ready."
        )

    await ctx.send(embed=embed)


# Permissions List (open to everyone)
@bot.command(name="permissions")
async def permissions(ctx):
    embed = discord.Embed(title="🔐 Command Permissions",
                          color=discord.Color.blue())
    embed.add_field(name="Access Role",
                    value="!announce, !broadcast",
                    inline=False)
    embed.add_field(name="Law Enforcement Officer Role",
                    value="!bolo, !status, !rules, !report",
                    inline=False)
    embed.add_field(name="Everyone", value="!help, !permissions", inline=False)
    await ctx.send(embed=embed)


# Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing arguments.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"⏳ Slow down! Try again in {error.retry_after:.2f} seconds.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Unknown command. Try `!help`.")
    else:
        print(f"Unhandled error: {error}")


@bot.command(name="rollcall")
async def rollcall(ctx,
                   channel: discord.TextChannel = None,
                   *,
                   category_name=None):
    if not has_role(ctx.author, ["Law Enforcement Officer"]):
        return await ctx.send(
            "❌ You don't have permission to use this command.")

    if channel is None or category_name is None:
        return await ctx.send("❗ Usage: `!rollcall #channel CategoryName`")

    role = discord.utils.get(ctx.guild.roles, name="Law Enforcement Officer")
    if not role:
        return await ctx.send("❌ 'Law Enforcement Officer' role not found.")

    embed = discord.Embed(
        title="🕙 Night Shift Watch",
        description=(f"**Roll call start at 21h**\n\n"
                     f"✅ **You will be present to the roll call**\n"
                     f"❌ **You won’t be present to the roll call**\n"
                     f"🕓 **You will be present later**\n\n"
                     f"📁 **Category:** {category_name}"),
        color=discord.Color.orange())
    embed.set_image(
        url=
        "https://i.pinimg.com/1200x/09/6d/cb/096dcb8a7ea0e6dd274756088b09bd03.jpg"
    )
    embed.set_footer(text="React below to indicate your status.")

    message = await channel.send(f"{role.mention}", embed=embed)

    for emoji in ["✅", "❌", "🕓"]:
        await message.add_reaction(emoji)


#Assigments
@bot.command(name="assignment")
async def assignment(ctx,
                     channel: discord.TextChannel = None,
                     *,
                     message: str = None):
    if not has_role(ctx.author, [
            "Access", "LEO |  Watch Commander", "Full acces to commands"
    ]):  # Customize roles as needed
        return await ctx.send(
            "❌ You don't have permission to use this command.")

    if not channel or not message:
        return await ctx.send(
            "❌ Usage: `!assignment #channel <assignment details>`")

    embed = discord.Embed(title="📝 Assignments",
                          description=message,
                          color=discord.Color.orange())
    embed.set_footer(text=f"Posted by {ctx.author}",
                     icon_url=ctx.author.display_avatar.url)

    # Optional: mention a role (e.g., Officers) or @everyone
    mention = "@Law Enforcement Officer"  # Or f"<@&{ROLE_ID}>" if you want a specific role tag
    await channel.send(content=mention, embed=embed)
    await ctx.send(f"✅ Assignment posted in {channel.mention}")


@bot.command(name="report")
async def report(ctx):

    def check(m):
        return m.author == ctx.author and isinstance(m.channel,
                                                     discord.DMChannel)

    try:
        await ctx.author.send(
            "👮‍♂️ **Roll Call Report Form**\nPlease answer the following questions:"
        )

        questions = [
            "1️⃣ What is your **Name and Badge Number**?",
            "2️⃣ What is your **Unit Assignment**?",
            "3️⃣ What was your **Shift Time** (e.g., 21h - 01h)?",
            "4️⃣ What was your **Attendance Status** (Present / Absent / Late)?",
            "5️⃣ Any **Additional Comments**?"
        ]

        answers = []

        for question in questions:
            await ctx.author.send(question)
            msg = await bot.wait_for("message", check=check, timeout=300.0)
            answers.append(msg.content)

        # Updated report channel name
        report_channel = discord.utils.get(ctx.guild.text_channels,
                                           name="📂・ᴅᴀɪʟʏ-ʀᴇᴘᴏʀᴛs")
        if not report_channel:
            return await ctx.author.send(
                "❌ Couldn't find the `📂・ᴅᴀɪʟʏ-ʀᴇᴘᴏʀᴛs` channel.")

        embed = discord.Embed(title="📋 Roll Call Report",
                              color=discord.Color.blue())
        embed.add_field(name="👤 Name / Badge", value=answers[0], inline=False)
        embed.add_field(name="🚔 Unit", value=answers[1], inline=False)
        embed.add_field(name="🕘 Shift Time", value=answers[2], inline=False)
        embed.add_field(name="✅ Attendance", value=answers[3], inline=False)
        embed.add_field(name="📝 Comments", value=answers[4], inline=False)
        embed.set_footer(text=f"Submitted by {ctx.author}",
                         icon_url=ctx.author.display_avatar.url)

        await report_channel.send(embed=embed)
        await ctx.author.send("✅ Your roll call report has been submitted.")

    except discord.Forbidden:
        await ctx.send("❌ I couldn't DM you. Please enable DMs and try again.")
    except asyncio.TimeoutError:
        await ctx.author.send(
            "⌛ Time's up. Please try the `!report` command again when you're ready."
        )

        #rollcall
        @bot.command(name="rollcall")
        async def rollcall(ctx,
                           channel: discord.TextChannel = None,
                           *,
                           category_name: str = None):
            allowed_roles = [
                "Law Enforcement Officer", "Full acces to commands"
            ]
            if not any(role.name in allowed_roles
                       for role in ctx.author.roles):
                return await ctx.send(
                    "❌ You don't have permission to use this command.")

            if channel is None or category_name is None:
                return await ctx.send(
                    "❗ Usage: `!rollcall #channel CategoryName`")

            role = discord.utils.get(ctx.guild.roles,
                                     name="Law Enforcement Officer")
            if not role:
                return await ctx.send(
                    "❌ 'Law Enforcement Officer' role not found.")

            embed = discord.Embed(
                title="🕙 Night Shift Watch",
                description=("**Roll call start at 21h**\n\n"
                             "✅ **You will be present to the roll call**\n"
                             "❌ **You won’t be present to the roll call**\n"
                             "🕓 **You will be present later**\n\n"
                             f"📁 **Category:** {category_name}"),
                color=discord.Color.orange())
            embed.set_image(
                url=
                "https://i.pinimg.com/1200x/09/6d/cb/096dcb8a7ea0e6dd274756088b09bd03.jpg"
            )
            embed.set_footer(text="React below to indicate your status.")

            message = await channel.send(f"{role.mention}", embed=embed)

            for emoji in ["✅", "❌", "🕓"]:
                await message.add_reaction(emoji)

#discipline
@bot.command(name="discipline")
@commands.has_role("High Command")
async def discipline(ctx, member: discord.Member, *, reason: str):
    log_channel = discord.utils.get(ctx.guild.text_channels, name="📂・internal-affairs")
    embed = discord.Embed(title="📌 Disciplinary Action", color=discord.Color.dark_red())
    embed.add_field(name="Officer", value=member.mention)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text=f"Filed by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await log_channel.send(embed=embed)


# 📘 Help
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="👮‍♂️ LSPD Bot Commands",
                          color=discord.Color.blue())
    embed.add_field(name="!announce #channel <message>",
                    value="Send announcement (Access)",
                    inline=False)
    embed.add_field(name="!bolo <message>",
                    value="Create BOLO alert (LEO)",
                    inline=False)
    embed.add_field(name="!status <officer> <status>",
                    value="Update unit status (LEO)",
                    inline=False)
    embed.add_field(name="!broadcast <message>",
                    value="Send broadcast (Access)",
                    inline=False)
    embed.add_field(name="!rules",
                    value="(Law Enforcement Officer role)",
                    inline=False)
    embed.add_field(name="!report <text>",
                    value="(Law Enforcement Officer role)",
                    inline=False)
    embed.add_field(name="!permissions",
                    value="See who can use which commands",
                    inline=False)
    embed.add_field(name="rollcall", value="send roll call message ")
    embed.add_field(name="!discipline <member> <reason>" , 
                    value="Send disciplinary action (High Command)", 
                    inline= False)
    embed.add_field(name="!help", 
                    value="Show this menu", 
                    inline=False)
    await ctx.send(embed=embed)
    await log_action(ctx.guild, "📘 Help Viewed", ctx.author, "Used !help")



# ✅ Run bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not set!")
    else:
        bot.run(token)

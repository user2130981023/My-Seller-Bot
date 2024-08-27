import discord
from discord.ext import commands
import aiohttp
import random
import string
import asyncio

# keyauth seller key found in your dashboard settings for your application of choice
sellerkey = ""
# discord bot token
token = ""  

icon_url = "https://cdn.discordapp.com/icons/1270572817951490048/a_1068e4d76fb5cf380faa8938521fe377.gif?size=512&width=0&height=0"
embed_footer_text = "Footer text you want to be sent"

def generate_unique_id(length=25):
    return ''.join(random.choices(string.digits, k=length))

cache = {}

async def fetch_data(url, headers=None):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                response.raise_for_status()

                if response.headers.get('Content-Type') == 'application/json':
                    return await response.json()
                else:
                    print(f"Unexpected content type: {response.headers.get('Content-Type')}")
                    return None
        except aiohttp.ClientError as e:
            print(f"Network error: {e}")
            return None

bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())
ALLOWED_SERVERS = [123123123, 123123123, 123123123] 

@bot.event
async def on_guild_join(guild):
    if guild.id not in ALLOWED_SERVERS:
        await guild.leave()
        print(f"Left server: {guild.name}")

@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")

    for guild_id in ALLOWED_SERVERS:
        guild = bot.get_guild(guild_id)
        if guild:
            await clear_duplicate_commands(guild)
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"Commands synced to guild: {guild.name} (ID: {guild.id})")

async def clear_duplicate_commands(guild):
    if not guild:
        return

    try:
        existing_commands = await bot.tree.fetch_commands(guild=guild)
        command_names = set()
        duplicates = []

        for command in existing_commands:
            if command.name in command_names:
                duplicates.append(command)
            else:
                command_names.add(command.name)

        for command in duplicates:
            await bot.tree.delete_command(command.id, guild=guild)
            print(f"Removed duplicate command: {command.name} (ID: {command.id})")

    except Exception as e:
        print(f"Failed to clear duplicate commands: {e}")

# Copy the role ID you want to be allowed to do certain commands ex: admins should be able to gen keys so enter there role id: 90123618231 
you can have multiple id's just seperate with a comma
AUTHORIZED_ROLES = {
    'deletelicense': [],  
    'banlicense': [],  
    'genkey': [],  
    'resethwid': []  
}

async def has_required_role(interaction: discord.Interaction, command_name: str) -> bool:
    required_roles = AUTHORIZED_ROLES.get(command_name, [])
    if not required_roles:
        return True
    user_role_ids = [role.id for role in interaction.user.roles]
    return any(role_id in user_role_ids for role_id in required_roles)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.tree.command(name="authstatus", description="Check KeyAuth authentication status")
async def authstatus(interaction: discord.Interaction):
    data = await fetch_data("https://keyauth.win/")
    status_code = data.get('status_code', 'unknown') if data else 'error'
    embed = discord.Embed(title="KeyAuth authentication Status", description=f"KeyAuth authentication website status: **{status_code}**", color=0x3498db)
    embed.set_footer(text=embed_footer_text, icon_url=icon_url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="deletelicense", description="Delete a license key")
async def deletelicense(interaction: discord.Interaction, key: str):
    if not await has_required_role(interaction, 'deletelicense'):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    data = await fetch_data(f"https://keyauth.win/api/seller/?sellerkey={sellerkey}&type=del&key={key}")
    if data and data.get("success"):
        embed = discord.Embed(title="Deleted License", description=f"Successfully deleted license key: {key}", color=0x3498db)
        embed.set_footer(text=embed_footer_text, icon_url=icon_url)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Failed to delete License", description=f"Failed to delete license key: {key}", color=0xe74c3c)
        embed.set_footer(text=embed_footer_text, icon_url=icon_url)
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="banlicense", description="Ban a license key with a reason")
async def banlicense(interaction: discord.Interaction, key: str, reason: str):
    if not await has_required_role(interaction, 'banlicense'):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    data = await fetch_data(f"https://keyauth.win/api/seller/?sellerkey={sellerkey}&type=ban&key={key}&reason={reason}")
    if data and data.get("success"):
        embed = discord.Embed(title="Banned License", description=f"Successfully banned license key: {key}", color=0x3498db)
        embed.set_footer(text=embed_footer_text, icon_url=icon_url)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Failed to Ban License", description=f"Failed to ban license key: {key}", color=0xe74c3c)
        embed.set_footer(text=embed_footer_text, icon_url=icon_url)
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="genkey", description="Generate a HWID license key")
async def genkey(interaction: discord.Interaction, day: int):
    if not await has_required_role(interaction, 'genkey'):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    license = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(40))
    data = await fetch_data(f"https://keyauth.win/api/seller/?sellerkey={sellerkey}&type=add&format=json&expiry={day}&mask={license}&level=1&amount=1&owner=InsidiousBot")
    if data and data.get("success"):
        key = data.get("key")
        await interaction.response.send_message(f"Successfully generated License key!\nLicense key: ```{key}```")

@bot.tree.command(name="resethwid", description="Reset HWID for a user")
async def resethwid(interaction: discord.Interaction, user: str):
    if not await has_required_role(interaction, 'resethwid'):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    data = await fetch_data(f"https://keyauth.win/api/seller/?sellerkey={sellerkey}&type=resetuser&user={user}")
    if data and data.get("success"):
        embed = discord.Embed(title="Reset your HWID", description=f":white_check_mark: Successfully resetted HWID for {user}", color=0x3498db)
        embed.set_footer(text=embed_footer_text, icon_url=icon_url)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Failed to reset HWID", description=f":anger: Failed to reset HWID for {user}", color=0xe74c3c)
        embed.set_footer(text=embed_footer_text, icon_url=icon_url)
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="purge", description="Clear all messages in the channel and clone it")
async def purge(interaction: discord.Interaction):
    if not await has_required_role(interaction, 'purge'):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    channel = interaction.channel
    category = channel.category
    position = channel.position
    user = interaction.user

    new_channel = await channel.guild.create_text_channel(
        name=channel.name,
        category=category,
        position=position,
        reason=f"Channel cloned by {user}"
    )

    for overwrite in channel.overwrites:
        await new_channel.set_permissions(overwrite.target, overwrite)

    async for message in channel.history(limit=100):
        await new_channel.send(message.content)

    await channel.delete(reason=f"Deleted by {user}")

    await interaction.response.send_message(f"Channel purged and cloned successfully.", ephemeral=True)

@bot.tree.command(name="guide", description="Step-by-step guide for users")
async def guide(interaction: discord.Interaction):
    required_role_id = 1270583455142510694

    if any(role.id == required_role_id for role in interaction.user.roles):
        steps = (

            "1. Disable any antivirus. If you need help, download this: [Help Link](https://www.sordum.org/downloads/?st-defender-control) password: `sordum`.",
            "2. Follow this [Guide](guide link here)",

            "Any questions make a support ticket!"

        )

        embed = discord.Embed(
            title="User Guide",
            description="Step-by-step guide to help you navigate through our services.",
            color=0x3498db
        )

        for step in steps:
            embed.add_field(name=f"Step {steps.index(step) + 1}", value=step, inline=False)

        embed.set_footer(text=embed_footer_text, icon_url=icon_url)

        try:
            dm_channel = await interaction.user.create_dm()
            await dm_channel.send(embed=embed)
            await interaction.response.send_message("The guide has been sent to your DMs.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I couldn't send you a DM. Please check your privacy settings.", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

@bot.tree.command(name="download-aio", description="Send download link for AIO loader")
async def download_aio(interaction: discord.Interaction):
    unique_id = generate_unique_id()
    async def send_dm():
        try:
            dm_channel = await interaction.user.create_dm()

            embed = discord.Embed(
                title="Here is the cheat loader",
                description=f"[Download AIO Loader](download link)",
                color=0x3498db
            )
            embed.set_footer(text=embed_footer_text, icon_url=icon_url)
            await dm_channel.send(embed=embed)
            await interaction.response.send_message(f"Sent the download link to your DM.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I couldn't send you a DM. Please check your privacy settings.", ephemeral=True)

    await send_dm()

bot.run(token)
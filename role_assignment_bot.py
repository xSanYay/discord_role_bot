# Meant for personal usage and automation and not commercial purposes.
# Discord can take action against auto role assign bots based on invites to prevent invite spamming.
# Please use this sensibly. 
# Working as of August 2024.

import discord
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file (contains the TOKEN)
load_dotenv()

# Set the intents for the bot, enabling member-related events such as on_member_join
intents = discord.Intents.default()
intents.members = True  # We need this for tracking member joins and roles

# Initialize the client with intents
client = discord.Client(intents=intents)

# Get the bot token from the environment variables
token = os.getenv('TOKEN')

# Dictionary to store user invites for tracking between member joins
user_invites = {}

# Function to grant the bot's role the Administrator permission
async def grant_admin_permission(guild):
    # Get the bot's member instance for the guild
    bot_member = guild.me
    
    # Find the bot's highest role in the server
    bot_role = discord.utils.get(guild.roles, name=bot_member.top_role.name)
    
    # Check if the bot has permission to manage roles
    if guild.me.guild_permissions.manage_roles and bot_role:
        # Set administrator permissions for the bot's role
        permissions = bot_role.permissions
        permissions.administrator = True
        # Edit the bot role to apply the changes
        await bot_role.edit(permissions=permissions)
    else:
        print("Bot does not have permission to manage roles.")

# Event triggered when the bot has successfully logged in
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

# Event triggered when a message is sent in a channel
@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself to prevent loops
    if message.author == client.user:
        return
    
    # Command to grant the bot administrator permission
    if message.content.startswith("$grant_permission"):
        await grant_admin_permission(message.guild)
        await message.channel.send("Administrator permission granted.")
    
    # Command to check how many invites the user has and assign roles based on it
    if message.content.startswith("$check_invites"):
        user = message.author  # Get the user who sent the message
        guild = message.guild  # Get the guild (server) where the message was sent

        # Get all invites for the guild
        invites = await guild.invites()

        # Find the invite created by the user who sent the command
        user_invite = None
        for invite in invites:
            if invite.inviter == user:  # If the invite's creator is the user
                user_invite = invite
                break

        # If the user has an invite link
        if user_invite:
            # Start creating the response message with the invite count
            response = f"{user.name} has {user_invite.uses} invite(s).\n"

            # Check if the user has the 'average' role (for users with at least one invite)
            role_average = discord.utils.get(guild.roles, name="average")
            if role_average and role_average in user.roles:
                response += f"{user.name} has the 'average' role! \n"

            # Check if the user has the 'Veteran' role (for high invite counts or trusted users)
            role_veteran = discord.utils.get(guild.roles, name="veteran")
            if role_veteran and role_veteran in user.roles:
                response += f"{user.name} has the 'Veteran' role! \n"

            # Check if the user has less than 5 invites and doesn't already have the 'newbie' role
            role_newbie = discord.utils.get(guild.roles, name="newbie")
            if user_invite.uses < 5:  # User has less than 5 invites
                if role_newbie and role_newbie not in user.roles:
                    # Assign the 'newbie' role if not already assigned
                    await user.add_roles(role_newbie)
                    response += f"{user.name} has been assigned the 'newbie' role! \n"

            # Send the constructed response to the channel
            await message.channel.send(response)
        else:
            # If the user has no invites, send a message to inform them
            await message.channel.send(f"{user.name} has no invites.")

# Event triggered when a new member joins the guild
@client.event
async def on_member_join(member):
    # Fetch all invites after the new member joined
    invites_after_join = await member.guild.invites()

    # Get the stored invites (before the member joined) to compare
    stored_invites = user_invites.get(member.id, [])
    
    # Compare the new invites with the stored ones to detect which invite was used
    for invite in invites_after_join:
        for stored_invite in stored_invites:
            # If the invite ID matches and the uses have increased, the invite was used
            if invite.id == stored_invite.id and invite.uses > stored_invite.uses:
                print(f"{member.name} joined using invite from {invite.inviter.name}")
                break

    # Store the updated invites for future use
    user_invites[member.id] = invites_after_join

# Run the bot with the token
client.run(token)

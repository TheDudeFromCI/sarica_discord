import os
import discord
from discord import app_commands
from .sql import Database
from .feed import query_rr


class SaricaBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)

        self.guild = discord.Object(id=os.getenv("GUILD_ID"))
        self.tree = app_commands.CommandTree(self)

        self.announcements_channel_id = int(os.getenv("ANNOUNCEMENTS_CHANNEL_ID"))

        self.new_members_channel_id = int(os.getenv("NEW_MEMBERS_CHANNEL_ID"))
        self.wave_sticker_id = int(os.getenv("WAVE_STICKER_ID"))

        self.role_message_id = int(os.getenv("ROLE_MESSAGE_ID"))
        self.tsqs_updates_role_id = int(os.getenv("TSQS_UPDATES_ROLE_ID"))
        self.role_mapping = {discord.PartialEmoji(name="🪰"): self.tsqs_updates_role_id}

        self.db = Database()

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        await self.check_for_rr_update()

    async def on_member_join(self, member: discord.Member):
        print(f"{member.name} has joined the server")

        guild = member.guild
        if guild is None:
            return

        channel = guild.get_channel(self.new_members_channel_id)
        if channel is None:
            print("Warning: New members channel not found")
            return

        await channel.send(f"Welcome to the Wraithaven server, {member.mention}!")

        sticker = await guild.fetch_sticker(self.wave_sticker_id)
        if sticker is None:
            return

        await channel.send(stickers=[sticker])

    async def setup_hook(self):
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            print("Warning: Guild not found")
            return

        try:
            role_id = self.role_mapping[payload.emoji]
        except KeyError:
            print(f"Unknown emoji: {payload.emoji}")
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        print(f"Adding role {role.name} to {payload.member.name}")
        await payload.member.add_roles(role)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            print("Warning: Guild not found")
            return

        try:
            role_id = self.role_mapping[payload.emoji]
        except KeyError:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        print(f"Removing role {role.name} from {member.name}")
        await member.remove_roles(role)

    async def check_for_rr_update(self):
        chapter = query_rr(self.db)
        if chapter is None:
            return

        print(f"New chapter posted: {chapter.name}")

        guild = self.get_guild(self.guild.id)
        if guild is None:
            print("Warning: Guild not found")
            return

        channel = guild.get_channel(self.announcements_channel_id)
        if channel is None:
            print("Warning: Announcements channel not found")
            return

        updates_role = guild.get_role(self.tsqs_updates_role_id)
        if updates_role is None:
            print("Warning: TSQS Updates role not found")
            return

        await channel.send(
            f"""{updates_role.mention} Chapter {chapter.index} is up: *{chapter.name}*
            [Royal Road]({chapter.link})
            [Scribble Hub](https://www.scribblehub.com/series/1421176/the-spoken-queens-swarm/)"""
        )


def run():
    client = SaricaBot()
    client.run(os.getenv("DISCORD_TOKEN"))

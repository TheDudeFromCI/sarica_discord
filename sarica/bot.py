import os
import sys
import discord
import asyncio
from datetime import datetime, timedelta
from discord import app_commands
from .sql import Database
from .feed import query_rr
from .table import make_table
from .essence import UserClass
from typing import Optional


class SaricaBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)

        self.guild = discord.Object(id=os.getenv("GUILD_ID"))
        self.tree = app_commands.CommandTree(self)

        self.announcements_channel_id = int(os.getenv("ANNOUNCEMENTS_CHANNEL_ID"))
        self.bot_spam_channel_id = int(os.getenv("BOT_SPAM_CHANNEL_ID"))

        self.new_members_channel_id = int(os.getenv("NEW_MEMBERS_CHANNEL_ID"))
        self.memes_channel_id = int(os.getenv("MEMES_CHANNEL_ID"))
        self.cute_pics_channel_id = int(os.getenv("CUTE_PICS_CHANNEL_ID"))
        self.nsfw_channel_id = int(os.getenv("NSFW_CHANNEL_ID"))
        self.tsqs_channel_id = int(os.getenv("TSQS_CHANNEL_ID"))
        self.tsqs_spoiler_channel_id = int(os.getenv("TSQS_SPOILER_CHANNEL_ID"))
        self.suggestions_channel_id = int(os.getenv("SUGGESTIONS_CHANNEL_ID"))
        self.theorycrafting_channel_id = int(os.getenv("THEORYCRAFTING_CHANNEL_ID"))
        self.q_and_a_channel_id = int(os.getenv("Q_AND_A_CHANNEL_ID"))
        self.server_discussion_channel_id = int(
            os.getenv("SERVER_DISCUSSION_CHANNEL_ID")
        )
        self.cool_stuff_channel_id = int(os.getenv("COOL_STUFF_CHANNEL_ID"))
        self.show_off_channel_id = int(os.getenv("SHOW_OFF_CHANNEL_ID"))
        self.intro_channel_id = int(os.getenv("INTRODUCTIONS_CHANNEL_ID"))
        self.fan_art_channel_id = int(os.getenv("FAN_ART_CHANNEL_ID"))
        self.fan_games_channel_id = int(os.getenv("FAN_GAMES_CHANNEL_ID"))
        self.fan_books_channel_id = int(os.getenv("FAN_BOOKS_CHANNEL_ID"))
        self.book_discussion_channel_id = int(os.getenv("BOOK_DISCUSSION_CHANNEL_ID"))

        self.wave_sticker_id = int(os.getenv("WAVE_STICKER_ID"))

        self.role_message_id = int(os.getenv("ROLE_MESSAGE_ID"))
        self.tsqs_updates_role_id = int(os.getenv("TSQS_UPDATES_ROLE_ID"))
        self.role_mapping = {discord.PartialEmoji(name="🪰"): self.tsqs_updates_role_id}

        self.db = Database()

    async def on_ready(self):
        print(f"Logged in as {self.user}")

        version = os.getenv("SARICA_VERSION_HASH")
        await self.bot_spam(f"I'm back online!\n(Version: {version})")

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
        @self.tree.command()
        @app_commands.describe(
            public="If true, this command will be visible to everyone.",
            member="The member to view the Essence of. If not provided, defaults to the user who invoked the command.",
        )
        async def essence(
            interaction: discord.Interaction,
            public: bool = False,
            member: Optional[discord.Member] = None,
        ):
            await self.essence_cmd(interaction, public, member)

        @self.tree.command()
        @app_commands.describe(
            member="The member to add Essence to.",
            points="The amount of Essence to add.",
            user_class="The class to add Essence to.",
        )
        async def add_essence(
            interaction: discord.Interaction,
            member: discord.Member,
            points: int,
            user_class: UserClass,
        ):
            await self.add_essence_cmd(interaction, member, points, user_class)

        @self.tree.command()
        @app_commands.describe(
            no_start="If true, the bot will not restart after reloading.",
        )
        async def reload(interaction: discord.Interaction, no_start: bool = False):
            await self.reload_cmd(interaction, no_start)

        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)

        self.update_checker = self.loop.create_task(self.check_for_rr_updates_slow())

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            print("Warning: Guild not found")
            return

        essence = self.db.get_essence(payload.member.id)
        points = 1
        print(f"{payload.member.name} reacted to a message. Adding {points} exp.")
        essence.add_points(UserClass.Reactionary, points)
        self.db.set_essence(payload.member.id, essence)

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
            f"""{updates_role.mention}
**Woo!** New chapter! *Ah, yeah!* 🎉🎉🎉
Chapter {chapter.index} is up: *{chapter.name}*
[Royal Road]({chapter.link})
[Scribble Hub](https://www.scribblehub.com/series/1421176/the-spoken-queens-swarm/)"""
        )

    async def check_for_rr_updates_slow(self):
        await self.wait_until_ready()

        print("Checking for RR updates every 10 minutes")
        while not self.is_closed():
            await self.check_for_rr_update()

            now = datetime.now() - timedelta(minutes=1)
            seconds = (now.minute % 10) * 60 + now.second
            to_wait = 600 - seconds
            await asyncio.sleep(to_wait)

    async def bot_spam(self, message):
        guild = self.get_guild(self.guild.id)
        if guild is None:
            print("Warning: Guild not found")
            return

        channel = guild.get_channel(self.bot_spam_channel_id)
        if channel is None:
            print("Warning: Bot spam channel not found")
            return

        await channel.send(message)

    async def add_essence_cmd(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        points: int,
        user_class: UserClass,
    ):
        if not interaction.permissions.administrator:
            await interaction.response.send_message(
                "Sorry, {interaction.user.name}, I can't do that. You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        essence = self.db.get_essence(member.id)
        print(f"{member.name} gained {points} {user_class.get_name()} exp.")
        essence.add_points(user_class, points)
        self.db.set_essence(member.id, essence)

        await interaction.response.send_message(
            f"{member.name} gained {points} exp in {user_class.get_name()}.",
            ephemeral=True,
        )

    async def essence_cmd(
        self,
        interaction: discord.Interaction,
        public: bool,
        member: Optional[discord.Member],
    ):
        if member is None:
            member = interaction.user

        essence = self.db.get_essence(member.id)
        level = f"{str(essence.get_level())} ({essence.get_exp_percent_str()})"
        realm = essence.get_realm()
        stage = essence.get_stage()
        path = essence.get_path().name

        if realm.has_progress():
            progress = essence.get_realm_progress().name
            realm = f"{realm.name} Realm ({progress})"
        else:
            realm = realm.name

        if stage.has_steps():
            suffix = ["st", "nd", "rd", "th"]
            step = essence.get_step()
            suffix = suffix[step - 1] if step < 4 else suffix[3]
            stage = f"{stage.name} Stage ({step}{suffix} Step)"
        else:
            stage = stage.name

        levels = [["Level", level], ["Realm", realm], ["Stage", stage], ["Path", path]]
        class_header = ["Class", "Alignment", "Affinity"]
        classes = []

        for class_progress in essence.get_class_list():
            name = class_progress.user_class.get_name()
            alignment = class_progress.user_class.get_alignment().name
            affinity = class_progress.get_grade()

            if affinity == "X":
                continue

            classes.append([name, alignment, affinity])

        if len(classes) == 0:
            classes.append(["-", "-", "-"])

        await interaction.response.send_message(
            f"""
            ```{make_table(levels)}\n{make_table(classes, class_header)}```
            """,
            ephemeral=not public,
        )

    async def reload_cmd(self, interaction: discord.Interaction, no_start: bool):
        if not interaction.permissions.administrator:
            await interaction.response.send_message(
                "Sorry, {interaction.user.name}, I can't do that. You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message("You got it, boss.", ephemeral=True)

        if no_start:
            await self.bot_spam("Oh, gotta go for a second. Be back soon!")
            sys.exit(1)
        else:
            await self.bot_spam("Restarting. I'll be back in a moment.")
            sys.exit(0)

    async def on_message(self, message: discord.Message):
        if message.author.id == self.user.id:
            return

        essence = self.db.get_essence(message.author.id)

        print(f"{message.author.name} posted a message. Adding 1 exp.")
        essence.add_points(UserClass.Social_Butterfly, 1)

        stickers = len(message.stickers)
        if stickers > 0:
            points = stickers * 5
            print(f"{message.author.name} posted a sticker. Adding {points} exp.")
            essence.add_points(UserClass.Sticker_Collector, points)

        if message.channel.id == self.memes_channel_id:
            points = len(message.attachments) * 100
            if message.content is not None and len(message.content) > 0:
                points += 1

            print(f"{message.author.name} posted a meme. Adding {points} exp.")
            essence.add_points(UserClass.Jester, points)

        if message.channel.id == self.new_members_channel_id:
            join_cutoff = datetime.now() - timedelta(days=1)
            points = 0

            for mention in message.mentions:
                if mention.joined_at is None:
                    continue

                if mention.joined_at > join_cutoff:
                    continue

                points += 100

            if points > 0:
                print(
                    f"{message.author.name} has greeted a new user(s). Adding {points} exp."
                )
                essence.add_points(UserClass.Friendly_Guide, points)

        if message.channel.id == self.cute_pics_channel_id:
            points = len(message.attachments) * 100
            if message.content is not None and len(message.content) > 0:
                points += 1

            print(f"{message.author.name} posted a cute pic. Adding {points} exp.")
            essence.add_points(UserClass.Soul_Healer, points)

        if message.channel.id == self.nsfw_channel_id:
            points = len(message.attachments) * 100
            if message.content is not None and len(message.content) > 0:
                points += 1

            print(f"{message.author.name} posted a NSFW pic. Adding {points} exp.")
            essence.add_points(UserClass.Deviant, points)

        if (
            message.channel.id == self.tsqs_channel_id
            or message.channel.id == self.tsqs_spoiler_channel_id
        ):
            points = 10
            print(f"{message.author.name} talked about TSQS. Adding {points} exp.")
            essence.add_points(UserClass.Bug_Girl_Connoisseur, points)

            points = 1
            print(f"{message.author.name} talked about a book. Adding {points} exp.")
            essence.add_points(UserClass.Reader, points)

        if message.channel.id == self.suggestions_channel_id:
            points = 10
            print(f"{message.author.name} made a suggestion. Adding {points} exp.")
            essence.add_points(UserClass.Visionary, points)

        if message.channel.id == self.theorycrafting_channel_id:
            points = 10
            print(f"{message.author.name} theorycrafted. Adding {points} exp.")
            essence.add_points(UserClass.Conspiracy_Theorist, points)

        if message.channel.id == self.q_and_a_channel_id:
            points = 10
            print(f"{message.author.name} asked a question. Adding {points} exp.")
            essence.add_points(UserClass.Researcher, points)

        if message.channel.id == self.server_discussion_channel_id:
            points = 10
            print(
                f"{message.author.name} discussed meta server topics. Adding {points} exp."
            )
            essence.add_points(UserClass.Tech_Support, points)

        if message.channel.id == self.bot_spam_channel_id:
            points = 1
            print(f"{message.author.name} talked in bot spam. Adding {points} exp.")
            essence.add_points(UserClass.Tech_Support, points)

        if message.channel.id == self.cool_stuff_channel_id:
            points = len(message.attachments) * 100
            if message.content is not None and len(message.content) > 0:
                points += 1

            print(f"{message.author.name} posted something cool. Adding {points} exp.")
            essence.add_points(UserClass.Web_Archiver, points)

        if message.channel.id == self.show_off_channel_id:
            if (
                message.thread is not None
                and message.thread.owner_id == message.author.id
            ):
                points = len(message.attachments) * 1000
                if message.content is not None and len(message.content) > 0:
                    points += 1

                print(f"{message.author.name} showed off. Adding {points} exp.")
                essence.add_points(UserClass.Content_Creator, points)

        if message.channel.id == self.intro_channel_id:
            points = 50

            join_cutoff = datetime.now() - timedelta(days=3)
            if (
                message.author.joined_at is not None
                and message.author.joined_at >= join_cutoff
            ):
                points = 500

            print(f"{message.author.name} introduced themselves. Adding {points} exp.")
            essence.add_points(UserClass.Social_Butterfly, points)

        if message.channel.id == self.fan_art_channel_id:
            if (
                message.thread is not None
                and message.thread.owner_id == message.author.id
            ):
                points = len(message.attachments) * 1000
                if message.content is not None and len(message.content) > 0:
                    points += 1

                print(f"{message.author.name} posted fan art. Adding {points} exp.")
                essence.add_points(UserClass.Artist, points)

                print(f"{message.author.name} showed off. Adding {points} exp.")
                essence.add_points(UserClass.Content_Creator, points)

        if message.channel.id == self.fan_games_channel_id:
            if (
                message.thread is not None
                and message.thread.owner_id == message.author.id
            ):
                points = len(message.attachments) * 1000
                if message.content is not None and len(message.content) > 0:
                    points += 1

                print(f"{message.author.name} posted a fan game. Adding {points} exp.")
                essence.add_points(UserClass.GameDev, points)

                print(f"{message.author.name} showed off. Adding {points} exp.")
                essence.add_points(UserClass.Content_Creator, points)

        if message.channel.id == self.fan_books_channel_id:
            if (
                message.thread is not None
                and message.thread.owner_id == message.author.id
            ):
                points = len(message.attachments) * 1000
                if message.content is not None and len(message.content) > 0:
                    points += 1

                print(f"{message.author.name} posted a fan book. Adding {points} exp.")
                essence.add_points(UserClass.Storyteller, points)

                print(f"{message.author.name} showed off. Adding {points} exp.")
                essence.add_points(UserClass.Content_Creator, points)

        if message.channel.id == self.book_discussion_channel_id:
            points = 10
            print(f"{message.author.name} discussed a book. Adding {points} exp.")
            essence.add_points(UserClass.Reader, points)

        self.db.set_essence(message.author.id, essence)


def run():
    client = SaricaBot()
    client.run(os.getenv("DISCORD_TOKEN"))

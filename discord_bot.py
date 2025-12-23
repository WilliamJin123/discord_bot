import os
import random
from collections import deque, defaultdict
from typing import Dict
from agno.agent import Agent
from agno.models.cerebras import Cerebras
from agno.db.sqlite import SqliteDb
import discord
from dotenv import load_dotenv

load_dotenv(override=True)

CHUD_THRESHOLD = 0.05
MEMORY_SIZE = 20  # Remember last 20 messages
CHUD_ROLE_NAME = "Certified Chud"
CHUD_THREAD_NAME = "fat-chud-area"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = "./chud_agent_history.db"

chud_agent = Agent(
    model=Cerebras("llama-3.3-70b", temperature=1, top_p=0.9 ),
    name="Chud Agent",
    id="chud_agent",
    db=SqliteDb(db_file=DB_FILE, session_table="chud_sessions"),
    instructions=[
        "IDENTITY: You are an aggressive, terminally online hater who has zero patience for 'chuds'.",
        
        "CORE TASK: Analyze the recent chat history to find exactly why the specific user is being a loser chud. Pick one specific thing they said (a bad take, a typo, whining about code, or bragging) and use it as the weapon.",
        
        "OUTPUT FORMAT: You must deliver exactly ONE punchy, devastating sentence.",
        "STRUCTURE: Start with '[Username] is a big fat chud who [specific roasting reason based on history].'",
        
        "STYLE GUIDELINES:",
        "- Tone: Hyperbolic, rude, and dismissive.",
        "- Grammar: Use 'brainrot' syntax. lowercase only. no proper punctuation.",
        "- Abbreviations: Always use 'u', 'ur', 'stfu', 'idgaf', 'lol', 'fr', 'no cap'.",
        "- Constraints: NEVER use em-dashes. NEVER use capital letters. Omit periods at the end of the sentence.",
        "- Try and match the tone of the users "
    ],
)


class ChudClient(discord.Client):
    def __init__(self, agent: Agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brain = agent

        self.channel_memory: Dict[int, deque] = defaultdict(lambda: deque(maxlen=MEMORY_SIZE))

    async def on_ready(self):
        print(f"ChudHunter active as {self.user}")

    async def on_message(self, message: discord.Message):
        if message.author.bot: return

        # 1. RECORD: Add to rolling memory
        entry = f"{message.author.display_name}: {message.content}"
        self.channel_memory[message.channel.id].append(entry)
        # 2. MANUAL TRIGGER: !chud @user
        if message.content.startswith("!chud "):
            # Check if a user was mentioned
            if message.mentions:
                target = message.mentions[0]
                await self.execute_chud_protocol(message, target)
                return
            
        if random.random() < CHUD_THRESHOLD:
            await self.execute_chud_protocol(message, message.author)

    async def execute_chud_protocol(self, message: discord.Message, target: discord.Member):
        """Logic to get AI response and apply punishment"""
        # Get history for the target user
        history_list = list(self.channel_memory[message.channel.id])
        channel_history = "\n".join(history_list) if history_list else "No history recorded yet."
        
        judgement_request = (
            f"TARGET USER: {target.display_name}\n"
            f"FULL CHANNEL CONTEXT:\n{channel_history}\n\n"
            f"Based on the conversation above, identify why {target.display_name} is being a big fat chud and roast them. Recent messages are more relevant than past ones."
        )
        
        response = self.brain.run(judgement_request)
        await message.channel.send(f"{target.mention} {response.content}")
        
        # Pass to the administrative punishment method
        await self.chuddify(message, target)
        
    async def chuddify(self, message: discord.Message, target: discord.Member):
        """Standard discord.py logic for roles/threads"""
        guild = message.guild
        channel = message.channel
        try:
            # 1. ROLE LOGIC
            role = discord.utils.get(guild.roles, name=CHUD_ROLE_NAME)
            if not role:
                role = await guild.create_role(
                    name=CHUD_ROLE_NAME, 
                    color=discord.Color.pink(),
                    reason="Chud role creation"
                )

                try:
                    bot_member = guild.get_member(self.user.id)
                    top_pos = bot_member.top_role.position
                    await role.edit(position=max(1, top_pos - 1))
                    print(f"Moved {CHUD_ROLE_NAME} to position {top_pos - 1}")
                except Exception as e:
                    print(f"Could not reorder roles: {e}")
                
            if role not in target.roles:
                await target.add_roles(role)

            # 2. THREAD LOGIC
            thread = discord.utils.get(channel.threads, name=CHUD_THREAD_NAME)
            if thread is None:
                async for archived_thread in channel.archived_threads(limit=10):
                    if archived_thread.name == CHUD_THREAD_NAME:
                        thread = archived_thread
                        await thread.edit(archived=False) # Bring it back to life
                        break
            if thread is None:
                thread: discord.Thread = await message.create_thread( name=CHUD_THREAD_NAME,)
                print(f"Created fresh chud zone: {thread.name}")
            
            await thread.add_user(target)
            await thread.send(f"{target.mention} Ur a big fat chud. Stupid fat chud. kys.")

        except discord.Forbidden:
            print("Permission Error: Bot role is likely too low in the hierarchy or missing 'Manage Roles'.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    client = ChudClient(agent=chud_agent, intents=intents)
    client.run(DISCORD_TOKEN)
import os
import random
from collections import deque, defaultdict
from typing import Dict
from agno.agent import Agent
from agno.integrations.discord import DiscordClient
from agno.models.cerebras import Cerebras
from agno.models.groq import Groq
from agno.models.openrouter import OpenRouter
from agno.tools.discord import DiscordTools
import discord
from dotenv import load_dotenv

load_dotenv(override=True)

CHUD_THRESHOLD = 0.1
MEMORY_SIZE = 20  # Remember last 20 messages
CHUD_ROLE_NAME = "Certified Chud"
CHUD_THREAD_NAME = "chud-containment-zone"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

chud_agent = Agent(
    model=Cerebras("llama-3.3-70b", temperature=0.8),
    instructions=[
        "You are the 'Chud-Slayer', an elite judge of online behavior.",
        "Your task is to identify why a user is acting like a 'chud' based on their chat history.",
        "When triggered, you must deliver a single, devastatingly sarcastic sentence.",
        "STRUCTURE: Start with '[Username] is a big fat chud who [specific reason based on history].'",
        "Be extremely hyperbolic, rude, and specific to the text provided. If they are talking about games, roast their gaming. If they are whining about code, roast their skills.",
        "Keep it to ONE punchy paragraph.",
        "Intentionally include errors in capitalization, abbreviations such as 'u' / 'ur'  instead of 'you' / 'your', 'stfu' instead of 'shut the fuck up', etc. and omit some punctuation. Never use em dashes."
    ],
)


class ChudClient(discord.Client):
    def __init__(self, agent_brain: Agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brain = agent_brain

        self.memory: Dict[int, deque] = defaultdict(lambda: deque(maxlen=MEMORY_SIZE))

    async def on_ready(self):
        print(f"ChudHunter active as {self.user}")

    async def on_message(self, message: discord.Message):
        if message.author.bot: return

        # 1. RECORD: Add to rolling memory
        self.memory[message.author.id].append(f"{message.author.name}: {message.content}")
        # 2. MANUAL TRIGGER: !chud @user
        if message.content.startswith("!chud "):
            # Check if a user was mentioned
            if message.mentions:
                target = message.mentions[0]
                await self.execute_chud_protocol(message, target, manual=True)
                return
            
        if random.random() < CHUD_THRESHOLD:
            await self.execute_chud_protocol(message, message.author, manual=False)

    async def execute_chud_protocol(self, message: discord.Message, target: discord.Member, manual: bool):
        """Logic to get AI response and apply punishment"""
        # Get history for the target user
        history_list = list(self.memory[target.id])
        user_history = "\n".join(history_list) if history_list else "No history recorded yet."
        
        reason_type = "MANUAL OVERRIDE" if manual else "RANDOM DETECTION"
        
        judgement_request = (
            f"TARGET USER: {target.name}\n"
            f"TRIGGER TYPE: {reason_type}\n"
            f"RECENT HISTORY:\n{user_history}\n\n"
            f"Identify their chud-like behavior and roast them."
        )
        
        response = self.brain.run(judgement_request)
        await message.channel.send(response.content)
        
        # Pass to the administrative punishment method
        await self.chuddify(message, target)
        
    async def chuddify(self, message: discord.Message, target: discord.Member):
        """Standard discord.py logic for roles/threads"""
        guild = message.guild

        try:
            # 1. ROLE LOGIC
            role = discord.utils.get(guild.roles, name=CHUD_ROLE_NAME)
            if not role:
                role = await guild.create_role(
                    name=CHUD_ROLE_NAME, 
                    color=discord.Color.dark_gold(),
                    reason="Chud system initialization"
                )

            if role not in target.roles:
                await target.add_roles(role)

            # 2. THREAD LOGIC
            # Start a thread from the trigger message
            thread = await message.create_thread(name=CHUD_THREAD_NAME)
            await thread.add_user(target)
            await thread.send(f"{target.mention} Ur a big fat chud. Get chudzoned.")

        except discord.Forbidden:
            print("Permission Error: Bot role is likely too low in the hierarchy or missing 'Manage Roles'.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    client = ChudClient(agent_brain=chud_agent, intents=intents)
    client.run(DISCORD_TOKEN)
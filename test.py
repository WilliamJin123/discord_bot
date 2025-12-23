import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import discord
from discord_bot import ChudClient, chud_agent # Change 'your_bot_file' to your filename

@pytest.mark.asyncio
async def test_chud_logic():
    # 1. Mock the Discord Message
    mock_guild = MagicMock()
    mock_author = AsyncMock(spec=discord.Member)
    mock_author.name = "TestUser"
    mock_author.id = 12345
    mock_author.roles = []
    
    mock_message = AsyncMock(spec=discord.Message)
    mock_message.guild = mock_guild
    mock_message.author = mock_author
    mock_message.content = "I hate Python and everyone who uses it."
    mock_message.mentions = []

    # 2. Mock the Agent Brain
    mock_brain = MagicMock()
    mock_brain.run.return_value = MagicMock(content="TestUser is a big fat chud who hates clean syntax.")

    # 3. Initialize Client
    client = ChudClient(agent_brain=mock_brain)
    
    # 4. Manually trigger the message handler
    with patch("random.random", return_value=0.0): # Force the 10% chance to trigger
        await client.on_message(mock_message)

    # 5. Assertions
    print("Checking if brain was consulted...")
    mock_brain.run.assert_called()
    
    print("Checking if roast was sent...")
    mock_message.channel.send.assert_called_with("TestUser is a big fat chud who hates clean syntax.")
    
    print("Checking if thread was created...")
    mock_message.create_thread.assert_called()

if __name__ == "__main__":
    # If not using pytest, we can run it manually
    asyncio.run(test_chud_logic())
    print("\n✅ Test completed successfully!")
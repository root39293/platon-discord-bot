import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents
        )
        
        self.initial_extensions = [
            "cogs.todo",
            "cogs.quotes"
        ]

    async def setup_hook(self):
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ {ext} 로드 완료")
            except Exception as e:
                print(f"❌ {ext} 로드 실패: {e}")
        
        print("슬래시 커맨드 동기화 중...")
        try:
            synced = await self.tree.sync()
            print(f"동기화된 커맨드: {len(synced)}개")
            print("동기화 완료!")
        except Exception as e:
            print(f"동기화 실패: {e}")

    async def on_ready(self):
        print(f"✨ {self.user.name} 준비 완료!")
        print(f"ID: {self.user.id}")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Developed by @faith6"
            )
        )

bot = MyBot()

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))

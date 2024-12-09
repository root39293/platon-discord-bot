import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from typing import Optional

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
            "cogs.quotes",
            "cogs.crawl_news",
            "cogs.finance"
        ]

    async def setup_hook(self):
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ {ext} 로드 완료")
            except Exception as e:
                print(f"❌ {ext} 로드 실패: {e}")
        
        @self.tree.command(name="도움말", description="사용 가능한 모든 명령어를 확인합니다")
        async def help(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🤖 명령어 도움말",
                description="사용 가능한 모든 명령어 목록입니다.",
                color=discord.Color.blue()
            )

            # 코인 관련 명령어
            embed.add_field(
                name="💰 코인 정보",
                value=(
                    "`/코인시세` - 특정 코인의 실시간 시세 조회\n"
                    "`/인기코인` - 거래대금 TOP 5 + BTC 시세 조회\n"
                    "`/코인알림설정` - 주기적 시세 알림 설정 (관리자)"
                ),
                inline=False
            )

            # 뉴스 관련 명령어
            embed.add_field(
                name="📰 뉴스",
                value=(
                    "`/뉴스조회` - 실시간 뉴스 확인\n"
                    "`/뉴스알림설정` - 주기적 뉴스 알림 설정 (관리자)"
                ),
                inline=False
            )

            # 명언 관련 명령어
            embed.add_field(
                name="✨ 명언",
                value=(
                    "`/명언조회` - AI가 생성한 명언 확인\n"
                    "`/명언알림설정` - 매일 아침 명언 알림 설정 (관리자)"
                ),
                inline=False
            )

            # 할 일 관련 명령어
            embed.add_field(
                name="📝 할 일",
                value=(
                    "`/할일` - 개인 할 일 목록 관리\n"
                    "`/주간퀘` - 메이플 주간퀘스트 체크리스트"
                ),
                inline=False
            )

            # 푸터에 관리자 명령어 안내
            embed.set_footer(text="💡 (관리자) 표시가 있는 명령어는 관리자 권한이 필요합니다.")

            await interaction.response.send_message(embed=embed, ephemeral=True)

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
                name=f"v0.1.0 | Developed by github.com/root39293"
            )
        )

bot = MyBot()

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))

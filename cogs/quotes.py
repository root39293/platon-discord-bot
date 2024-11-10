# quotes.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import google.generativeai as genai
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import json
from datetime import datetime

class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.quote_channel_id = None 
        self.setup_gemini()
        self.scheduler = AsyncIOScheduler()
        self.setup_scheduler()

    def setup_gemini(self):
        """Gemini API 초기화"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def setup_scheduler(self):
        """매일 아침 9시에 명언 전송"""
        korea_tz = pytz.timezone('Asia/Seoul')
        self.scheduler.add_job(
            self.send_daily_quote,
            CronTrigger(hour=9, minute=0, timezone=korea_tz),
            id='daily_quote',
            max_instances=1,
            coalesce=True
        )
        self.scheduler.start()

    @app_commands.command(name="명언설정", description="매일 아침 명언이 전송될 채널을 설정합니다")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_quote_channel(self, interaction: discord.Interaction):
        """명언이 전송될 채널을 설정합니다"""
        self.quote_channel_id = interaction.channel.id
        
        embed = discord.Embed(
            title="✨ 명언 채널 설정",
            description=f"매일 아침 9시에 이 채널에서 명언이 전송됩니다.",
            color=discord.Color.brand_green()
        )
        embed.add_field(
            name="📍 설정된 채널",
            value=f"{interaction.channel.mention}",
            inline=False
        )
        embed.add_field(
            name="⏰ 전송 시간",
            value="매일 아침 9시 (KST)",
            inline=False
        )
        embed.set_footer(text="설정을 변경하려면 다른 채널에서 다시 명령어를 사용하세요.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def generate_quote(self):
        """명언 생성"""
        prompt = """
        실존 인물의 실제 명언을 제공해줘.
        다음 형식으로만 응답해줘:
        {
            "quote": "명언 내용",
            "author": "작성자",
            "context": "간단한 맥락"
        }

        조건:
        1. 명언 선택:
           - 반드시 실제로 해당 인물이 말했다고 역사적으로 입증된 명언만 선택
           - 인터넷에서 흔히 보이는 가짜 명언이나 출처가 불분명한 명언은 제외
           - 책, 연설문, 일기, 편지 등 명확한 출처가 있는 명언만 선택
           - 한국어로 번역
        
        2. 작성자:
           - 실존했던 역사적 인물만 선택
           - 작성자의 full name 표기
        
        3. 맥락:
           - 구체적인 연도나 장소, 상황 포함
           - 해당 명언이 등장한 구체적인 출처 명시 (책 제목, 연설명 등)

        위 JSON 형식으로만 응답하고 다른 텍스트는 절대 포함하지 마.
        """

        try:
            response = await self.model.generate_content_async(prompt)
            if not response.text:
                raise ValueError("API 응답이 비어있습니다")
                
            # 응답 텍스트 정리
            text = response.text.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1].rsplit('\n', 1)[0]
            if text.startswith('json'):
                text = text[4:].strip()
                
            quote_data = json.loads(text)
            
            # 필수 필드 검증
            if not all(key in quote_data for key in ['quote', 'author', 'context']):
                raise ValueError("필수 필드가 누락되었습니다")
                
            return quote_data
            
        except Exception as e:
            print(f"명언 생성 오류: {str(e)}")
            # 폴백 명언 반환
            return {
                "quote": "실패는 성공의 어머니다.",
                "author": "토마스 에디슨",
                "context": "수많은 실험 실패 후 전구 발명에 성공했을 때 한 말 (1879년)"
            }

    async def send_quote_embed(self, quote_data):
        """명언 임베드 생성"""
        embed = discord.Embed(color=discord.Color.gold())
        
        # 명언 본문 (큰 텍스트로)
        embed.description = f"```{quote_data['quote']}```"
        
        # 작성자와 맥락
        author_text = f"*― {quote_data['author']}*"
        context_text = f"\n{quote_data['context']}"
        embed.add_field(name="", value=f"{author_text}{context_text}", inline=False)
        
        # 날짜 표시
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y년 %m월 %d일")
        embed.set_footer(text=f"📅 {today}")
        
        return embed

    async def send_daily_quote(self):
        """매일 아침 명언 전송"""
        try:
            if not self.quote_channel_id:
                return
                
            channel = self.bot.get_channel(self.quote_channel_id)
            if not channel:
                return

            quote_data = await self.generate_quote()
            embed = await self.send_quote_embed(quote_data)
            await channel.send(embed=embed)
                
        except Exception as e:
            print(f"명언 전송 실패: {e}")

    def cog_unload(self):
        """스케줄러 정리"""
        self.scheduler.shutdown()

    @app_commands.command(name="명언생성", description="명언을 생성합니다")
    @app_commands.checks.has_permissions(administrator=True)
    async def generate_quote_command(self, interaction: discord.Interaction):
        """명언을 생성합니다"""
        try:
            await interaction.response.defer()
            
            quote_data = await self.generate_quote()
            if not quote_data:
                raise ValueError("명언 생성에 실패했습니다")
                
            embed = await self.send_quote_embed(quote_data)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ 오류 발생",
                description=f"명언 생성 중 오류가 발생했습니다:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Quotes(bot))
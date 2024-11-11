import discord
from discord import app_commands
from discord.ext import commands
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from datetime import datetime
import pytz
from discord.ext import tasks
import logging

class NewsItem:
    def __init__(self, title: str, url: str, summary: str = None, date: str = None):
        self.title = title
        self.url = url
        self.summary = summary
        self.date = date

class CrawlNews(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.news_channel_id = None
        self.session = None
        self.news_url = "https://media.naver.com/press/052/ranking?type=popular"
        self.daily_news_task.start()
        
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_news(self, url: str) -> list[NewsItem]:
        """뉴스 크롤링 메인 함수"""
        try:
            await self.init_session()
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP 요청 실패: {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                news_items = []
                articles = soup.select('ul.press_ranking_list > li.as_thumb')[:10]  
                
                for article in articles:
                    title = article.select_one('strong.list_title').text.strip()
                    url = article.select_one('a._es_pc_link')['href']
                    rank = article.select_one('em.list_ranking_num').text.strip()
                    
                    news_items.append(NewsItem(
                        title=f"{rank}. {title}",
                        url=url
                    ))
                
                return news_items
                
        except Exception as e:
            logging.error(f"뉴스 크롤링 중 오류 발생: {e}")
            return []

    def create_news_embed(self, news_items: list[NewsItem]) -> discord.Embed:
        """뉴스 임베드 생성"""
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y년 %m월 %d일")
        
        embed = discord.Embed(
            title=f"📰 오늘의 뉴스 - {today}",
            color=discord.Color.blue()
        )
        
        for item in news_items:
            embed.add_field(
                name=item.title,
                value=f"[링크]({item.url})\n{item.summary if item.summary else ''}\n",
                inline=False
            )
            
        embed.set_footer(text=f"마지막 업데이트: {datetime.now(pytz.timezone('Asia/Seoul')).strftime('%H:%M')}")
        return embed

    @tasks.loop(hours=3)  # 3시간마다 실행
    async def daily_news_task(self):
        """뉴스 전송 (3시간 간격)"""
        if not self.news_channel_id:
            return
            
        channel = self.bot.get_channel(self.news_channel_id)
        if not channel:
            return
            
        news_items = await self.fetch_news(self.news_url)
        if news_items:
            embed = self.create_news_embed(news_items)
            await channel.send(embed=embed)

    @app_commands.command(name="뉴스설정", description="뉴스가 전송될 채널을 설정합니다")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_news_channel(self, interaction: discord.Interaction):
        """뉴스 채널 설정"""
        self.news_channel_id = interaction.channel.id
        
        embed = discord.Embed(
            title="✅ 뉴스 채널 설정 완료",
            description="매일 아침 9시에 이 채널에서 뉴스가 전송됩니다.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="뉴스테스트", description="뉴스 크롤링 테스트")
    @app_commands.checks.has_permissions(administrator=True)
    async def test_news(self, interaction: discord.Interaction):
        """뉴스 크롤링 테스트"""
        await interaction.response.defer() 
        
        try:
            news_items = await self.fetch_news(self.news_url)
            if news_items:
                embed = self.create_news_embed(news_items)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("뉴스를 가져오는데 실패했습니다.", ephemeral=True)
        except Exception as e:
            logging.error(f"뉴스 테스트 중 오류 발생: {e}")
            await interaction.followup.send(f"오류가 발생했습니다: {str(e)}", ephemeral=True)

    def cog_unload(self):
        """Cog 언로드 시 정리 작업"""
        self.daily_news_task.cancel()
        if self.session:
            asyncio.create_task(self.close_session())

async def setup(bot: commands.Bot):
    await bot.add_cog(CrawlNews(bot)) 
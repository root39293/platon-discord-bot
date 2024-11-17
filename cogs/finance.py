import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import logging
from datetime import datetime
import pytz
from typing import Optional, List, Dict
from discord.ext import tasks

COIN_NAMES = {
    'BTC': '비트코인',
    'ETH': '이더리움',
    'NEO': '네오',
    'MTL': '메탈',
    'XRP': '리플',
    'ETC': '이더리움클래식',        
    'SNT': '스테이터스네트워크토큰',
    'WAVES': '웨이브',
    'XEM': '넴',
    'QTUM': '퀀텀',
    'LSK': '리스크',
    'STEEM': '스팀',
    'XLM': '스텔라루멘',
    'ARDR': '아더',
    'ARK': '아크',
    'STORJ': '스토리지',
    'GRS': '그로스톨코인',
    'ADA': '에이다',
    'SBD': '스팀달러',
    'POWR': '파워렛저',
    'BTG': '비트코인골드',
    'ICX': '아이콘',
    'EOS': '이오스',
    'TRX': '트론',
    'SC': '시아코인',
    'ONT': '온톨로지',
    'ZIL': '질리카',
    'POLYX': '폴리매쉬',
    'ZRX': '제로엑스',
    'LOOM': '룸네트워크',
    'BCH': '비트코인캐시',
    'BAT': '베이직어텐션토큰',
    'IOST': '아이오에스티',
    'CVC': '시빅',
    'IQ': '아이큐',
    'IOTA': '아이오타',
    'HIFI': '하이파이',
    'ONG': '온톨로지가스',
    'GAS': '가스',
    'BOUNTY': '체인바운티',
    'ELF': '엘프',
    'KNC': '카이버네트워크',
    'BSV': '비트코인에스브이',
    'THETA': '쎄타토큰',
    'QKC': '쿼크체인',
    'BTT': '비트토렌트',
    'MOC': '모스코인',
    'TFUEL': '쎄타퓨엘',
    'MANA': '디센트럴랜드',
    'ANKR': '앵커',
    'AERGO': '아르고',
    'ATOM': '코스모스',
    'TT': '썬더코어',
    'GAME2': '게임빌드',
    'MBL': '무비블록',
    'WAXP': '왁스',
    'HBAR': '헤데라',
    'MED': '메디블록',
    'MLK': '밀크',
    'STPT': '에스티피',
    'ORBS': '오브스',
    'VET': '비체인',
    'CHZ': '칠리즈',
    'STMX': '스톰엑스',
    'DKA': '디카르고',
    'HIVE': '하이브',
    'KAVA': '카바',
    'AHT': '아하토큰',
    'LINK': '체인링크',
    'XTZ': '테조스',
    'BORA': '보라',
    'JST': '저스트',
    'CRO': '크로노스',
    'TON': '토카막네트워크',
    'SXP': '솔라',
    'HUNT': '헌트',
    'DOT': '폴카닷',
    'MVL': '엠블',
    'STRAX': '스트라티스',
    'AQT': '알파쿼크',
    'GLM': '골렘',
    'META': '메타디움',
    'FCT2': '피르마체인',
    'CBK': '코박토큰',
    'SAND': '샌드박스',
    'HPO': '히포크랏',
    'DOGE': '도지코인',
    'STRIKE': '스트라이크',
    'PUNDIX': '펀디엑스',
    'FLOW': '플로우',
    'AXS': '엑시인피니티',
    'STX': '스택스',
    'XEC': '이캐시',
    'SOL': '솔라나',
    'POL': '폴리곤에코시스템토큰',
    'AAVE': '에이브',
    '1INCH': '1인치네트워크',
    'ALGO': '알고랜드',
    'NEAR': '니어프로토콜',
    'AVAX': '아발란체',
    'T': '쓰레스홀드',
    'CELO': '셀로',
    'GMT': '스테픈',
    'APT': '앱토스',
    'SHIB': '시바이누',
    'MASK': '마스크네트워크',
    'ARB': '아비트럼',
    'EGLD': '멀티버스엑스',
    'SUI': '수이',
    'GRT': '더그래프',
    'BLUR': '블러',
    'IMX': '이뮤터블엑스',
    'SEI': '세이',
    'MINA': '미나',
    'CTC': '크레딧코인',
    'ASTR': '아스타',
    'ID': '스페이스아이디',
    'PYTH': '피스네트워크',
    'MNT': '맨틀',
    'AKT': '아카시네트워크',
    'ZETA': '제타체인',
    'AUCTION': '바운스토큰',
    'STG': '스타게이트파이낸스',
    'BEAM': '빔',
    'TAIKO': '타이코',
    'USDT': '테더',
    'ONDO': '온도파이낸스',
    'ZRO': '레이어제로',
    'BLAST': '블라스트',
    'JUP': '주피터',
    'ENS': '이더리움네임서비스',
    'G': '그래비티',
    'PENDLE': '펜들',
    'ATH': '에이셔',
    'USDC': '유에스디코인',
    'UXLINK': '유엑스링크',
    'BIGTIME': '빅타임',
    'CKB': '너보스',
    'W': '웜홀',
    'CARV': '카브',
    'INJ': '인젝티브',
    'MEW': '캣인어독스월드',
    'UNI': '유니스왑',
    'SAFE': '세이프',
    'DRIFT': '드리프트',
    'AGLD': '어드벤처골드',
    'PEPE': '페페',
    'MATIC': '폴리곤',
}

def create_reverse_mapping(coin_names: dict) -> dict:
    """코인 한글명으로 심볼을 찾기 위한 역방향 매핑"""
    reverse_map = {}
    for symbol, korean in coin_names.items():
        # 기본 한글명 매핑
        reverse_map[korean.lower()] = symbol
        # 특수문자 제거한 한글명도 매핑 (예: "비트코인골드" -> BTG)
        cleaned_name = korean.replace(" ", "").lower()
        reverse_map[cleaned_name] = symbol
    return reverse_map

COIN_SYMBOLS = create_reverse_mapping(COIN_NAMES)

class Finance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = None
        self.base_url = "https://api.upbit.com/v1"
        self.alert_channel_id = None
        self.price_alert_task.start()  # 가격 알림 task 시작
        
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_price(self, markets: list[str]) -> list[dict]:
        """업비트 시세 조회"""
        try:
            await self.init_session()
            url = f"{self.base_url}/ticker"
            params = {
                "markets": ",".join(markets)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"API 요청 실패: {response.status}")
                return await response.json()
                
        except Exception as e:
            logging.error(f"시세 조회 중 오류 발생: {e}")
            raise

    def format_price(self, price: float, market_type: str) -> str:
        """가격 포맷팅"""
        if market_type == "KRW":
            if price >= 100:
                return f"{price:,.0f}"
            else:
                return f"{price:.2f}"
        else:  # USDT
            if price >= 100:
                return f"{price:.2f}"
            else:
                return f"{price:.4f}"

    def get_change_color(self, change_rate: float) -> discord.Color:
        """변동률에 따른 색상 반환"""
        if change_rate > 3:
            return discord.Color.from_rgb(255, 59, 59)  # 강한 상승 - 진한 빨강
        elif change_rate > 0:
            return discord.Color.from_rgb(255, 129, 129)  # 상승 - 연한 빨강
        elif change_rate < -3:
            return discord.Color.from_rgb(59, 59, 255)  # 강한 하락 - 진한 파랑
        elif change_rate < 0:
            return discord.Color.from_rgb(129, 129, 255)  # 하락 - 연한 파랑
        else:
            return discord.Color.light_grey()  # 보합

    def create_price_embed(self, data: list[dict]) -> discord.Embed:
        """시세 정보 임베드 생성"""
        if not data:
            raise ValueError("시세 데이터가 없습니다")

        market = data[0]["market"]
        symbol = market.split("-")[1]
        korean_name = COIN_NAMES.get(symbol, symbol)
        
        # 첫 번째 마켓(KRW)의 변동률로 색상 결정
        main_change_rate = data[0]["signed_change_rate"] * 100
        embed_color = self.get_change_color(main_change_rate)

        embed = discord.Embed(
            title=f" {korean_name} ({symbol}) 실시간 시세",
            color=embed_color,
            timestamp=datetime.now(pytz.UTC)
        )

        for item in data:
            market_type = "KRW" if item["market"].startswith("KRW") else "USDT"
            current_price = item["trade_price"]
            change_rate = item["signed_change_rate"] * 100
            change_price = item["signed_change_price"]
            acc_trade_price_24h = item["acc_trade_price_24h"]
            
            # 가격 포맷팅
            price_str = self.format_price(current_price, market_type)
            change_price_str = self.format_price(abs(change_price), market_type)
            
            # 등락 화살표 및 이모지
            if change_rate > 0:
                change_emoji = "🔺"  # 빨간 상승 삼각형
                price_trend = "상승" 
            elif change_rate < 0:
                change_emoji = "⏬"  # 란 이중 하락 화살표 
                price_trend = "하락"
            else:
                change_emoji = "➖"  # 보합
                price_trend = "보합"

            # 24시간 거래대금
            if market_type == "KRW":
                trade_price_str = f"{acc_trade_price_24h/1000000:,.0f}백만원"
            else:
                trade_price_str = f"{acc_trade_price_24h:,.0f} USDT"

            market_title = "원화 (KRW) 마켓" if market_type == "KRW" else "테더 (USDT) 마켓"
            
            embed.add_field(
                name=f"💱 {market_title}",
                value=f"```\n"
                      f"현재가: {price_str} {market_type}\n"
                      f"전일대비: {change_emoji} {price_trend} {abs(change_rate):.2f}% ({change_price_str} {market_type})\n"
                      f"고가: {self.format_price(item['high_price'], market_type)} {market_type}\n"
                      f"저가: {self.format_price(item['low_price'], market_type)} {market_type}\n"
                      f"거래대금(24H): {trade_price_str}\n"
                      f"```",
                inline=False
            )

        # 푸터에 업데이트 시간 표시
        korea_time = datetime.now(pytz.timezone('Asia/Seoul'))
        embed.set_footer(
            text=f"업비트 기준 • {korea_time.strftime('%Y-%m-%d %H:%M:%S')} KST"
        )
        
        return embed

    def find_symbol(self, query: str) -> str:
        """코인명 또는 심볼로 실제 심볼 찾기"""
        query = query.strip()
        
        # 대문자로 변환한 입력값이 심볼인 경우
        if query.upper() in COIN_NAMES:
            return query.upper()
        
        # 한글명으로 검색
        cleaned_query = query.replace(" ", "").lower()
        if cleaned_query in COIN_SYMBOLS:
            return COIN_SYMBOLS[cleaned_query]
            
        raise ValueError(f"'{query}'에 해당하는 코인을 찾을 수 없습니다.")

    @app_commands.command(name="코인시세", description="암호화폐의 실시간 시세를 조회합니다")
    @app_commands.describe(코인="코인 심볼 또는 이름 (예: BTC, 비트코인, ETH, 이더리움)")
    async def check_price(self, interaction: discord.Interaction, 코인: str):
        """특정 암호화폐 시세 조회"""
        await interaction.response.defer()
        
        try:
            # 심볼 찾기
            symbol = self.find_symbol(코인)
            markets = [f"KRW-{symbol}"]
            
            # BTC의 경우 USDT 마켓도 조회
            if symbol == "BTC":
                markets.append(f"USDT-{symbol}")
            
            data = await self.fetch_price(markets)
            if not data:
                raise ValueError("해당 코인의 시세 정보를 찾을 수 없습니다")
            
            embed = self.create_price_embed(data)
            await interaction.followup.send(embed=embed)
            
        except ValueError as ve:
            error_embed = discord.Embed(
                title="❌ 코인 조회 실패",
                description=(
                    f"```{str(ve)}```\n"
                    "코인 심볼(예: BTC, ETH) 또는\n"
                    "코인 이름(예: 비트코인, 이더리움)로 검색해주세요."
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ 시스템 오류",
                description="```시세 조회 중 오류가 발생했습니다.\n잠시 후 다시 시도해주세요.```",
                color=discord.Color.red()
            )
            logging.error(f"시세 조회 중 오류: {e}")
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    def cog_unload(self):
        """Cog 언로드 시 정리 작업"""
        if self.session:
            import asyncio
            asyncio.create_task(self.close_session())

    async def fetch_all_krw_markets(self) -> List[Dict]:
        """모든 원화 마켓 시세 조회"""
        try:
            await self.init_session()
            # 원화 마켓 목록 조회
            markets_url = f"{self.base_url}/market/all"
            async with self.session.get(markets_url) as response:
                if response.status != 200:
                    raise Exception("마켓 목록 조회 실패")
                markets_data = await response.json()
                
            # KRW 마켓만 필터링
            krw_markets = [market["market"] for market in markets_data 
                         if market["market"].startswith("KRW-")]
            
            # 시세 조회
            return await self.fetch_price(krw_markets)
                
        except Exception as e:
            logging.error(f"전체 마켓 조회 중 오류: {e}")
            raise

    async def get_top_markets(self) -> discord.Embed:
        """BTC + TOP 5 거래대금 코인 시세 임베드 생성"""
        try:
            # 전체 원화 마켓 데이터 조회
            all_markets = await self.fetch_all_krw_markets()
            
            # 비트코인 데이터 찾기
            btc_data = next((item for item in all_markets 
                           if item["market"] == "KRW-BTC"), None)
            
            # 거래대금 기준 정렬
            sorted_markets = sorted(all_markets, 
                                 key=lambda x: x["acc_trade_price_24h"], 
                                 reverse=True)
            
            # TOP 5 추출 (BTC 제외)
            top_markets = [market for market in sorted_markets 
                         if market["market"] != "KRW-BTC"][:5]
            
            # 임베드 생성
            embed = discord.Embed(
                title="📊 실시간 암호화폐 시세 요약",
                description="BTC + 거래대금 TOP 5",
                color=discord.Color.blue(),
                timestamp=datetime.now(pytz.UTC)
            )
            
            # 비트코인 정보 추가
            if btc_data:
                self.add_market_field(embed, btc_data, "📈 비트코인 (BTC)")
            
            # TOP 5 정보 추가
            for idx, market in enumerate(top_markets, 1):
                symbol = market["market"].split("-")[1]
                korean_name = COIN_NAMES.get(symbol, symbol)
                self.add_market_field(embed, market, 
                                    f"#{idx} {korean_name} ({symbol})")
            
            korea_time = datetime.now(pytz.timezone('Asia/Seoul'))
            embed.set_footer(
                text=f"업비트 기준 • {korea_time.strftime('%Y-%m-%d %H:%M:%S')} KST"
            )
            
            return embed
            
        except Exception as e:
            logging.error(f"TOP 마켓 데이터 처리 중 오류 발생: {e}")
            raise

    def add_market_field(self, embed: discord.Embed, market_data: Dict, title: str):
        """임베드에 마켓 정보 필드 추가"""
        current_price = market_data["trade_price"]
        change_rate = market_data["signed_change_rate"] * 100
        change_price = market_data["signed_change_price"]
        acc_trade_price_24h = market_data["acc_trade_price_24h"]
        
        # 가격 변동 화살표
        change_emoji = "🔺" if change_rate > 0 else "⏬" if change_rate < 0 else "➖"
        price_trend = "상승" if change_rate > 0 else "하락" if change_rate < 0 else "보합"
        
        embed.add_field(
            name=title,
            value=f"```\n"
                  f"현재가: {self.format_price(current_price, 'KRW')} KRW\n"
                  f"전일대비: {change_emoji} {price_trend} {abs(change_rate):.2f}% "
                  f"({self.format_price(abs(change_price), 'KRW')} KRW)\n"
                  f"거래대금: {acc_trade_price_24h/1000000:,.0f}백만원\n"
                  f"```",
            inline=False
        )

    @tasks.loop(hours=3)
    async def price_alert_task(self):
        """3시간 간격으로 시세 알림"""
        if not self.alert_channel_id:
            return
            
        try:
            channel = self.bot.get_channel(self.alert_channel_id)
            if not channel:
                return
                
            embed = await self.get_top_markets()
            await channel.send(embed=embed)
            
        except Exception as e:
            logging.error(f"시세 알림 중 오류 발생: {e}")

    @app_commands.command(name="코인알림설정", description="실시간 시세 알림을 받을 채널을 설정합니다")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_price_channel(self, interaction: discord.Interaction):
        """시세 알림 채널 설정"""
        self.alert_channel_id = interaction.channel.id
        
        embed = discord.Embed(
            title="✅ 시세 알림 채널 설정 완료",
            description="3시간 간격으로 비트코인과 거래대금 TOP 5 코인의 시세 정보가 전송됩니다.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📍 설정된 채널",
            value=interaction.channel.mention,
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="인기코인", description="거래대금 기준 TOP 5 코인과 비트코인 시세를 조회합니다")
    async def check_top_coins(self, interaction: discord.Interaction):
        """인기 코인 시세 조회"""
        await interaction.response.defer()
        
        try:
            embed = await self.get_top_markets()
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ 조회 실패",
                description="```시세 정보를 불러오는 중 오류가 발생했습니다.\n잠시 후 다시 시도해주세요.```",
                color=discord.Color.red()
            )
            logging.error(f"인기 코인 조회 중 오류: {e}")
            await interaction.followup.send(embed=error_embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Finance(bot))
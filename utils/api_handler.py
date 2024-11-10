import aiohttp
import asyncio

# API 요청 처리 클래스
class APIHandler:
    def __init__(self):
        self.session = None
    
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get(self, url, params=None):
        await self.init_session()
        async with self.session.get(url, params=params) as response:
            return await response.json()
    
    async def post(self, url, data=None):
        await self.init_session()
        async with self.session.post(url, json=data) as response:
            return await response.json()
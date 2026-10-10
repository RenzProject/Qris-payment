from Qris import get_session

async def get(url: str, *args, **kwargs):
    session = await get_session()
    
    async with session.get(url, *args, **kwargs) as resp:
        try:
            data = await resp.json()
        except Exception:
            data = await resp.text()
    return data

async def post(url: str, *args, **kwargs):
    session = await get_session()

    async with session.post(url, *args, **kwargs) as resp:
        try:
            data = await resp.json()
        except Exception:
            data = await resp.text()
    return data
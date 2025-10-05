import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from typing import TypedDict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import httpx
import uvicorn
from threading import Thread
import time

from keep_alive import keep_alive
from api import app

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Start the FastAPI server in a separate thread
def run_api():
    port = int(os.environ.get('API_PORT', 8001))  # Use different port from keep_alive
    uvicorn.run(app, host='0.0.0.0', port=port, log_level='error')

# Start both servers
keep_alive()
api_thread = Thread(target=run_api, daemon=True)
api_thread.start()

# Wait a moment for the API server to start
time.sleep(2)

logging.basicConfig(level=logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()

intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

class Prompt(TypedDict, total=False):
    id: str
    month: str
    week_in_month: int
    title: str
    time_hint: str
    tags: list[str]

BASE = f"http://localhost:{os.environ.get('API_PORT', 8001)}"

async def get_prompt_by_week(week: int) -> Optional[Prompt]:
    # clamp if your calendar rule can yield 53
    if week > 52:
        week = 52
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{BASE}/prompts/week/{week}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

def global_week(dt):
    doy = int(dt.strftime("%j"))           # 1..365 or 366
    return (doy - 1) // 7 + 1              # 1..53

@bot.event
async def on_ready():
    print("ready")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

@bot.command(name='start')
async def start(ctx):
    now_ny = datetime.now(ZoneInfo("America/New_York"))
    week = global_week(now_ny)
    prompt = await get_prompt_by_week(week)
    if not prompt:
        await ctx.send(f"No prompt found for week {week}")
        return
    await ctx.send(prompt["title"])

bot.run(token, log_handler=handler, log_level=logging.DEBUG)


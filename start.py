#!/usr/bin/env python3
"""
Startup script for the Photo Challenge Bot
This script handles the proper initialization and startup of all services
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if we have the required Discord token
if not os.getenv("DISCORD_TOKEN"):
    print("ERROR: DISCORD_TOKEN environment variable is required")
    sys.exit(1)

# Import and run the main bot
if __name__ == "__main__":
    from main import bot, token
    print("Starting Photo Challenge Bot...")
    print(f"Discord Bot: Ready to connect")
    print(f"Flask Keep-alive: Running on port {os.environ.get('PORT', 8000)}")
    print(f"FastAPI Server: Running on port {os.environ.get('API_PORT', 8001)}")
    bot.run(token)

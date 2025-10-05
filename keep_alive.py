from flask import Flask
from threading import Thread
import os

app= Flask('')

@app.route('/')
def home():
    return 'Bot is running'

def run():
    # Use Render's PORT environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
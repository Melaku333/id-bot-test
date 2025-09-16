import os
import threading
import http.server
import socketserver
import asyncio
from bot import dp, bot  # import dispatcher and bot from your bot.py

# Health server so Render knows the service is alive
def run_health_server():
    port = int(os.getenv("PORT", "8000"))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Health server listening on 0.0.0.0:{port}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Start health server in a separate thread
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    
    print("✅ Starting Telegram bot...")
    asyncio.run(dp.start_polling(bot))

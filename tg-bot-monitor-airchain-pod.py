import asyncio
import aiohttp
from telegram import Bot
from telegram.error import NetworkError
from telegram.request import HTTPXRequest
from datetime import datetime, timedelta

# Telegram Bot Token and Chat ID
TELEGRAM_BOT_TOKEN = ''  # Token
CHAT_ID = ''  # Chat ID

# Proxy URL and flag
PROXY_URL = 'http://localhost:7890'  # Replace with your proxy URL
USE_PROXY = False  # Set to True to use proxy, False otherwise

# Record the latest pod information and update time for each station
station_status = {}

async def send_message_async(bot_token, chat_id, text, use_proxy, proxy_url):
    request = HTTPXRequest(proxy=proxy_url) if use_proxy else HTTPXRequest()
    bot = Bot(token=bot_token, request=request)
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        print("Message sent successfully!")
    except NetworkError as e:
        print(f"Network error occurred: {e}")

async def get_station_data(session, station_id, use_proxy, proxy_url):
    url = "https://testnet.airchains.io/api/stations/single-station/details"
    data = {"stationID": station_id}
    proxy = proxy_url if use_proxy else None
    async with session.post(url, json=data, proxy=proxy) as response:
        if response.status == 200:
            result = await response.json()
            if result['status']:
                latest_pod = result['data']['latestPod']
                now = datetime.now()
                station_id_short = station_id[-4:]  # Retain only the last 4 characters of station_id

                if station_id in station_status:
                    previous_pod, last_update = station_status[station_id]

                    # Check if there has been no change for a long time
                    if latest_pod == previous_pod and now - last_update > timedelta(minutes=5):  # Assume 5 minutes without change
                        message = f"StationID: {station_id_short} - LatestPod: {latest_pod} (No change for 5 minutes!)"
                    else:
                        message = f"StationID: {station_id_short} - LatestPod: {latest_pod}"
                else:
                    message = f"StationID: {station_id_short} - LatestPod: {latest_pod}"

                # Update status
                station_status[station_id] = (latest_pod, now)
                return message
            else:
                return f"StationID: {station_id_short} - Error: {result['message']}"
        else:
            return f"StationID: {station_id_short} - HTTP Error: {response.status}"

async def monitor_stations(station_ids, interval, bot_token, chat_id, use_proxy, proxy_url):
    connector = aiohttp.TCPConnector(ssl=False)  # Skip SSL verification if needed
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            tasks = [get_station_data(session, station_id, use_proxy, proxy_url) for station_id in station_ids]
            results = await asyncio.gather(*tasks)
            message = "\n".join(results)
            await send_message_async(bot_token, chat_id, message, use_proxy, proxy_url)
            print("Message sent to Telegram Bot")
            print("---------------")
            await asyncio.sleep(interval)

if __name__ == "__main__":
    station_ids = [
        "xxxxxxxx-xxxx-xxxx-xxx-xxxx",
    ]
    asyncio.run(monitor_stations(station_ids, interval=300, bot_token=TELEGRAM_BOT_TOKEN, chat_id=CHAT_ID, use_proxy=USE_PROXY, proxy_url=PROXY_URL))  # Request every 300 seconds

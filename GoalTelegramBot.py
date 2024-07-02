import asyncio
import os
from app.db.mongo import MongoDB
from dotenv import load_dotenv
from pymongo.errors import PyMongoError
import telebot
from telebot.async_telebot import AsyncTeleBot

load_dotenv()

class GoalTelegramBot:
    def __init__(self):
        mongodb_uri = os.getenv('MONGODB_URI')
        mongodb_db_name = os.getenv('MONGODB_DB_NAME')
        self.mongodb_client = MongoDB(mongodb_uri, mongodb_db_name)
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.group_id = os.getenv('TELEGRAM_GROUP_ID')
        self.bot = AsyncTeleBot(self.bot_token, parse_mode='HTML')  # Using HTML parse mode for formatting
        self.last_scores = {}

    async def check_for_goals(self):
        try:
            data = self.mongodb_client.read('goal_data', {})
            for league in data:
                for match in league['matches']:
                    match_id = f"{match['เจ้าบ้าน']} vs {match['ทีมเยือน']}"
                    current_score = match['ผลบอล']
                    
                    if match_id in self.last_scores and self.last_scores[match_id] != current_score:
                        await self.send_goal_notification(league['league'], match)
                    
                    self.last_scores[match_id] = current_score
                    
                    print(f"Checking for goals: {match['เจ้าบ้าน']} vs {match['ทีมเยือน']}")
        except PyMongoError as e:
            print(f"Error reading from database: {str(e)}")

    async def send_goal_notification(self, league, match):
        message = self.create_table_message(league, match)
        try:
            await self.bot.send_message(chat_id=self.group_id, text=message, parse_mode='HTML')
            print(f"Telegram message sent successfully for {match['เจ้าบ้าน']} vs {match['ทีมเยือน']}")
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")

    def create_table_message(self, league, match):
        message = f"<b>🚨 Goal Alert! 🚨</b>\n\n"
        message += f"<pre>"
        message += f"┌──────────────────────────────┐\n"
        message += f"│ League: {league: <24}│\n"
        message += f"├──────────────────────────────┤\n"
        message += f"│ {match['เจ้าบ้าน']: <14} vs {match['ทีมเยือน']: <13}│\n"
        message += f"│ Score: {match['ผลบอล']: <24}│\n"
        message += f"│ Time: {match['เวลา']: <25}│\n"
        message += f"└──────────────────────────────┘"
        message += f"</pre>"
        return message

    async def run(self):
        while True:
            await self.check_for_goals()
            await asyncio.sleep(60)  # Check every minute

async def main():
    bot = GoalTelegramBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
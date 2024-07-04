import asyncio
from itertools import groupby
import os
from db.mongo import MongoDB
from dotenv import load_dotenv
from pymongo.errors import PyMongoError
import telebot
from telebot.async_telebot import AsyncTeleBot
from datetime import datetime, timedelta
import pytz

load_dotenv()

class GoalTelegramBot:
    def __init__(self):
        mongodb_uri = os.getenv('MONGODB_URI')
        mongodb_db_name = os.getenv('MONGODB_DB_NAME')
        self.mongodb_client = MongoDB(mongodb_uri, mongodb_db_name)
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.group_id = os.getenv('TELEGRAM_GROUP_ID')
        self.bot = AsyncTeleBot(self.bot_token, parse_mode='HTML')
        self.last_scores = {}
        self.last_schedule_date = None
        self.first_match_started = False

    async def check_first_match(self):
        try:
            bangkok_tz = pytz.timezone('Asia/Bangkok')
            now = datetime.now(bangkok_tz)
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)

            first_match = self.mongodb_client.db['matches_data'].find_one({
                'date': {'$gte': today}
            }, sort=[('date', 1)])

            if first_match and first_match['date'] <= now:
                self.first_match_started = True
                print(f"First match of the day has started: {first_match['home_team']} vs {first_match['away_team']}")
            else:
                self.first_match_started = False
                print("First match of the day hasn't started yet.")
        except PyMongoError as e:
            print(f"Error checking first match: {str(e)}")

    async def check_for_goals(self):
        if not self.first_match_started:
            print("Skipping goal check as first match hasn't started yet.")
            return

        try:
            now = datetime.now(pytz.UTC)
            one_day_ago = now - timedelta(days=1)
            
            matches = self.mongodb_client.db['matches_data'].find({
                'date': {'$gte': one_day_ago, '$lte': now}
            }).sort('date', 1)

            for match in matches:
                match_id = match['_id']
                current_score = match['score']

                if match_id in self.last_scores and self.last_scores[match_id] != current_score:
                    await self.send_goal_notification(match)
                
                self.last_scores[match_id] = current_score
                
                print(f"Checking for goals: {match['home_team']} vs {match['away_team']}")
        except PyMongoError as e:
            print(f"Error reading from database: {str(e)}")

    async def send_goal_notification(self, match):
        message = self.create_table_message(match)
        try:
            await self.bot.send_message(chat_id=self.group_id, text=message, parse_mode='HTML')
            print(f"Telegram message sent successfully for {match['home_team']} vs {match['away_team']}")
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")

    def create_table_message(self, match):
        score_parts = match['score'].split(' - ')
        home_score = int(score_parts[0]) if len(score_parts) > 0 and score_parts[0].isdigit() else 0
        away_score = int(score_parts[1]) if len(score_parts) > 1 and score_parts[1].isdigit() else 0
        
        previous_score_parts = match['previous_score'].split(' - ')
        previous_home_score = int(previous_score_parts[0]) if len(previous_score_parts) > 0 and previous_score_parts[0].isdigit() else 0
        previous_away_score = int(previous_score_parts[1]) if len(previous_score_parts) > 1 and previous_score_parts[1].isdigit() else 0
        
        goal_message = ""
        if home_score > previous_home_score:
            goal_message = f"🎉 {match['home_team']} ทำประตู! 🎉"
        elif away_score > previous_away_score:
            goal_message = f"🎉 {match['away_team']} ทำประตู! 🎉"
        
        base_message = (
            f"<b>{match['league']}</b>\n\n"
            f"⚽️ <b>{match['home_team']}</b> vs <b>{match['away_team']}</b>\n\n"
            f"📊 <b>Score:</b>\n"
            f"    <code>{match['home_team'][:15]: <15}</code> {home_score}\n"
            f"    <code>{match['away_team'][:15]: <15}</code> {away_score}\n\n"
            f"💰 <b>ราคาบอล:</b> {match['odds']}\n"
            f"🕒 <b>ทรรศนะฟุตบอลวันนี้:</b> {match['signal']}\n\n"
            f"🕒 <b>เริ่มเตะ:</b> {match['bangkok_time']}"
        )

        if goal_message:
            message = f"🚨 <b>GOAL ALERT!</b> 🚨\n\n{goal_message}\n\n{base_message}"
        else:
            message = f"⚽ <b>MATCH UPDATE</b> ⚽\n\n{base_message}"

        message += f"\n\n#FootballAlert #LiveScore"
        
        return message
    
    async def send_daily_schedule(self):
        try:
            bangkok_tz = pytz.timezone('Asia/Bangkok')
            now = datetime.now(bangkok_tz)
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)

            matches = list(self.mongodb_client.db['matches_data'].find({
                'date': {'$gte': today}
            }).sort([('league', 1), ('date', 1)]))

            grouped_matches = groupby(matches, key=lambda x: x['league'])

            for league, league_matches in grouped_matches:
                message = self.create_daily_schedule_message(league, list(league_matches))
                await self.bot.send_message(chat_id=self.group_id, text=message, parse_mode='HTML')
                print(f"Daily schedule for {league} sent successfully")
                await asyncio.sleep(1)  # Add a small delay between messages

            print("All league schedules sent successfully")
            self.last_schedule_date = now.date()
        except Exception as e:
            print(f"Error sending daily schedules: {str(e)}")

    def create_daily_schedule_message(self, league, matches):
        message = f"📅 <b>ตารางการแข่งขันฟุตบอลวันนี้</b> 📅\n"
        message += f"<code>{league}</code>\n\n"

        for match in matches:
            message += (
                f"<code>"
                f"🏠 <b>ทีมเหย้า:</b> {match['home_team']}\n"
                f"🛫 <b>ทีมเยือน:</b> {match['away_team']}\n"
                f"⚽ <b>ผลการแข่งขัน:</b> {match['score']}\n"
                f"💰 <b>ราคาบอล:</b> {match['odds']}\n"
                f"🔮 <b>ทรรศนะฟุตบอลวันนี้:</b> {match.get('signal', 'ไม่มีข้อมูล')}\n"
                f"🕒 <b>เวลาเตะ:</b> {match['bangkok_time']}\n"
                f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                f"</code>\n"
            )

        message += f"#{league.replace(' ', '')}\n\n"
        return message

    async def run(self):
        while True:
            await self.check_first_match()
            await self.check_for_goals()
            
            bangkok_tz = pytz.timezone('Asia/Bangkok')
            now = datetime.now(bangkok_tz)
            
            if now.hour == 12 and now.minute == 0 and (self.last_schedule_date is None or self.last_schedule_date < now.date()):
                await self.send_daily_schedule()

            await asyncio.sleep(60)  # Check every minute

async def main():
    bot = GoalTelegramBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
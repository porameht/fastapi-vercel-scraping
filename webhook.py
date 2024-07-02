import asyncio
import os
from app.db.mongo import MongoDB
from dotenv import load_dotenv
import aiohttp
from pymongo.errors import PyMongoError

load_dotenv()

class GoalWebhook:
    def __init__(self):
        mongodb_uri = os.getenv('MONGODB_URI')
        mongodb_db_name = os.getenv('MONGODB_DB_NAME')
        self.mongodb_client = MongoDB(mongodb_uri, mongodb_db_name)
        self.webhook_url = os.getenv('WEBHOOK_URL')
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
        except PyMongoError as e:
            print(f"Error reading from database: {str(e)}")

    async def send_goal_notification(self, league, match):
        message = (f"Goal Alert!\n"
                   f"League: {league}\n"
                   f"Match: {match['เจ้าบ้าน']} vs {match['ทีมเยือน']}\n"
                   f"New Score: {match['ผลบอล']}\n"
                   f"Time: {match['เวลา']}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.webhook_url, json={'content': message}) as response:
                    if response.status == 204:
                        print(f"Webhook sent successfully for {match['เจ้าบ้าน']} vs {match['ทีมเยือน']}")
                    else:
                        print(f"Failed to send webhook. Status: {response.status}")
            except aiohttp.ClientError as e:
                print(f"Error sending webhook: {str(e)}")

    async def run(self):
        while True:
            await self.check_for_goals()
            await asyncio.sleep(60)  # Check every minute

async def main():
    webhook = GoalWebhook()
    await webhook.run()

if __name__ == "__main__":
    asyncio.run(main())
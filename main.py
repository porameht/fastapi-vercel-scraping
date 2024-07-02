import asyncio
from collections import defaultdict
from datetime import datetime

import pymongo
import pytz
from app.db.mongo import MongoDB
from pymongo import UpdateOne

from dotenv import load_dotenv
import os
from app.scrapper import goal

load_dotenv()

class GoalWorker:
    def __init__(self):
        mongodb_uri = os.getenv('MONGODB_URI')
        mongodb_db_name = os.getenv('MONGODB_DB_NAME')
        self.mongodb_client = MongoDB(mongodb_uri, mongodb_db_name)
        self.mongodb_client.db['matches_data'].create_index([('_id', 1), ('date', 1), ('league', 1)], unique=True)

    async def process_goal_data(self):
        try:
            data = goal()
            await self.save_matches(data)
            print(f"Processed {len(data)} items")
        except Exception as e:
            print(f"Error processing goal data: {str(e)}")
            
    async def save_matches(self, data):
        try:
            bangkok_tz = pytz.timezone('Asia/Bangkok')
            current_date = datetime.now(bangkok_tz).strftime("%Y-%m-%d")
            matches_updates = []
            match_counts = defaultdict(int)  # To keep track of match order for each league

            for league_index, item in enumerate(data, start=1):
                leagues_name = item['leagues']
                matches = item['matches']

                for match in matches:
                    match_counts[league_index] += 1
                    match_order = match_counts[league_index]
                    
                    try:
                        match_time = datetime.strptime(match['เวลา'], "%H:%M")
                        bangkok_match_time = bangkok_tz.localize(match_time.replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day))
                        bangkok_match_time_str = bangkok_match_time.strftime('%d%m%Y_%H%M')
                    except ValueError as e:
                        print(f"Error parsing time for match: {match}. Error: {e}")
                        continue

                    match_id = f"{bangkok_match_time_str}_{league_index:02d}_{match_order:02d}"

                    matches_updates.append(UpdateOne(
                        {'_id': match_id, 'date': current_date, 'league': leagues_name},
                        {'$set': {
                            'home_team': match['เจ้าบ้าน'],
                            'away_team': match['ทีมเยือน'],
                            'score': match['ผลบอล'],
                            'time': match['เวลา'],
                            'bangkok_time': bangkok_match_time.strftime("%H:%M"),
                            'league_order': league_index,
                            'match_order': match_order,
                            'updated_at': datetime.now(pytz.UTC),
                        },
                        '$setOnInsert': {
                            'created_at': datetime.now(pytz.UTC),
                        }},
                        upsert=True
                    ))

            print(f"Saving {len(matches_updates)} matches data to database")
            # Split matches updates into chunks to avoid hitting BSON size limit
            chunk_size = 100
            for i in range(0, len(matches_updates), chunk_size):
                chunk = matches_updates[i:i + chunk_size]
                matches_result = self.mongodb_client.db['matches_data'].bulk_write(chunk)
                print(f"Matches data chunk {i//chunk_size + 1}: {matches_result.upserted_count} inserted, {matches_result.modified_count} modified")

        except Exception as e:
            print(f"Error saving leagues and matches data to database: {str(e)}")


    async def run(self):
        while True:
            await self.process_goal_data()
            await asyncio.sleep(30)  # Sleep for 5 minutes (300 seconds)

async def main():
    worker = GoalWorker()
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
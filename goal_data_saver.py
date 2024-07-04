import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import pytz
from pymongo import UpdateOne
from db.mongo import MongoDB
from dotenv import load_dotenv
import os
from scrapper import goal

load_dotenv()

class GoalDataSaver:
    def __init__(self):
        mongodb_uri = os.getenv('MONGODB_URI')
        mongodb_db_name = os.getenv('MONGODB_DB_NAME')
        self.mongodb_client = MongoDB(mongodb_uri, mongodb_db_name)
        self.mongodb_client.db['matches_data'].create_index([('_id', 1), ('date', 1), ('league', 1)], unique=True)
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
        except Exception as e:
            print(f"Error checking first match: {str(e)}")

    async def save_matches(self, data):
        try:
            bangkok_tz = pytz.timezone('Asia/Bangkok')
            matches_updates = []
            previous_score_updates = []
            match_counts = defaultdict(int)  # To keep track of match order for each league

            for league_index, item in enumerate(data, start=1):
                leagues_name = item['leagues']
                matches = item['matches']
                date = datetime.strptime(item['date'], "%Y-%m-%dT%H:%M:%S.%fZ")

                for match in matches:
                    match_counts[league_index] += 1
                    match_order = match_counts[league_index]
                    
                    try:
                        match_time = datetime.strptime(match['เวลา'], "%H:%M")
                        bangkok_match_datetime = bangkok_tz.localize(datetime.combine(date.date(), match_time.time()))
                        utc_match_datetime = bangkok_match_datetime.astimezone(pytz.UTC)
                        bangkok_match_time_str = bangkok_match_datetime.strftime('%d%m%Y_%H%M')
                        
                        thai_time_datetime = utc_match_datetime + timedelta(hours=7)  # เพิ่มเวลา 7 ชั่วโมง
                    except ValueError as e:
                        print(f"Error parsing time for match: {match}. Error: {e}")
                        continue

                    match_id = f"{bangkok_match_time_str}_{league_index:02d}_{match_order:02d}"

                    # First operation: Update previous_score if necessary
                    previous_score_updates.append(UpdateOne(
                        {'_id': match_id, 'league': leagues_name, 'score': {'$ne': match['ผลบอล']}},
                        {'$set': {'previous_score': '$score'}},
                        upsert=False
                    ))

                    # Second operation: Update match data
                    matches_updates.append(UpdateOne(
                        {'_id': match_id, 'league': leagues_name},
                        {'$set': {
                            'date': thai_time_datetime,
                            'home_team': match['เจ้าบ้าน'],
                            'away_team': match['ทีมเยือน'],
                            'odds': match['ราคาบอล'],
                            'score': match['ผลบอล'],
                            'time': match['เวลา'],
                            'bangkok_time': bangkok_match_datetime.strftime("%H:%M"),
                            'league_order': league_index,
                            'match_order': match_order,
                            'signal': match['ทรรศนะฟุตบอลวันนี้'],
                            'updated_at': datetime.now(pytz.UTC) + timedelta(hours=7),
                        },
                        '$setOnInsert': {
                            'created_at': datetime.now(pytz.UTC) + timedelta(hours=7),
                            'previous_score': '0 - 0',
                        }},
                        upsert=True
                    ))

            # Execute previous_score updates
            if previous_score_updates:
                previous_score_result = self.mongodb_client.db['matches_data'].bulk_write(previous_score_updates)
                print(f"Previous score updates: {previous_score_result.modified_count} modified")

            # Execute match data updates
            print(f"Saving {len(matches_updates)} matches data to database")
            chunk_size = 100
            for i in range(0, len(matches_updates), chunk_size):
                chunk = matches_updates[i:i + chunk_size]
                matches_result = self.mongodb_client.db['matches_data'].bulk_write(chunk)
                print(f"Matches data chunk {i//chunk_size + 1}: {matches_result.upserted_count} inserted, {matches_result.modified_count} modified")

        except Exception as e:
            print(f"Error saving leagues and matches data to database: {str(e)}")

    async def run(self):
        while True:
            try:
                await self.check_first_match()
                if self.first_match_started:
                    data = goal(0)
                    await self.save_matches(data)
                    print(f"Processed {len(data)} items")
                    await asyncio.sleep(30)  # Sleep for 30 seconds if first match has started
                else:
                    print("Waiting for the first match to start...")
                    await asyncio.sleep(1800)  # Sleep for 30 minutes if first match hasn't started
            except Exception as e:
                print(f"Error processing goal data: {str(e)}")
                await asyncio.sleep(30)  # Sleep for 30 seconds in case of error

if __name__ == "__main__":
    saver = GoalDataSaver()
    asyncio.run(saver.run())
import asyncio
from goal_data_saver import GoalDataSaver
from goal_telegram_bot import GoalTelegramBot

async def run_data_saver():
    saver = GoalDataSaver()
    await saver.run()

async def run_telegram_bot():
    bot = GoalTelegramBot()
    await bot.run()

async def main():
    # Run both processes concurrently
    await asyncio.gather(
        run_data_saver(),
        run_telegram_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())
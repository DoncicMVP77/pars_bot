import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import BotBlocked


from new_scrapper import check_new_products
from db_service import DB

logging.basicConfig(level=logging.INFO)


bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot)

db = DB('db.db')


@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    if not db.subscriber_exists(message.from_user.id):
        db.add_subscriber(message.from_user.id)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, True)

    await message.answer("Вы успешно подписались на рассылку!")


@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    if not db.subscriber_exists(message.from_user.id):
        db.add_subscriber(message.from_user.id, False)
        await message.answer("Вы итак не подписаны.")
    else:
        db.update_subscription(message.from_user.id, False)
        await message.answer('Вы успешно отписаны от рассылки.')


@dp.message_handler(commands=['fresh_news'])
async def get_fresh_news(message: types.Message):
    new_products = check_new_products()

    if len(new_products) >= 1:
        for k, v in sorted(new_products.items()):
            news = f"{v['link']}"

            await message.answer(news)
    else:
        await message.answer("No new products")


async def news_every_minute():
    while True:
        new_products = check_new_products()
        if new_products is not None:
            if len(new_products) >= 1:
                for k, v in sorted(new_products.items()):
                    news = f"{v['link']}"

                    subscriptions = db.get_subscriptions()
                    for s in subscriptions:
                        try:
                            await bot.send_message(s[0], news,
                                                   disable_notification=False)
                        except BotBlocked:
                            print('Bot was blocked')
                            continue
                        except:
                            pass

            await asyncio.sleep(5)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(news_every_minute())
    executor.start_polling(dp, skip_updates=True)

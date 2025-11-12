from aiogram import Bot, Dispatcher, types
from hi import ADMIN_BOT_TOKEN
from product_p import get_all_orders
import asyncio

bot = Bot(token='8210815132:AAHNb7qOuwZt8bZs3ZMFQi0s5Bym7e1dLCI')
dp = Dispatcher()

@dp.message()
async def admin_panel(message: types.Message):
    orders = get_all_orders()
    if not orders:
        await message.answer("Hozircha buyurtmalar yo'q.")
        return

    msg = ""
    summary = {}
    total_sum = 0

    for o in orders:
        msg += f"{o['customer_name']} | {o['bread_type']} | {o['quantity']} | {o['order_time'].strftime('%H:%M')} | {o['price']} so'm\n"
        summary[o['bread_type']] = summary.get(o['bread_type'], 0) + o['quantity']
        total_sum += o['price']

    msg += "\n---Summary---\n"
    for bread, qty in summary.items():
        msg += f"{bread}: {qty} dona\n"
    msg += f"Umumiy pul: {total_sum} so'm"

    await message.answer(msg)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

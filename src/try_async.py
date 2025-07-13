import asyncio

async def count_down(number: int):
    while number > 0:
        print(f"Countdown: {number}")
        await asyncio.sleep(1)
        number -= 1

async def count_up(stop: int):
    number = 0
    while number < stop:
        print(f"Countup: {number}")
        await asyncio.sleep(0.75)
        number += 1

async def main():
    await asyncio.gather(
        count_down(5),
        count_up(5)
    )

asyncio.run(main())
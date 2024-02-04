import platform
import aiohttp
import asyncio
import sys
from datetime import date, timedelta


def prepare_day_list(daysback):
    today = date.today()
    if daysback > 10:
        print("Currency rate check limited to 10 days back")
        daysback = 10
    return [str(today - timedelta(days=n)) for n in range(daysback + 1)]


async def get_page(day, session):
    async with session.get(
        f"https://api.nbp.pl/api/exchangerates/tables/a/{day}?format=json"
    ) as response:
        print("Status:", response.status)
        print("Content-type:", response.headers["content-type"])

        html = await response.text()
        return f"Body: {html[:150]}..."


async def main():
    try:
        daysback = int(sys.argv[1])

        days = prepare_day_list(daysback)
        print(days)

    except ValueError as err:
        print(str(err), "\nArgument should be (int)")
        return -1
    except IndexError as err:
        print(str(err), "\nPlease provide at least one argument (int)")
        return -1

    async with aiohttp.ClientSession() as session:
        result = await asyncio.gather(
            get_page(days[0], session),
            get_page(days[1], session),
            get_page(days[2], session),
        )
        return result


if __name__ == "__main__":

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r = asyncio.run(main())
    print(r)

import platform
import aiohttp
import asyncio
import sys
import json
from datetime import date, timedelta


def prepare_day_list(daysback):
    today = date.today()
    # today = date(year=2024, month=2, day=1)  # testing
    if daysback > 10:
        print("Currency exchange-rate check limited to 10 days back")
        daysback = 10
    return [str(today - timedelta(days=n)) for n in range(daysback + 1)]


async def get_page(day, session):
    try:
        async with session.get(
            f"https://api.nbp.pl/api/exchangerates/tables/c/{day}?format=json"
        ) as response:
            print("Status:", response.status)
            if response.status == 200:
                response_json = await response.json()
                return response_json
                # return json.dumps(response_json, indent=4)
            else:
                return json.dumps({day: "No exchange rates for this day"})
    except aiohttp.ClientConnectorError as err:
        print(
            f"Connection error when asking nbp API for currency rates from {day}",
            str(err),
        )


async def main():

    if len(sys.argv) > 1:
        try:
            daysback = int(sys.argv[1])
            days = prepare_day_list(daysback)
            print(days)

        except ValueError as err:
            print(str(err), "\nArgument should be (int)")
            return -1
    else:
        days = prepare_day_list(0)

    async with aiohttp.ClientSession() as session:
        result = await asyncio.gather(*[get_page(day, session) for day in days])

        return result


if __name__ == "__main__":

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r = asyncio.run(main())
    print(*r)
    # print(json.dumps(r, indent=4))

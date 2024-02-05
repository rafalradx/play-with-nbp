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


async def get_currency_exchange_rate(day, session):
    try:
        async with session.get(
            f"https://api.nbp.pl/api/exchangerates/tables/c/{day}?format=json"
        ) as response:
            print("Status:", response.status)
            if response.status == 200:
                data = await response.json()  # API returns list
                return {day: data[0]}
            else:
                return {day: None}
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
        result = await asyncio.gather(
            *[get_currency_exchange_rate(day, session) for day in days]
        )

        return result


if __name__ == "__main__":

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    results = asyncio.run(main())

    merged_results = {}
    for result in results:
        merged_results.update(result)

    currency_codes = {"EUR", "USD"}
    if len(sys.argv) > 2:
        additional_codes = {code.upper() for code in sys.argv[2:]}
        currency_codes.update(additional_codes)

    print(currency_codes)

    exchange_rates = []
    for day, rate_data in merged_results.items():
        if rate_data is None:
            exchange_rates.append({day: "No exchange rates available"})
        else:
            selected_currencies = list(
                filter(lambda x: x["code"] in currency_codes, rate_data["rates"])
            )
            reformated = {
                curr["code"]: {"sale": curr["ask"], "purchase": curr["bid"]}
                for curr in selected_currencies
            }
            exchange_rates.append({day: reformated})

    print(json.dumps(exchange_rates, indent=4))

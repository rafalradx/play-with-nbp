import platform
import aiohttp
import asyncio
import sys
import json
from datetime import date, timedelta


class NBPCurrencyRateRetriever:
    """startDate, endDate format 2024-02-02"""

    def __init__(
        self, startDate: str, endDate: str, currency_codes={"EUR", "USD"}
    ) -> None:

        self.currency_codes = currency_codes
        self.startDate = startDate
        self.endDate = endDate

    async def get_currency_rate_period(self, startDate, endDate, session, table="c"):
        """table: a - average currency exchange rate; b - ???; c - sale and purchase currency rates"""
        if startDate == endDate:
            get_string = f"https://api.nbp.pl/api/exchangerates/tables/{table}/{startDate}?format=json"
        else:
            get_string = f"http://api.nbp.pl/api/exchangerates/tables/{table}/{startDate}/{endDate}/?format=json"

        try:
            async with session.get(get_string) as response:
                if response.status == 200:
                    data = await response.json()  # NBP API returns list
                    return data
                else:
                    return None
        except aiohttp.ClientConnectorError as err:
            print(
                f"Connection error when asking nbp API for currency rates from",
                str(err),
            )

    async def send_request_nbp(self):

        async with aiohttp.ClientSession() as session:

            result = await asyncio.gather(
                self.get_currency_rate_period(
                    self.startDate, self.endDate, session, table="c"
                )
            )
            return result

    def run(self):
        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        results = asyncio.run(self.send_request_nbp())
        return self.pretty_output(results)

    def pretty_output(self, nbp_data) -> str:
        if nbp_data[0] is None:
            return "No data available"
        merged_results = {
            result["effectiveDate"]: result["rates"] for result in nbp_data[0]
        }
        exchange_rates = []
        for day, rate_data in merged_results.items():
            if rate_data is None:
                exchange_rates.append({day: "No exchange rates available"})
            else:
                selected_currencies = list(
                    filter(lambda x: x["code"] in self.currency_codes, rate_data)
                )
                reformated = {
                    curr["code"]: {"sale": curr["ask"], "purchase": curr["bid"]}
                    for curr in selected_currencies
                }
                exchange_rates.append({day: reformated})
        return json.dumps(exchange_rates, indent=4)


def prepare_dates(daysback):
    today = date.today()
    endDate = str(today)
    if daysback > 10:
        print("Currency exchange-rate check limited to 10 days back")
        daysback = 10
    startDate = str(today - timedelta(days=daysback))
    return startDate, endDate


if __name__ == "__main__":

    if len(sys.argv) == 1:
        startDate, endDate = prepare_dates(0)

    if len(sys.argv) > 1:
        try:
            daysback = int(sys.argv[1])
            startDate, endDate = prepare_dates(daysback)
        except ValueError as err:
            print(str(err), "\nArgument should be (int)")

    currency_codes = {"EUR", "USD"}
    if len(sys.argv) > 2:
        additional_codes = {code.upper() for code in sys.argv[2:]}
        currency_codes.update(additional_codes)

    NBPRetriever = NBPCurrencyRateRetriever(
        startDate, endDate, currency_codes=currency_codes
    )

    output = NBPRetriever.run()

    print(output)

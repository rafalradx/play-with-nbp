import asyncio
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
import nbpreq as nbp

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            m_splitted = message.strip().lower().split()
            if m_splitted[0] == "exchange":
                if len(m_splitted) == 1:
                    daysback = 0
                else:
                    try:
                        daysback = int(m_splitted[1])
                    except ValueError as err:
                        response = "\nArgument for 'exchange' should be (int)"
                startDate, endDate = nbp.NBPCurrencyRateRetriever.prepare_dates(
                    daysback
                )
                currency_codes = nbp.NBPCurrencyRateRetriever.prepare_codes()
                if len(m_splitted) > 2:
                    currency_codes = nbp.NBPCurrencyRateRetriever.prepare_codes(
                        m_splitted[2:]
                    )
                NBPRetriever = nbp.NBPCurrencyRateRetriever(
                    startDate=startDate, endDate=endDate, currency_codes=currency_codes
                )
                results = await NBPRetriever.send_request_nbp()
                response = NBPRetriever.pretty_output(results)
                await self.send_to_clients(f"{' '.join(m_splitted)}: {response}")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())

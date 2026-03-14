import asyncio
from utils.tatum import check_ltc_transaction

async def test_api():
    # Replace with a real address and amount if you want to test live integration
    # Or mock the aiohttp response in utils/tatum.py for testing
    address = "ltc1qxxxxxx"
    amount = 0.05
    timestamp = 1700000000
    
    print(f"Checking transaction for {address}...")
    result = await check_ltc_transaction(address, amount, timestamp)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_api())

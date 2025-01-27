import os
import asyncio
from planet.clients.quota import QuotaClient


async def get_my_products(client: QuotaClient):
    products = await client.get_my_products(organization_id=1)
    print("products:", products)
    return products


async def estimate_reservation(client: QuotaClient):
    estimate_payload = {
        "aoi_refs": [
            "pl:features/my/8k_iowa_fields-JvV1kZY/191522006971610-oxABerg",
            "pl:features/my/8k_iowa_fields-JvV1kZY/191522007502907-07PEybm"
        ],
        "product_id":
        8636
    }
    estimate = await client.estimate_reservation(estimate_payload)
    print("Reservation estimate:", estimate)
    return estimate


async def create_reservation(client: QuotaClient):
    create_payload = {
        "aoi_refs": [
            "pl:features/my/8k_iowa_fields-JvV1kZY/191522006971610-oxABerg",
            "pl:features/my/8k_iowa_fields-JvV1kZY/191522007502907-07PEybm"
        ],
        "product_id":
        8636
    }
    created_reservation = await client.create_reservation(create_payload)
    print("Created Reservation:", created_reservation)
    return created_reservation


async def get_reservations(client: QuotaClient):
    reservations = await client.get_reservations(limit=10)
    print("Reservations:", reservations)
    return reservations


async def create_bulk_reservations(client: QuotaClient):
    create_payload = {
        "aoi_refs": [
            "pl:features/my/8k_iowa_fields-JvV1kZY/191522004869934-on4GBM0",
            "pl:features/my/8k_iowa_fields-JvV1kZY/191522004552108-g8W4eYo",
            "pl:features/my/8k_iowa_fields-JvV1kZY/191522004545840-gqGrQym"
        ],
        "product_id":
        8636
    }
    job_details = await client.create_bulk_reservations(create_payload)
    print("Job details:", job_details)
    return job_details


async def get_bulk_reservation_job(client: QuotaClient, job_id: int):
    job = await client.get_bulk_reservation_job(job_id)
    print("job:", job)
    return job


async def main():
    api_key = os.getenv('PLANET_API_KEY', '')
    client = QuotaClient(api_key=api_key)

    await get_my_products(client)
    # await estimate_reservation(client)
    # await create_reservation(client)
    # await get_reservations(client)
    # await create_bulk_reservations(client)
    # await get_bulk_reservation_job(client, job_id=179)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from planet.clients.quota import QuotaClient
import os

async def main():
    api_key = os.getenv('PLANET_API_KEY', '')
    client = QuotaClient(api_key=api_key)

    
    '''
    # Test get_my_products
    products = await client.get_my_products(organization_id=1)
    print("products:", products)

    # Test estimate_reservation
    estimate_payload = {
       "aoi_refs": ["pl:features/my/8k_iowa_fields-JvV1kZY/191522006971610-oxABerg","pl:features/my/8k_iowa_fields-JvV1kZY/191522007502907-07PEybm"],
       "product_id": 8636
    }
    estimate = await client.estimate_reservation(estimate_payload)
    print("Reservation estimate:", estimate)

    # Test create_reservation
    create_payload = {
       "aoi_refs": ["pl:features/my/8k_iowa_fields-JvV1kZY/191522006971610-oxABerg","pl:features/my/8k_iowa_fields-JvV1kZY/191522007502907-07PEybm"],
       "product_id": 8636
    }
    created_reservation = await client.create_reservation(create_payload)
    print("Created Reservation:", created_reservation)

    # Test get_reservations
    reservations = await client.get_reservations(limit=10)
    print("Reservations:", reservations)

    # Test create_bulk_reservations
    create_payload = {
       "aoi_refs": ["pl:features/my/8k_iowa_fields-JvV1kZY/191522004869934-on4GBM0","pl:features/my/8k_iowa_fields-JvV1kZY/191522004552108-g8W4eYo","pl:features/my/8k_iowa_fields-JvV1kZY/191522004545840-gqGrQym"],
       "product_id": 8636
    }
    job_details = await client.create_bulk_reservations(create_payload)
    print("Job details:", job_details)

    # Test get_bulk_reservation_job
    job = await client.get_bulk_reservation_job(179)
    print("job:", job)
    '''



if __name__ == "__main__":
    asyncio.run(main())
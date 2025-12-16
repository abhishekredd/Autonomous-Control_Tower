import asyncio

from app.services.risk_service import RiskService
from app.core.database import AsyncSessionLocal

async def main(shipment_id: int = 11):
    rs = RiskService()
    async with AsyncSessionLocal() as session:
        res = await rs.assess_shipment(shipment_id, session)
        print('Persisted risks count:', len(res))
        for r in res:
            print('Risk:', r.id, r.risk_type, r.description)

if __name__ == '__main__':
    import sys
    sid = int(sys.argv[1]) if len(sys.argv) > 1 else 11
    asyncio.run(main(sid))

import os
from sqlalchemy import create_engine, text

url = os.environ.get('DATABASE_URL')
print('DATABASE_URL=', url)
engine = create_engine(url)
with engine.connect() as conn:
    for t in ['risks','simulations','shipments']:
        print('\nTABLE', t)
        rs = conn.execute(text("select column_name,data_type,udt_name from information_schema.columns where table_name=:t order by ordinal_position"), {'t': t})
        for r in rs:
            print(r)
print('\nDone')

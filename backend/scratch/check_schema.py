from app.config import engine
from sqlalchemy import text
with engine.connect() as conn:
    r = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'KhoHocLieu'")).fetchall()
    print([row[0] for row in r])

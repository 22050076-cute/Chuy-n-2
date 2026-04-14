import urllib.parse
from sqlalchemy import create_engine, text

USERNAME = 'sa'
PASSWORD = '123'
SERVER = '127.0.0.1'
PORT = '1433' 
DATABASE = 'LopHocSo'
DRIVER = 'ODBC Driver 17 for SQL Server' 

params = urllib.parse.quote_plus(
    f"DRIVER={{{DRIVER}}};SERVER={SERVER},{PORT};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Encrypt=yes;TrustServerCertificate=yes;"
)

SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as conn:
    print("--- Table: TraoDoiChuNhiem ---")
    res = conn.execute(text("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'TraoDoiChuNhiem'")).fetchall()
    for r in res:
        print(f"Col: {r[0]}, Type: {r[1]}")
    
    print("\n--- Foreign Keys for TraoDoiChuNhiem ---")
    fk_query = text("""
        SELECT 
            OBJECT_NAME(f.parent_object_id) AS TableName,
            COL_NAME(fc.parent_object_id,fc.parent_column_id) AS ColumnName,
            OBJECT_NAME (f.referenced_object_id) AS ReferenceTableName,
            COL_NAME(fc.referenced_object_id,fc.referenced_column_id) AS ReferenceColumnName
        FROM sys.foreign_keys AS f
        INNER JOIN sys.foreign_key_columns AS fc 
           ON f.OBJECT_ID = fc.constraint_object_id
        WHERE OBJECT_NAME(f.parent_object_id) = 'TraoDoiChuNhiem'
    """)
    fks = conn.execute(fk_query).fetchall()
    for fk in fks:
        print(f"FK: {fk[1]} -> {fk[2]}.{fk[3]}")

import os

import pymysql
from dotenv import load_dotenv

load_dotenv()

conexao = pymysql.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "sail"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "sus_map"),
    charset="utf8mb4",
)

with conexao.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM locations")
    print("Locais no banco:", cursor.fetchone()[0])

conexao.close()
import os

import pymysql
from dotenv import load_dotenv


def conectar():
    """Abre a conexão com o MySQL do PMS, lendo os dados do arquivo .env."""
    load_dotenv()
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "sail"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "sus_map"),
        charset="utf8mb4",
        autocommit=False,
    )


def salvar_registro(conexao, r):
    """Grava um estabelecimento nas tabelas do PMS.

    Tudo acontece em uma transação: ou grava o estabelecimento inteiro,
    ou não grava nada. Devolve "inserido" ou "atualizado".
    """
    try:
        with conexao.cursor() as cur:
            # 1) locations: o código CNES decide entre inserir e atualizar
            cur.execute("SELECT id FROM locations WHERE cnes = %s", (r["cnes"],))
            linha = cur.fetchone()

            if linha is None:
                cur.execute(
                    "INSERT INTO locations (cnes, latitude, longitude, created_at, updated_at) "
                    "VALUES (%s, %s, %s, NOW(), NOW())",
                    (r["cnes"], r["latitude"], r["longitude"]),
                )
                location_id = cur.lastrowid
                acao = "inserido"
            else:
                location_id = linha[0]
                cur.execute(
                    "UPDATE locations SET latitude = %s, longitude = %s, updated_at = NOW() "
                    "WHERE id = %s",
                    (r["latitude"], r["longitude"], location_id),
                )
                acao = "atualizado"

            # 2) descriptions: a chave primária é o próprio location_id
            cur.execute(
                "INSERT INTO descriptions (location_id, name, contact, created_at, updated_at) "
                "VALUES (%s, %s, %s, NOW(), NOW()) "
                "ON DUPLICATE KEY UPDATE name = VALUES(name), contact = VALUES(contact), "
                "updated_at = NOW()",
                (location_id, r["name"], r["contact"]),
            )

            # 3) addresses: a chave primária é o description_id (= location_id)
            cur.execute(
                "INSERT INTO addresses (description_id, street, number, district, cep, "
                "created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW()) "
                "ON DUPLICATE KEY UPDATE street = VALUES(street), number = VALUES(number), "
                "district = VALUES(district), cep = VALUES(cep), updated_at = NOW()",
                (location_id, r["street"], r["number"], r["district"], r["cep"]),
            )

            # 4) services + tabela de ligação
            if r["service"]:
                cur.execute("SELECT id FROM services WHERE name = %s", (r["service"],))
                servico = cur.fetchone()
                if servico is None:
                    cur.execute(
                        "INSERT INTO services (name, created_at, updated_at) "
                        "VALUES (%s, NOW(), NOW())",
                        (r["service"],),
                    )
                    service_id = cur.lastrowid
                else:
                    service_id = servico[0]

                cur.execute(
                    "SELECT 1 FROM locations_services WHERE location_id = %s AND service_id = %s",
                    (location_id, service_id),
                )
                if cur.fetchone() is None:
                    cur.execute(
                        "INSERT INTO locations_services (location_id, service_id, created_at, updated_at) "
                        "VALUES (%s, %s, NOW(), NOW())",
                        (location_id, service_id),
                    )

        conexao.commit()
        return acao
    except Exception:
        conexao.rollback()
        raise
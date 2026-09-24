import base64
import os
import tempfile
import mysql.connector
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _resolve_ssl_ca():
    ca_path = os.getenv("DB_SSL_CA", "").strip()
    if ca_path:
        return ca_path

    pem_text = os.getenv("DB_SSL_CA_PEM", "").strip()
    ca_b64 = os.getenv("DB_SSL_CA_BASE64", "").strip()
    if ca_b64:
        pem_text = base64.b64decode(ca_b64).decode("utf-8")

    if not pem_text:
        return None

    target = os.path.join(tempfile.gettempdir(), "easylearn-aiven-ca.pem")
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(pem_text.replace("\\n", "\n"))
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    return target


def get_db_connection():
    connection_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "mathsy_db"),
        "connection_timeout": 10,
    }

    db_ssl_ca = _resolve_ssl_ca()
    if db_ssl_ca:
        connection_config["ssl_ca"] = db_ssl_ca
        connection_config["ssl_verify_cert"] = True

    conn = mysql.connector.connect(**connection_config)

    cursor = conn.cursor()
    cursor.execute("SET time_zone = '+08:00'")
    cursor.close()
    return conn

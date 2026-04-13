import os
import socket
import datetime
import psycopg2
from flask import Flask, render_template, request

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        database=os.environ.get("DB_NAME", "citizendb"),
        user=os.environ.get("DB_USER", "appuser"),
        password=os.environ["DB_PASSWORD"]
    )

def get_infra_info():
    try:
        # Connect to an external address to find the real outbound IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = "unknown"
    return {
        "env":        os.environ.get("ENV_NAME", "dev"),
        "ip":         ip,
        "db_host":    os.environ.get("DB_HOST", "unknown"),
        "deployed_at": os.environ.get("DEPLOYED_AT", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
        "tf_version": os.environ.get("TF_VERSION", "Terraform"),
    }

@app.route("/", methods=["GET"])
def index():
    region = request.args.get("region", "")
    regions = []
    citizens = []

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT region FROM citizens ORDER BY region")
    regions = [row[0] for row in cur.fetchall()]

    if region:
        cur.execute(
            "SELECT first_name, last_name, birth_date, city, region "
            "FROM citizens WHERE region = %s ORDER BY last_name",
            (region,)
        )
        citizens = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        regions=regions,
        citizens=citizens,
        selected_region=region,
        infra=get_infra_info()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

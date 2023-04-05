import os

import mysql.connector
from dotenv import load_dotenv
load_dotenv()


mydb = mysql.connector.connect(
  host=os.getenv("HOST", "localhost"),
  user=os.getenv("USER", "root"),
  password=os.getenv("PASSWORD", ""),
  database=os.getenv("DATABASE", "telegram")
)

# testdb.execute("SHOW TABLES")
def query_db(sql, val):
    mydb.connect()
    rundb = mydb.cursor()
    mydb.start_transaction()
    rundb.execute(sql, val)
    mydb.commit()
    mydb.close()

def query_all(sql):
    mydb.connect()
    rundb = mydb.cursor()
    rundb.execute(sql)
    return rundb.fetchall()
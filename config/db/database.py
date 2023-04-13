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
    try:
        mydb.start_transaction()
        rundb.execute(sql, val)
        mydb.commit()
    except Exception as e:
        mydb.rollback()
        raise e
    finally:
        rundb.close()
        mydb.close()

def query_all(sql):
    mydb.connect()
    rundb = mydb.cursor()
    rundb.execute(sql)
    result = rundb.fetchall()
    rundb.close()
    mydb.close()
    return result
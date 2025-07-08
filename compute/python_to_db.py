import mysql.connector

tennisEloDb = mysql.connector.connect(
  host="localhost",
  user="noamshamir",
  password="ch@!ch@Sfr3ncHt0@sT"
)

print(tennisEloDb)
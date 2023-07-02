import json
import os

from pyspark.sql import SparkSession

DATABASE_URL = os.environ["DATABASE_URL"]

spark = SparkSession.builder.appName("Product Statistics").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

products_data_frame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_URL}:3306/store") \
    .option("dbtable", "store.products") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

products = products_data_frame \
    .filter((products_data_frame["sold"] > 0) | (products_data_frame["waiting"] > 0)) \
    .collect()

statistics = [
    {'name': row.name, 'sold': row.sold, 'waiting': row.waiting}
    for row in products
]

print("!!!!!*****")
print(json.dumps(statistics))

spark.stop()

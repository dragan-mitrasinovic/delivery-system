import json
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import sum, desc

DATABASE_URL = os.environ["DATABASE_URL"]

spark = SparkSession.builder.appName("Category Statistics").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

pic_data_frame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_URL}:3306/store") \
    .option("dbtable", "store.products_in_categories") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

products_data_frame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_URL}:3306/store") \
    .option("dbtable", "store.products") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

categories = pic_data_frame \
    .join(products_data_frame, pic_data_frame["product_id"] == products_data_frame["id"]) \
    .groupBy("category_name") \
    .agg(sum("sold").alias("total_sold")) \
    .sort(desc("total_sold"), "category_name") \
    .collect()

statistics = [
    row.category_name
    for row in categories
]

print("!!!!!*****")
print(json.dumps(statistics))

spark.stop()

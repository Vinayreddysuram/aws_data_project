import sys
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, current_date
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions

# Initialize the Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Retrieve arguments from the AWS Glue job
args = getResolvedOptions(sys.argv, ['BRONZE_DATABASE', 'BRONZE_TABLE', 'SILVER_BUCKET', 'SILVER_TABLE'])
bronze_database = args['BRONZE_DATABASE']
bronze_table = args['BRONZE_TABLE']
silver_bucket = args['SILVER_BUCKET']
silver_table = args['SILVER_TABLE']

# Access the Bronze level data
bronze_df = spark.sql(f"SELECT * FROM {bronze_database}.{bronze_table}")

# Calculate the max batch_id from the data
max_batch_id_result = spark.sql(f"SELECT max(batch_id) as max_batch_id FROM {bronze_database}.{bronze_table}")
max_batch_id = max_batch_id_result.collect()[0]['max_batch_id']

# Filter the data for the latest batch
latest_batch_df = bronze_df.filter(col('batch_id') == max_batch_id)

# Transformation logic
transformed_df = latest_batch_df.withColumnRenamed("OrderID", "order_id") \
                                .withColumnRenamed("DeliveredDt", "delivered_dt") \
                                .withColumnRenamed("Total", "total_amnt") \
                                .withColumnRenamed("ProductCode", "product_cd") \
                                .withColumnRenamed("ProductCategory", "product_catgry") \
                                .withColumnRenamed("Status", "order_status") \
                                .withColumnRenamed("CustomerID", "customer_id") \
                                .withColumn("quantity", col("quantity").cast("double")) \
                                .withColumn("price_per_unit", col("price_per_unit").cast("double")) \
                                .withColumn("total_amnt", col("total_amnt").cast("double")) \
                                .withColumn("OrderDt", to_date(col("OrderDt"), 'yyyy/MM/dd')) \
                                .withColumn("delivered_dt", to_date(col("delivered_dt"), 'yyyy/MM/dd')) \
                                .withColumn("record_create_dt", current_date())  # Adding the current date

# Define the output path
output_path = f"s3://{silver_bucket}/{silver_table}/batch_id={max_batch_id}"

# Write the transformed DataFrame back to S3 in Parquet format
transformed_df.write.parquet(output_path, mode="overwrite")

# After writing the data, add a new partition to the Athena table
spark.sql(f""" ALTER TABLE silver.{silver_table} ADD IF NOT EXISTS PARTITION (batch_id='{max_batch_id}')' """)

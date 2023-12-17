import sys
import datetime
from awsglue.context import GlueContext
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.dynamicframe import DynamicFrame
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

# Create a Glue context
glueContext = GlueContext(SparkContext.getOrCreate())

# Retrieve arguments
args = getResolvedOptions(sys.argv, ['S3_INPUT_PATH', 'S3_OUTPUT_BUCKET', 'BRONZE_DATABASE', 'TABLE_NAME'])
s3_input_path = args['S3_INPUT_PATH']
s3_output_bucket = args['S3_OUTPUT_BUCKET']
bronze_database = args['BRONZE_DATABASE']  # parameterized database name
table_name = args['TABLE_NAME']  # parameterized table name

spark = SparkSession.builder.appName("Read CSV and Write Parquet with batch_id").getOrCreate()

previous_day = datetime.now() - timedelta(1)
formatted_date = previous_day.strftime("%Y%m%d")


# Construct the path dynamically
s3_input_file = f"{s3_input_path}/orders_{formatted_date}.csv" 


df = spark.read.csv(s3_input_file, header=True)

# Generate batch_id based on today's date
batch_id = datetime.datetime.now().strftime("%Y%m%d")

# Add the batch_id column to the DataFrame
df_with_batch = df.withColumn("batch_id", F.lit(batch_id))

# Define the path where the parquet file will be saved
parquet_output_path = f"s3://{s3_output_bucket}/orders/batch_id={batch_id}/"

# Save the DataFrame as a Parquet file
df_with_batch.write.parquet(parquet_output_path, mode="overwrite")

spark.sql(f"ALTER TABLE {bronze_database}.{table_name} ADD IF NOT EXISTS PARTITION (batch_id='{batch_id}')")


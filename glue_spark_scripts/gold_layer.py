import sys
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, datediff, when, sum as sql_sum
from pyspark.sql.window import Window
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from awsglue.dynamicframe import DynamicFrame

# Initialize the Glue and Spark contexts
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Retrieve arguments from the AWS Glue job parameters
args = getResolvedOptions(sys.argv, ['GOLD_BUCKET', 'SILVER_DATABASE', 'ORDERS_TABLE'])
gold_bucket = args['GOLD_BUCKET']
silver_database= args['SILVER_DATABASE']
orders_table = args['ORDERS_TABLE']


# Access the silver level data
order_df = spark.sql(f"SELECT * FROM {silver_database}.{orders_table}")



# Calculate the max batch_id from the data
max_batch_id = orders_df.agg({"batch_id": "max"}).collect()[0][0]

# Filter the data for the max batch_id
latest_orders_df = orders_df.filter(col('batch_id') == max_batch_id)

windowSpec = Window.partitionBy('order_id')
orders_df_with_total = latest_orders_df.withColumn('order_total', sql_sum('total_amnt').over(windowSpec))

orders_df_with_delivery_time = orders_df_with_total.withColumn('delivery_time_days', 
                                                               datediff(col('delivered_dt'), col('order_dt')))

final_orders_df = orders_df_with_delivery_time.withColumn('order_total',
                                                          when(col('order_status') == 'cancelled', 0)
                                                          .otherwise(col('order_total')))



# Define the output path
output_path = f"s3://{gold_bucket}/{order_table}/batch_id={max_batch_id}"


# Write the transformed DataFrame back to S3 in Parquet format
transformed_df.write.parquet(output_path, mode="overwrite")



# After writing the data, add a new partition to the Athena table
spark.sql(f""" ALTER TABLE gold.{orders_table} ADD IF NOT EXISTS PARTITION (batch_id='{max_batch_id}')' """)


# Convert to Glue Dynamic Frame as Glue connections utilize DynamicFrames
dynamic_frame_write = DynamicFrame.fromDF(final_orders_df, glueContext, "dynamic_frame_write")


redshift_copy = glueContext.write_dynamic_frame.from_options(
    frame=dynamic_frame_write, 
    connection_type="redshift",
    connection_options={
        "redshiftTmpDir": "s3://aws-glue-assets-123456776-us-east-1a/temporary/",  
        "useConnectionProperties": "true",
        "dbtable": "retail_db.orders",
        "connectionName": "redshift_retail_conn",
    },
    transformation_ctx="redshift_copy"
)

print("Data has been loaded into Redshift successfully.")

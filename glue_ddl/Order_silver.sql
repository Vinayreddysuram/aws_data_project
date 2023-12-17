CREATE EXTERNAL TABLE silver.orders(
  order_id string, 
  order_dt date, 
  product_catgry string, 
  product_cd string, 
  price_per_unit double, 
  quantity double, 
  total_amnt double, 
  order_source string, 
  delivered_dt date, 
  order_status string, 
  customer_id string, 
  shipping_address string, 
  country string, 
  postal string, 
  region string,
  record_create_dt date
)
PARTITIONED BY ( 
  batch_id string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://qkart-silver-prod/silver/orders/' 
TBLPROPERTIES ( 
  'parquet.compress'='SNAPPY'
);

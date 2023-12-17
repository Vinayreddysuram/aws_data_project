CREATE EXTERNAL TABLE qkart_orders(
  orderID string,
  OrderDt string,
  product_category string,
  ProductCode string,
  price_per_unit string,
  quantity string,
  Total string,
  OrderSource string,
  DeliveredDt string,
  Status string,
  CustomerID string,
  ShippingAddress string,
  Country string,
  Postal string,
  region string
)
PARTITIONED BY (
  batch_id string
)
STORED AS PARQUET
LOCATION 's3://qkart-bronze-prod/orders/'
TBLPROPERTIES ("parquet.compress"="SNAPPY");

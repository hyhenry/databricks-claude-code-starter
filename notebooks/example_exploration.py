# Databricks notebook source
# MAGIC %md
# MAGIC # Example exploration
# MAGIC
# MAGIC A standard Databricks notebook. It runs unchanged in the workspace, or locally with
# MAGIC **Run in Databricks Connect** in VS Code. Use it to check your setup, then copy it as a starting point.
# MAGIC
# MAGIC Data: `samples.bakehouse`, a sample dataset that ships with Databricks workspaces.

# COMMAND ----------

# MAGIC %md ## Parameters
# MAGIC Widgets work in the workspace. Locally they return their default values.

# COMMAND ----------

dbutils.widgets.text("catalog", "samples", "Catalog")
dbutils.widgets.text("schema", "bakehouse", "Schema")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")

# COMMAND ----------

# MAGIC %md ## Look at the data
# MAGIC Spark runs on Databricks. `display()` renders a table.

# COMMAND ----------

transactions = spark.table(f"{CATALOG}.{SCHEMA}.sales_transactions")
print(f"{transactions.count():,} transactions")
display(transactions.drop("cardNumber").limit(10))

# COMMAND ----------

# MAGIC %md ## Aggregate in Spark, then bring the small result to pandas

# COMMAND ----------

from pyspark.sql import functions as F

by_product = (transactions
              .groupBy("product")
              .agg(F.sum("totalPrice").alias("revenue"), F.sum("quantity").alias("units"))
              .orderBy(F.desc("revenue")))
by_product_pd = by_product.toPandas()
display(by_product_pd)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- SQL cells work too
# MAGIC SELECT paymentMethod, COUNT(*) AS transactions, SUM(totalPrice) AS revenue
# MAGIC FROM samples.bakehouse.sales_transactions
# MAGIC GROUP BY paymentMethod
# MAGIC ORDER BY revenue DESC

# COMMAND ----------

# MAGIC %md ## Chart locally with matplotlib

# COMMAND ----------

import matplotlib.pyplot as plt

data = by_product_pd.sort_values("revenue")
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(data["product"], data["revenue"], color="#2a78d6", height=0.6)
ax.bar_label(bars, labels=[f"${v:,.0f}" for v in data["revenue"]], padding=3, color="#52514e")
ax.set_title("Revenue by product", loc="left", fontweight="semibold")
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlabel("Revenue ($)")
plt.tight_layout()
plt.show()

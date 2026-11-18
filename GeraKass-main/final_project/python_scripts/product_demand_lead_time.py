import pandas as pd
import pyodbc
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np


server = 'johndroescher.com'
default_db = 'Sum_2025'
username = os.environ["mssql_ccny_user"]
password = os.environ["mssql_ccny_pw"]


cnxn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + server
        + ";DATABASE="
        + default_db
        + ";UID="
        + username
        + ";PWD="
        + password
    )

# sql_query = """
# SELECT 
#   TOP(3) * FROM [Sum_2025].[dbo].[tx_deathrow];
# """
sql_query = """
SELECT
   product_name,
   ROUND(AVG(daily_units), 2) AS avg_daily_demand
FROM (
   SELECT
       product_name,
       CAST(Order_Date AS DATE) AS order_day,
       SUM(units) AS daily_units
   FROM [Sum_2025].[dbo].[candy_sales]
   GROUP BY product_name, CAST(Order_Date AS DATE)
) AS daily_data
GROUP BY product_name
ORDER BY avg_daily_demand DESC;
"""

df = pd.read_sql(sql_query, cnxn)
df['Reorder_3_Day'] = df['avg_daily_demand'] * 3
df['Reorder_7_Day'] = df['avg_daily_demand'] * 7
df['Reorder_9_Day'] = df['avg_daily_demand'] * 9

print(df.columns)


sorted_df = df.sort_values("avg_daily_demand", ascending=False).reset_index(drop=True)



#HIGH PRIORITY
#products = df.sort_values("avg_daily_demand", ascending=False).head(5)

#LOW  PRIORITY PRODUCTS
# products = sorted_df.tail(5)

#MEDIUM  PRIORITY PRODUCTS
middle_index = len(sorted_df) // 2
products = sorted_df.iloc[middle_index - 2 : middle_index + 3]  # 5 items centered around the middle



# Step 3: Set up the graph
labels = products['product_name']
x = np.arange(len(labels))
width = 0.25

fig, ax = plt.subplots(figsize=(12, 6))

ax.bar(x - width, products['Reorder_3_Day'], width, label='3-Day')
ax.bar(x,         products['Reorder_7_Day'], width, label='7-Day')
ax.bar(x + width, products['Reorder_9_Day'], width, label='9-Day')

ax.set_ylabel('Units Needed')
ax.set_title('Medium-Demand Products: Reorder Quantity Based on Lead Time')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right')
ax.legend()
plt.tight_layout()
plt.show()
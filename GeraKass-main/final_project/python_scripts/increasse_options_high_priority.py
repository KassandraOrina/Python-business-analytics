import pandas as pd
import pyodbc
import os
import matplotlib.pyplot as plt
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

#TODO
# identify which products had sales spikes of more than 25% in specific months, based on data from the past 2 years.
#group orders by year
# sum the sales for each product in each month
# Calculate the average monthly sales per product
#calculate the average monthly sales for each product
# join the monthly sales with the average sales and determine how much more percantage the monthly sales where compared to the average
# sort everything by product name and month 

sql_query = """
WITH monthly_sales AS (
  SELECT
    FORMAT(order_date, 'yyyy-MM') AS order_month,
    product_name,
    SUM(sales) AS total_sales
  FROM [Sum_2025].[dbo].[candy_sales]
  WHERE order_date >= DATEADD(YEAR, -2, CAST(GETDATE() AS DATE))
  GROUP BY FORMAT(order_date, 'yyyy-MM'), product_name
),
avg_sales AS (
  SELECT 
    product_name,
    AVG(total_sales) AS avg_monthly_sales
  FROM monthly_sales
  GROUP BY product_name
)
SELECT 
  ms.order_month,
  ms.product_name,
  ms.total_sales,
  a.avg_monthly_sales,
  ROUND((ms.total_sales - a.avg_monthly_sales) / a.avg_monthly_sales * 100, 1) AS percent_increase
FROM monthly_sales ms
JOIN avg_sales a ON ms.product_name = a.product_name
WHERE (ms.total_sales - a.avg_monthly_sales) / a.avg_monthly_sales > 0.25
ORDER BY ms.product_name, ms.order_month;
"""


df = pd.read_sql(sql_query, cnxn)

# grab/ and convert the month name from each month by using datetime 
df['month_name'] = pd.to_datetime(df['order_month']).dt.strftime('%b')


# figure out the AVERAGE percentage increase for each product 
df_grouped = df.groupby(['month_name', 'product_name'], as_index=False).agg({
    'percent_increase': 'mean'
})


month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
df_grouped['month_name'] = pd.Categorical(df_grouped['month_name'], categories=month_order, ordered=True)

# make the graph order by month name
df_grouped = df_grouped.sort_values(['month_name', 'product_name'])

# Filter to high-priority products
top_products = [
    'Wonka Bar - Milk Chocolate',
    'Nerds',
    'Kazookles',
    'Fun Dip',
    'Laffy Taffy'
]
df_high_priority = df_grouped[df_grouped['product_name'].isin(top_products)].copy()


#giving it a baseline of 1 but this would be in adition to what we already order regularely 
df_high_priority['Reorder_7_Day'] = 1
df_high_priority['Reorder_7_Day_Seasonal'] = df_high_priority['Reorder_7_Day'] * (1 + df_high_priority['percent_increase'] / 100)


pivot = df_high_priority.pivot(index='month_name', columns='product_name', values='Reorder_7_Day_Seasonal')

pivot.plot(kind='bar', figsize=(14, 6))
plt.title('How Much More to Order During Peak Months (7-Day Cycle)')
plt.ylabel('Units to Reorder')
plt.xlabel('Month')
plt.xticks(rotation=0)
plt.legend(title="Product")
plt.tight_layout()
plt.show()


print(df_high_priority[['month_name', 'product_name', 'percent_increase', 'Reorder_7_Day_Seasonal']])

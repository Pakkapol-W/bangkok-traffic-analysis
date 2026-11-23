import pandas as pd
import numpy as np
import glob
import os
from sklearn.preprocessing import LabelEncoder

"""## Merge All Datasets
Merge all dataset together and also rename file the lat long column for all files so it matches
"""

folder_path = 'data'

# Find all files
search_path = os.path.join(folder_path, "*.xlsx")
all_files = glob.glob(search_path)

print(f"Looking in: {search_path}")
print(f"Found {len(all_files)} files.")

df_list = []
for filename in all_files:
    temp_df = pd.read_excel(filename, engine='openpyxl')

    # standardized lat/long column name
    temp_df.columns = temp_df.columns.str.strip()

    rename_map = {
        'Lat.': 'Lat',
        'Lon.': 'Long',
    }
    temp_df.rename(columns=rename_map, inplace=True)

    temp_df['Source_Month'] = os.path.basename(filename)
    df_list.append(temp_df)
    print(f"-> Loaded: {os.path.basename(filename)} ({temp_df.shape[0]} rows)")

#Combine
if df_list:
    df = pd.concat(df_list, axis=0, ignore_index=True)
    print(f"\nTOTAL MERGED ROWS: {df.shape[0]}")
else:
    df = pd.DataFrame()

df.head(1000)

from google.colab import drive
drive.mount('/content/drive')

df.to_csv('/content/drive/My Drive/merged_dataset.csv', index=False)

"""## Clean/Format Data

### Fix Dates
Add
- Column Day_Name (i.e. Monday, Thursday)
- Column DayOfWeek_Num (encode day into num)
  - Monday = 0
  - Tuesday = 1
- Column Is_Weekend
"""

df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date'])

df['Day_Name'] = df['Date'].dt.day_name()
df['Day_OfWeek_Num'] = df['Date'].dt.dayofweek
df['Is_Weekend'] = df['Date'].dt.dayofweek >= 5

df.head(10)

"""### Total Number of Types of Vehicles in Each Day"""

def get_safe_sum(df, keyword):
        cols = [c for c in df.columns if keyword in c and 'Total' not in c]
        for c in cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        return df[cols].sum(axis=1)

df['Total_Car'] = get_safe_sum(df, 'Car')
df['Total_Van'] = get_safe_sum(df, 'Van')
df['Total_Bus'] = get_safe_sum(df, 'Bus')
df['Total_Truck'] = get_safe_sum(df, 'Truck')
df['Total_Minibus'] = get_safe_sum(df, 'Minibus')

# Summing Time Slots
cols_7_9 = [c for c in df.columns if '7-9' in c and 'Total' not in c]
cols_17_19 = [c for c in df.columns if '17-19' in c and 'Total' not in c]
cols_9_17 = [c for c in df.columns if '9-17' in c and 'Total' not in c]

for c in cols_7_9 + cols_17_19 + cols_9_17:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

df['Vol_7_9'] = df[cols_7_9].sum(axis=1)
df['Vol_17_19'] = df[cols_17_19].sum(axis=1)
df['Vol_9_17'] = df[cols_9_17].sum(axis=1)

df['Total_Vol'] = df['Vol_7_9'] + df['Vol_9_17'] + df['Vol_17_19']

df.head(10)

"""### Create Ratios
Ratio of each type of vehicles with the total vehicles on each day
"""

safe_total = df['Total_Vol'].replace(0, 1)
df['Ratio_Car'] = df['Total_Car'] / safe_total
df['Ratio_Truck'] = df['Total_Truck'] / safe_total
df['Ratio_Public'] = (df['Total_Van'] + df['Total_Bus'] + df['Total_Minibus']) / safe_total

df.head(10)

"""### Create Scores
Direction: +1 (Morning), -1 (Evening)

describe if morning commute or evening, which one is heavier
"""

df['Direction_Score'] = (df['Vol_7_9'] - df['Vol_17_19']) / (df['Vol_7_9'] + df['Vol_17_19'] + 0.1)

df.head(10)

"""### Peakedness: Rush vs Day"""

rush_rate = (df['Vol_7_9'] + df['Vol_17_19']) / 4.0
day_rate = df['Vol_9_17'] / 8.0
df['Peakedness_Score'] = rush_rate / (day_rate + 0.1)

df.head(10)

"""### Encoding Road Names"""

le = LabelEncoder()
df['Road'] = df['Road'].astype(str)
df['Road_Code'] = le.fit_transform(df['Road'])

df.head(1000)

"""## Final Data Set"""

cols_to_keep = [
    'Date', 'Day_Name', 'Day_OfWeek_Num', 'Is_Weekend',
    'Road', 'Road_Code', 'Lat', 'Long',
    'Total_Vol', 'Total_Car', 'Total_Truck',
    'Ratio_Car', 'Ratio_Truck',
    'Direction_Score', 'Peakedness_Score'
]

final_cols = [c for c in cols_to_keep if c in df.columns]
df_clean = df[final_cols].copy()

output_filename = 'traffic_master_data_final.csv'
df_clean.to_csv(output_filename, index=False)

from google.colab import drive
drive.mount('/content/drive')

df_clean.to_csv('/content/drive/My Drive/cleaned_dataset.csv', index=False)

df_clean.head(10)

"""## Cleaned Column Description

### General ข้อมูล

| **Column Name** | **Description** |
| :--- | :--- |
| `Date` | The specific date of the traffic count.
| `Day_Name`  | Name of the day
| `Is_Weekend`  | `True` if Saturday/Sunday, `False` if Weekday.
| `Road` | name of road
| `Lat` | Latitude coordinate
| `Long` | Longitude coordinate

| **Column Name** | **Description** |
| :--- | :--- |
| `Total_Car` | Sum of cars from all time slots (7-9, 9-17, 17-19). |
| `Total_Truck` | Sum of trucks |
| `Total_Bus` | Sum of large buses |
| `Total_Van` | Sum of passenger vans |
| `Vol_7_9` | Total volume during Morning Rush (2 Hours) |
| `Vol_17_19` | Total volume during Evening Rush (2 Hours). |

### ข้อมูลสำหรับ Clustering

| **Column Name** | **Description** | **Interpretation** |
| :--- | :--- | :--- |
| `Ratio_Car` | **Formula:** `Total Car / Total Vol` <br>Percentage of traffic that is private cars. | • **High (> 0.70):** Commuter Road <br>• **Low (< 0.50):** Mixed or Industrial Road |
| `Ratio_Truck` | **Formula:** `Total Truck / Total Vol` <br>Percentage of traffic that is heavy trucks. | • **High (> 0.10):** Industrial Zone <br>• **Low (~ 0.01):** Residential/City Center |
| `Ratio_Public` | **Formula:** `(Van+Bus+Minibus) / Total Vol`<br>Percentage of public transport usage. | • **High:** Transit เยอะ.<br>• **Low:** "Transit น้อย. |
| `Direction_Score` | **Formula:** `(AM - PM) / Total Rush`<br>Determines flow direction. | • **+1.0:** Morning Heavy <br>• **-1.0:** Evening Heavy <br>• **0.0:** Balanced Flow. |
| `Peakedness_Score`| **Formula:** `Avg Rush Vol / Avg Day Vol`<br>Determines if traffic is temporary or constant. | • **> 1.2:** Rush Hour Only <br>• **~ 1.0:** Busy All Day |

### ข้อมูลสำหรับ Prediction

| **Column Name** | **Role** | **Description** |
| :--- | :--- | :--- |
| `Total_Vol` | **TARGET (Y)** | The total number of vehicles counted that day. **This is what we are predicting.** |
| `Road_Code` | Feature (X) | numeric ID for the Road Name |
| `Day_OfWeek_Num`| Feature (X) | Number representing the day |
"""

df_clean.Long.unique()
df_clean.loc[df_clean.Long == "10.0.609137","Long"] = 100.609137

df_clean["Long"] = df_clean["Long"].astype(float)

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

features = ["Lat","Long","Ratio_Car", "Ratio_Truck", "Direction_Score", "Peakedness_Score"]
X = df_clean[features]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

inertia_list = []
K_range = range(2, 12)

for k in K_range:
    km = KMeans(n_clusters=k, random_state=42)
    km.fit(X_scaled)
    inertia_list.append(km.inertia_)

plt.plot(K_range, inertia_list, marker='o')
plt.xlabel("k")
plt.ylabel("Inertia")
plt.title("Elbow Method")
plt.show()

optimal_k = 7   # adjust based on elbow plot
kmeans = KMeans(n_clusters=optimal_k, random_state=42)
df_clean["Cluster_ID"] = kmeans.fit_predict(X_scaled)

df_clean.head()

cluster_stats = df_clean.groupby("Cluster_ID")[["Lat","Long","Ratio_Car", "Ratio_Truck", "Direction_Score", "Peakedness_Score"]].mean()

print(cluster_stats)

import matplotlib.pyplot as plt
import itertools

# Pick the features you want to plot
features = ["Lat","Long","Ratio_Car", "Ratio_Truck", "Direction_Score", "Peakedness_Score"]

# Generate all feature pairs
pairs = list(itertools.combinations(features, 2))

for x in features[:-1]:
    plt.figure(figsize=(8, 6))
    plt.scatter(df_clean[x], df_clean["Peakedness_Score"],
                c=df_clean["Cluster_ID"], cmap="viridis")

    plt.xlabel(x)
    plt.ylabel("Peakedness_Score")
    plt.title(f"Clusters by {x} vs Peakedness_Score")
    plt.colorbar(label="Cluster ID")
    plt.show()


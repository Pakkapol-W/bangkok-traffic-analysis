# Bangkok Traffic Analysis

Groups Bangkok road-count locations by their traffic behaviour using monthly open-data traffic counts. The script merges the monthly spreadsheets, builds features from them (vehicle mix, rush-hour direction, peakedness) and clusters the locations with K-Means.

## Contributors
- Pakkapol Wongnitirat
- Pongburit Wongchaiyakul
- Waritsara Chanthadet

## Data

`data/` contains monthly traffic-count spreadsheets (`opendata-*.xlsx`) from Bangkok open data, covering roughly **2023 to May 2025**. Each file lists count locations (bridges, tunnels, intersections and roads, named in Thai), with their coordinates and vehicle counts by type for three time slots:

- **07:00–09:00**: morning rush
- **09:00–17:00**: daytime
- **17:00–19:00**: evening rush

## Pipeline (`code.py`)

1. **Merge**: loads every `data/*.xlsx`, standardizes the `Lat.`/`Lon.` columns to `Lat`/`Long`, and records the source file in each row.
2. **Date features**: `Day_Name`, `Day_OfWeek_Num` (Mon = 0) and `Is_Weekend`.
3. **Volumes**: totals per vehicle type (car, van, bus, truck, minibus) and per time slot (`Vol_7_9`, `Vol_9_17`, `Vol_17_19`, `Total_Vol`).
4. **Engineered features**:

   | Feature | Formula | How to read it |
   | :--- | :--- | :--- |
   | `Ratio_Car` | Total Car / Total Vol | > 0.70 suggests a commuter road; < 0.50 suggests mixed or industrial traffic |
   | `Ratio_Truck` | Total Truck / Total Vol | > 0.10 suggests an industrial zone |
   | `Ratio_Public` | (Van + Bus + Minibus) / Total Vol | Share of public transport |
   | `Direction_Score` | (AM − PM) / (AM + PM) | +1 is morning-heavy, −1 is evening-heavy, 0 is balanced |
   | `Peakedness_Score` | Avg rush-hour rate / avg daytime rate | > 1.2 means busy only at rush hour; ~1.0 means busy all day |

5. **Encoding**: `Road` is label-encoded to `Road_Code` for later prediction work. The intended target is `Total_Vol`.
6. **Clustering**: standardizes `Lat`, `Long`, `Ratio_Car`, `Ratio_Truck`, `Direction_Score` and `Peakedness_Score`, picks *k* with the elbow method, and fits K-Means (k = 7). It then plots the clusters against `Peakedness_Score`.

The cleaned dataset is written to `traffic_master_data_final.csv`. That file is git-ignored; run the script to regenerate it.

## Getting started

```bash
pip install pandas numpy scikit-learn matplotlib openpyxl
python code.py
```

> **Note:** `code.py` was exported from Google Colab. The `google.colab` / `drive.mount(...)` lines only work in Colab. To run it locally, remove or comment out those lines and the `to_csv('/content/drive/...')` calls.

## Project structure

```
.
├── code.py      # Merge, clean, feature engineering, clustering
├── data/        # Monthly traffic-count spreadsheets (.xlsx)
└── README.md
```

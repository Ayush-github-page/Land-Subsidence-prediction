
# ------------------------------
# 1. Import Libraries
# ------------------------------
import ee
import pandas as pd
import json
# Trigger the authentication flow.
ee.Authenticate()

ee.Initialize(project="healthy-saga-471512-a4")


# ------------------------------
# 2. Define AOI and Date Range
# ------------------------------
# 500m x 500m rectangle over Singareni Mines, Yellandu
aoi = ee.Geometry.Polygon([
    [[80.31646, 17.58814],
     [80.31646, 17.59314],
     [80.32146, 17.59314],
     [80.32146, 17.58814]]
])

start_date = '2014-01-01'
end_date = '2025-06-30'

# ------------------------------
# 3. Load Sentinel-1 Collection
# ------------------------------
s1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
       .filterBounds(aoi) \
       .filterDate(start_date, end_date) \
       .filter(ee.Filter.eq('instrumentMode', 'IW')) \
       .select('VV')  # Change to 'VH' if needed

# ------------------------------
# 4. Reduce Each Image Over AOI
# ------------------------------
def reduce_image(image):
    mean_dict = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=10
    )
    # Handle null values
    vv = ee.Algorithms.If(mean_dict.get('VV'), mean_dict.get('VV'), -9999)
    
    return ee.Feature(None, {
        'date': image.date().format('YYYY-MM-dd'),
        'VV': vv
    })

fc = s1.map(reduce_image)

# Filter out nulls
fc_filtered = fc.filter(ee.Filter.neq('VV', -9999))

# ------------------------------
# 5. Convert FeatureCollection to Pandas DataFrame
# ------------------------------
features = fc_filtered.getInfo()['features']
data = [(f['properties']['date'], f['properties']['VV']) for f in features]
df = pd.DataFrame(data, columns=['date', 'VV'])
df.sort_values('date', inplace=True)
df.reset_index(drop=True, inplace=True)

# Save CSV
df.to_csv('singareni.csv', index=False)

# ------------------------------
# 6. Convert to JSON for Website
# ------------------------------
chart_json = {'labels': df['date'].tolist(), 'data': df['VV'].tolist()}
with open('singareni.json', 'w') as f:
    json.dump(chart_json, f)

print("CSV and JSON for chart generated successfully!")

# How to Visualize Your Postcode Data

## Problem
Your `test_data` has postcodes but **no coordinates (lat/long)** yet. You need coordinates to plot on a map.

## Solution Options

### Option 1: Use OS Code-Point Open (Recommended - Free)
Download postcode coordinates from London Datastore:
- URL: https://data.london.gov.uk/dataset/ordnance-survey-code-point/
- Contains: Postcode → Easting/Northing coordinates
- You'll need to convert to Lat/Long

### Option 2: Visualize by MSOA (What you can do NOW)
Since you already have `msoa21cd` in your data, you can:
1. Join with MSOA boundaries (which you already have)
2. Visualize by MSOA instead of individual postcodes

## Quick Visualization Code (Using MSOA)

```python
# Join test_data with your MSOA boundaries
postcode_summary = test_data.groupby('msoa21cd').agg({
    'pcds': 'count',  # Count postcodes per MSOA
    'msoa21nm': 'first',
    'ladnm': 'first'
}).rename(columns={'pcds': 'postcode_count'}).reset_index()

# Merge with MSOA geodata
msoa_with_postcodes = london_gdf_wgs84.merge(
    postcode_summary,
    on='msoa21cd',
    how='left'
)

# Visualize
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(15, 15))
msoa_with_postcodes.plot(
    ax=ax,
    column='postcode_count',
    cmap='YlOrRd',
    edgecolor='black',
    linewidth=0.5,
    legend=True,
    legend_kwds={'label': 'Number of Postcodes', 'orientation': 'horizontal'}
)
ax.set_title('Postcode Count by MSOA', fontsize=18)
plt.axis('off')
plt.show()
```

## Interactive Folium Map

```python
import folium

# Create map
m = folium.Map(
    location=[51.5074, -0.1278],
    zoom_start=10,
    tiles='CartoDB positron'
)

# Add choropleth
folium.Choropleth(
    geo_data=msoa_with_postcodes,
    data=msoa_with_postcodes,
    columns=['msoa21cd', 'postcode_count'],
    key_on='feature.properties.msoa21cd',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.5,
    legend_name='Postcode Count'
).add_to(m)

# Add tooltips
folium.GeoJson(
    msoa_with_postcodes,
    style_function=lambda x: {'fillOpacity': 0},
    tooltip=folium.GeoJsonTooltip(
        fields=['msoa21nm', 'ladnm', 'postcode_count'],
        aliases=['MSOA:', 'Borough:', 'Postcodes:']
    )
).add_to(m)

m
```

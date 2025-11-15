## London Housing Cost Visualization - Project Plan


### Phase 1: Early Functionality
**A. Travel cost calculator**
   - A simple UI where user can calculate the travel cost between their home and workplace
   - Deployment in Streamlit 
   - Data source: TfL transport api
   - Cost calculator -> route_calculator.py

**B. Inclusion of concil tax and average rent cost in**

  **B.1 Acquire datasets**:
   - London postcode boundaries (GeoJSON/Shapefile from OS Open Data or London Datastore)
   - Average rent per square meter by postcode/borough
   - Council tax data by borough
   - London postcode coordinates

 **B.2 Data cleaning & integration**:
   - Merge datasets on postcode/borough
   - Handle missing values
   - Calculate derived metrics
   - Export to clean CSV/JSON format

### Phase 2: Optimization of best accomodation location

**C. Build Interactive map visualization Streamlit UI**:
   - Postcode selection inputs (home & work)
   - Interactive map visualization
   - Cost breakdown display (rent, travel, council tax, total)
   - Filter/toggle options (property size, travel mode)

   **C.1 Build geospatial components**:
   - Create interactive London map using Folium or Plotly
   - Add postcode boundary overlays
   - Implement color-coding by cost metrics


### Phase 3: Refinement & Deployment
**D. Add enhancements**:
   - Comparison mode (multiple postcodes)
   - Affordability heatmap overlay
   - Data visualizations (charts for cost breakdown)

**E. Prepare for deployment**:
   - Create requirements.txt
   - Optimize data loading (caching)
   - Add documentation/README
   - Test locally

**F. Deploy to Streamlit Cloud**:
   - Push to GitHub repository
   - Connect to Streamlit Cloud
   - Configure deployment settings
   - Test production deployment

**Key Technologies**: Python, Streamlit, Folium/Plotly, Pandas, GeoPandas

# 🏠 Where to Live in London?

A comprehensive Streamlit web application that helps you make informed decisions about where to live in London by calculating and comparing travel costs, council tax, and rent prices between different postcodes.

**🔗 Live App**: [https://wheretoliveinlondon.streamlit.app](https://wheretoliveinlondon.streamlit.app)

## Overview

This app combines real-time Transport for London (TfL) journey data with council tax and rental price information to give you a complete picture of the monthly cost of living in different London areas.

## ✨ Key Features

### 🚇 Journey Planning & Travel Costs
- **Multiple Route Options**: Compare different journey routes between any two London postcodes
- **Journey Time Selection**: View costs for current time, rush hour (8:30 AM), or off-peak (11:00 AM)
- **Smart Route Filtering**: Automatically filters duplicate routes for clearer comparisons
- **Advanced Journey Options**:
  - Transport mode selection (tube, bus, DLR, overground, etc.)
  - Journey preferences (least time, least walking, least interchanges)
  - Customizable travel days per week (1-5 days)
- **Cost Breakdown**:
  - Single journey fare
  - Daily, weekly, and monthly commute costs
  - Includes TfL fare capping calculations
- **Interactive Maps**: Visual journey representation with color-coded transport modes

### 🏛️ Council Tax
- Council tax lookup by postcode and borough
- Monthly and annual costs for all bands (A-H)
- Interactive band selector to see different cost scenarios
- Data source: [London Datastore](https://data.london.gov.uk/dataset/council-tax-charges-bands-borough-expnl/)

### 🏘️ Average Rent Prices
- Median rent prices by bedroom category:
  - Room, Studio, One Bedroom, Two Bedrooms, Three Bedrooms, Four or More Bedrooms
- Monthly and annual rent estimates
- Lower and upper quartile data for context
- Data source: [ONS Private Rental Market in London](https://www.ons.gov.uk/economy/inflationandpriceindices/adhocs/2923privaterentalmarketinlondonjuly2024tojune2025)

### 💰 Cost Comparison
- **Total Monthly Cost**: Combined view of commute + rent + council tax
- **Save Comparisons**: Save multiple location scenarios with custom names
- **Export to CSV**: Download all saved comparisons for further analysis
- **Comprehensive Details**: Each comparison includes:
  - From/To postcodes and boroughs
  - Journey time and period (rush hour/off-peak)
  - Travel days per week
  - Council tax band
  - Bedroom category
  - All associated costs

### 🗺️ Interactive Visualization
- Journey maps with station markers and route details
- Color-coded transport modes
- Borough information for each postcode
## 🚀 Quick Start

### Using the Live App
Simply visit **[https://wheretoliveinlondon.streamlit.app](https://wheretoliveinlondon.streamlit.app)** and start comparing locations!

### Running Locally

**Prerequisites:**
- Python 3.8+
- TfL API Key ([Get one free here](https://api-portal.tfl.gov.uk/))

**Setup:**

1. Clone the repository:
```bash
git clone https://github.com/modatasci/house_and_living_cost_in_London.git
cd housing_in_london
```


2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your TfL API key:
```bash
TFL_APP_KEY=your_api_key_here
```

4. Run the Streamlit app:
```bash
streamlit run src/app.py
```

## 📖 How to Use

1. **Enter Postcodes**: Input your home and office/school postcodes in the sidebar
2. **Set Preferences**:
   - Choose council tax band (A-H)
   - Select bedroom category for rent or enter rent amount manually
   - Set traveling days per week
   - Optional: Adjust journey time (rush hour/off-peak) and transport modes
3. **Calculate**: Click "Calculate Costs" to see your results
4. **Compare Routes**: If multiple routes are available, select your preferred option
5. **Adjust Parameters**: Change council tax band, bedroom category, or travel days on the fly
6. **Save Comparisons**: Add a name and save different scenarios to compare side-by-side
7. **Export**: Download all saved comparisons as CSV for further analysis

## 📱 Example Use Cases

**Scenario 1: New Job, Where Should I Live?**
- Input your new office postcode
- Try different residential postcodes (e.g., different boroughs)
- Compare total monthly costs to find the sweet spot

**Scenario 2: Comparing Neighborhoods**
- Save comparisons for Zones 2, 3, and 4
- See how commute costs offset by lower rent/council tax
- Export to spreadsheet for detailed analysis

**Scenario 3: Part-Time Commute**
- Adjust traveling days to 2-3 days per week
- See how hybrid work affects total costs
- Compare rush hour vs off-peak journey times

## 🏗️ Project Structure

```
housing_in_london/
├── src/
│   ├── app.py                        # Main Streamlit application
│   ├── route_calculator.py           # TfL journey planning & cost calculations
│   ├── get_living_cost.py            # Council tax & rent lookup
│   ├── post_code_data_processor.py   # Postcode to borough mapping
│   └── council_tax_processor.py      # Council tax data processing
├── data/
│   ├── council_tax/
│   │   └── council_tax_2024_2025.csv
│   ├── rent_price/
│   │   └── londonrent.csv
│   └── geodata/
│       └── post_code/
│           └── london_post_code_data.csv
├── .streamlit/
│   └── secrets.toml                  # Streamlit Cloud secrets (not in git)
├── requirements.txt                   # Python dependencies
├── .env                              # Local API keys (not in git)
├── .gitignore
└── README.md
```

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Mapping**: Folium
- **Data Processing**: Pandas, GeoPandas
- **APIs**: TfL Journey Planner API
- **Deployment**: Streamlit Cloud

## 📊 Data Sources

- **TfL Journey Data**: [Transport for London Journey Planner API](https://api.tfl.gov.uk/)
- **Council Tax**: [London Datastore - Council Tax Charges](https://data.london.gov.uk/dataset/council-tax-charges-bands-borough-expnl/)
- **Rent Prices**: [ONS - Private Rental Market in London (2024-2025)](https://www.ons.gov.uk/economy/inflationandpriceindices/adhocs/2923privaterentalmarketinlondonjuly2024tojune2025)
- **Postcode Data**: London postcode to borough mapping

## 📝 Important Notes

- Council tax and rent data are **averages by borough** and for reference only
- Actual costs may vary based on specific property and location
- Journey costs are estimates based on TfL fare data
- Fare capping is approximate and may vary by zones
- Data is current as of 2024-2025 tax year


## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **Transport for London (TfL)** for providing the Journey Planner API
- **London Datastore** for council tax data
- **Office for National Statistics** for rental price data
- **Streamlit** for the amazing framework
- **Folium** for interactive map visualization

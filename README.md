# Housing and Living Cost in London

This project provides tools to analyze housing and living costs in London, including comprehensive journey planning, travel cost estimation, and route visualization using Transport for London (TfL) data.

## Features

### 🚇 Route Calculator (`route_calculator.py`)

A comprehensive travel planning tool with the following capabilities:

#### Journey Planning
- **Interactive Journey Selection**: Browse all available route options and select your preferred journey
- **Multiple Journey Options**: View and compare different routes between two locations
- **Detailed Journey Instructions**: Step-by-step directions for each leg of the journey
- **Smart Route Filtering**: Automatically filters out duplicate routes with the same start/end stations

#### Travel Cost Analysis
- **Single Journey Fares**: Get accurate fare information from TfL API
- **Monthly Commute Cost**: Calculate estimated monthly commuting expenses
- **Cost Breakdown**: View daily, weekly, monthly, and annual cost estimates
- **Fare Capping**: Includes daily and monthly cap calculations

#### Route Visualization
- **Interactive Maps**: Visual representation of your journey on an interactive map
- **Color-Coded Routes**: Different transport modes shown in different colors
- **Station Markers**: Start, end, and transfer points clearly marked
- **Route Details**: Click markers and paths for journey information

#### Advanced Options
- **Transport Mode Selection**: Choose specific modes (tube, bus, DLR, overground, etc.)
- **Journey Preferences**: Optimize for least time, least walking, or least interchanges
- **Via Points**: Add intermediate stops to your journey
- **Time Scheduling**: Plan journeys for specific departure or arrival times
- **Date Selection**: Plan journeys for any date (defaults to today)

#### Additional Features
- **OSRM Integration**: Get driving, walking, and cycling distances
- **Haversine Distance**: Calculate straight-line distances between points
- **Journey Caching**: Automatically caches the last journey for reuse

## Installation

### Prerequisites
- Python 3.8+
- TfL API Key ([Get one here](https://api-portal.tfl.gov.uk/))

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd housing_in_london
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

4. Add your TfL API key to `.env`:
```
TFL_APP_KEY=your_api_key_here
```

## Usage

### Basic Example

```python
from route_calculator import TravelCalculator

# Initialize calculator
calculator = TravelCalculator()

# Interactive journey selection
journey = calculator.select_journey_option('IG3 8EE', 'EC2Y 5BL')

# Print detailed instructions
calculator.print_journey_instructions()

# Visualize on map
calculator.visualize_journey()

# Calculate monthly costs
monthly_cost = calculator.calculate_monthly_commute_cost()
print(f"Monthly cost: £{monthly_cost['monthly_cost']:.2f}")
```

### Advanced Usage

```python
# Journey with specific options
journey = calculator.get_tfl_journey(
    from_location='IG3 8EE',
    to_location='EC2Y 5BL',
    mode='tube,bus',
    journey_preference='leasttime',
    time='0900',  # 9:00 AM
    date='20250120',  # January 20, 2025
    time_is_arrival=False,
    via='Liverpool Street'
)

# Get all journey options
all_options = calculator.get_all_journey_options('IG3 8EE', 'EC2Y 5BL')

# Calculate driving distance
route = calculator.get_osrm_route(
    from_coords=(-0.1276, 51.5014),
    to_coords=(-0.0753, 51.5055),
    profile='driving'
)
```

## API Parameters

### Journey Parameters
- `from_location`: Starting postcode (e.g., 'SW1A 1AA')
- `to_location`: Destination postcode (e.g., 'E1 6AN')
- `mode`: Transport modes (default: all modes)
  - Options: `tube`, `bus`, `dlr`, `overground`, `tram`, `national-rail`, `walking`, `cycle`
- `journey_preference`: Route optimization
  - `leasttime`: Fastest journey
  - `leastwalking`: Minimize walking
  - `leastinterchange`: Fewest transfers
- `time`: Time in HHmm format (e.g., '0900' for 9:00 AM)
- `date`: Date in YYYYMMDD format (e.g., '20250115', defaults to today)
- `time_is_arrival`: Boolean - True for arrival time, False for departure time
- `via`: Optional via point (station or location name)

## Output

### Journey Information
- Duration in minutes
- Number of legs/transfers
- Fare information (if available)
- Start and arrival times
- Detailed step-by-step instructions

### Cost Estimates
- Single journey fare
- Daily commute cost (return journey)
- Weekly cost
- Monthly cost (with and without capping)
- Annual cost

### Map Visualization
- HTML file with interactive map
- Color-coded routes by transport mode
- Clickable markers and paths
- Journey summary legend

## Project Structure

```
housing_in_london/
├── route_calculator.py      # Main travel calculator module
├── visualize_postcodes.py   # Postcode visualization tools
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your API keys (not in git)
└── README.md              # This file
```

## Dependencies

- `requests`: API calls to TfL
- `folium`: Interactive map visualization
- `python-dotenv`: Environment variable management
- Additional dependencies in `requirements.txt`

## Contributing

Contributions are welcome! Please ensure all new features include:
- Clear documentation
- Example usage
- Error handling

## License

[Add your license here]

## Acknowledgments

- Transport for London (TfL) for providing the Journey Planner API
- OpenStreetMap and OSRM for routing data
- Folium for map visualization

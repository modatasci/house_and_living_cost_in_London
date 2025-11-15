"""
Route and Travel Cost Calculator for London Housing Project

Supports:
- TfL API for public transport routing and fares
- OSRM for driving/walking distances
- Haversine distance as fallback
"""

import requests
import os
from typing import Dict, Optional, Tuple, List
from math import radians, cos, sin, asin, sqrt
from dotenv import load_dotenv
import folium
from folium import PolyLine, Marker, Icon
from datetime import datetime

# Load environment variables
load_dotenv()


class TravelCalculator:
    """Calculate travel routes, times, and costs in London"""

    def __init__(self, tfl_app_key: Optional[str] = None):
        """
        Initialize travel calculator

        Args:
            tfl_app_key: TfL API key (optional, will try to load from .env)
        """
        self.tfl_app_key = tfl_app_key or os.getenv('TFL_APP_KEY')
        self.tfl_base_url = "https://api.tfl.gov.uk"
        self.osrm_base_url = "http://router.project-osrm.org"
        self.last_journey = None  # Cache last journey result

    def get_tfl_journey(
        self,
        from_location: str,
        to_location: str,
        mode: str = None,
        time_is_arrival: bool = False,
        via: Optional[str] = None,
        journey_preference: Optional[str] = None,
        time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict:
        """
        Get journey information from TfL API

        Args:
            from_location: Starting postcode (e.g., 'SW1A 1AA')
            to_location: Destination postcode (e.g., 'E1 6AN')
            mode: Transport modes (comma-separated)
            time_is_arrival: Whether time is arrival time (default: departure)
            via: Optional via point (e.g., 'Liverpool Street')
            journey_preference: Journey preference - "leastinterchange", "leasttime", or "leastwalking"
            time: Time in format HHmm (e.g., '0900' for 9am, '1430' for 2:30pm)
            date: Date in format YYYYMMDD (e.g., '20250115' for Jan 15, 2025). Defaults to today.

        Returns:
            Dict with journey information or error
        """
        if not self.tfl_app_key:
            return {
                'error': 'TfL API key not found. Set TFL_APP_KEY in .env file',
                'success': False
            }

        # URL encode postcodes
        from_encoded = from_location.replace(' ', '%20')
        to_encoded = to_location.replace(' ', '%20')
        via_encoded = via.replace(' ', '%20') if via else None

        # Set default date to today if not provided
        if date is None:
            date = datetime.now().strftime('%Y%m%d')


        url = f"{self.tfl_base_url}/Journey/JourneyResults/{from_encoded}/to/{to_encoded}"

        params = {
            'app_key': self.tfl_app_key,
            'mode': mode,
            'timeIs': 'Arriving' if time_is_arrival else 'Departing'
        }

        if via_encoded:
            params['via'] = via_encoded

        if journey_preference:
            params['journeyPreference'] = journey_preference

        if time:
            params['time'] = time

        # Always include date (defaults to today)
        params['date'] = date

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse first journey option
            if data.get('journeys') and len(data['journeys']) > 0:
                journey = data['journeys'][0]

                result = {
                    'success': True,
                    'duration_minutes': journey.get('duration', 0),
                    'arrival_time': journey.get('arrivalDateTime'),
                    'start_time': journey.get('startDateTime'),
                    'legs': len(journey.get('legs', [])),
                    'fare': self._extract_fare(journey),
                    'raw_data': journey
                }
            else:
                result = {
                    'success': False,
                    'error': 'No journey found',
                    'raw_data': data
                }

        except requests.exceptions.RequestException as e:
            result = {
                'success': False,
                'error': f'API request failed: {str(e)}'
            }

        # Cache the result
        self.last_journey = result
        return result

    def _extract_fare(self, journey: Dict) -> Dict:
        """Extract fare information from journey data"""
        fare_info = {
            'total_cost': None,
            'peak_single': None,
            'off_peak_single': None,
            'zones': None
        }

        if 'fare' in journey:
            fare_data = journey['fare']

            # Try to get total cost
            if 'totalCost' in fare_data:
                total_cost = fare_data['totalCost']
                if total_cost and total_cost > 0:
                    fare_info['total_cost'] = total_cost / 100  # Convert pence to pounds

            # If totalCost is not available or is 0, try to get from fares breakdown
            if not fare_info['total_cost'] and 'fares' in fare_data and len(fare_data['fares']) > 0:
                first_fare = fare_data['fares'][0]

                # Try different fare fields
                if 'lowZone' in first_fare and first_fare['lowZone'] > 0:
                    fare_info['total_cost'] = first_fare['lowZone'] / 100
                    fare_info['off_peak_single'] = first_fare['lowZone'] / 100
                elif 'highZone' in first_fare and first_fare['highZone'] > 0:
                    fare_info['total_cost'] = first_fare['highZone'] / 100
                    fare_info['peak_single'] = first_fare['highZone'] / 100

                # Store both if available
                if 'highZone' in first_fare:
                    fare_info['peak_single'] = first_fare.get('highZone', 0) / 100
                if 'lowZone' in first_fare:
                    fare_info['off_peak_single'] = first_fare.get('lowZone', 0) / 100

            # Get zones
            if 'caveatText' in fare_data:
                fare_info['zones'] = fare_data.get('caveatText', '')

        return fare_info

    def get_all_journey_options(self, from_location: str, to_location: str, **kwargs) -> Optional[List[Dict]]:
        """
        Get all available journey options from TfL API

        Args:
            from_location: Starting postcode
            to_location: Destination postcode
            **kwargs: Additional parameters (mode, via, journey_preference, etc.)

        Returns:
            List of journey dictionaries or None if error
        """
        if not self.tfl_app_key:
            return None

        # URL encode postcodes
        from_encoded = from_location.replace(' ', '%20')
        to_encoded = to_location.replace(' ', '%20')

        url = f"{self.tfl_base_url}/Journey/JourneyResults/{from_encoded}/to/{to_encoded}"

        # Build params
        params = {
            'app_key': self.tfl_app_key,
            'timeIs': 'Arriving' if kwargs.get('time_is_arrival') else 'Departing'
        }

        # Add optional parameters
        if kwargs.get('mode'):
            params['mode'] = kwargs['mode']
        if kwargs.get('via'):
            params['via'] = kwargs['via'].replace(' ', '%20')
        if kwargs.get('journey_preference'):
            params['journeyPreference'] = kwargs['journey_preference']
        if kwargs.get('time'):
            params['time'] = kwargs['time']

        # Set date (defaults to today)
        params['date'] = kwargs.get('date', datetime.now().strftime('%Y%m%d'))

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            journeys = data.get('journeys', [])

            # Filter out duplicate routes (same start and end stations)
            if journeys:
                filtered_journeys = []
                seen_routes = set()  # Track unique start-end combinations

                for journey in journeys:
                    legs = journey.get('legs', [])
                    if legs and len(legs) > 0:
                        first_leg = legs[0]
                        last_leg = legs[-1]

                        start_station = first_leg.get('departurePoint', {}).get('commonName', '').strip()
                        end_station = last_leg.get('arrivalPoint', {}).get('commonName', '').strip()

                        # Create a unique key for this route
                        route_key = (start_station.lower(), end_station.lower())

                        # Only include if we haven't seen this start-end combination before
                        if route_key not in seen_routes:
                            seen_routes.add(route_key)
                            filtered_journeys.append(journey)

                return filtered_journeys if filtered_journeys else None

            return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching journey options: {str(e)}")
            return None

    def print_all_journey_options(self, from_location: str, to_location: str, **kwargs) -> Optional[Dict]:
        """
        Print all available journey options in short format and return all journeys data

        Args:
            from_location: Starting postcode
            to_location: Destination postcode
            **kwargs: Additional parameters to pass to get_tfl_journey (mode, via, journey_preference, etc.)

        Returns:
            Dict with all journeys data or None if error
        """
        if not self.tfl_app_key:
            print("TfL API key not found")
            return None

        # URL encode postcodes
        from_encoded = from_location.replace(' ', '%20')
        to_encoded = to_location.replace(' ', '%20')

        url = f"{self.tfl_base_url}/Journey/JourneyResults/{from_encoded}/to/{to_encoded}"

        # Build params
        params = {
            'app_key': self.tfl_app_key,
            'timeIs': 'Arriving' if kwargs.get('time_is_arrival') else 'Departing'
        }

        # Add optional parameters
        if kwargs.get('mode'):
            params['mode'] = kwargs['mode']
        if kwargs.get('via'):
            params['via'] = kwargs['via'].replace(' ', '%20')
        if kwargs.get('journey_preference'):
            params['journeyPreference'] = kwargs['journey_preference']
        if kwargs.get('time'):
            params['time'] = kwargs['time']

        # Set date (defaults to today)
        params['date'] = kwargs.get('date', datetime.now().strftime('%Y%m%d'))

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            journeys = data.get('journeys', [])

            if not journeys:
                print("No journey options found")
                return None

            # Filter out duplicate routes (same start and end stations)
            filtered_journeys = []
            seen_routes = set()  # Track unique start-end combinations

            for journey in journeys:
                legs = journey.get('legs', [])
                if legs and len(legs) > 0:
                    first_leg = legs[0]
                    last_leg = legs[-1]

                    start_station = first_leg.get('departurePoint', {}).get('commonName', '').strip()
                    end_station = last_leg.get('arrivalPoint', {}).get('commonName', '').strip()

                    # Create a unique key for this route
                    route_key = (start_station.lower(), end_station.lower())

                    # Only include if we haven't seen this start-end combination before
                    if route_key not in seen_routes:
                        seen_routes.add(route_key)
                        filtered_journeys.append(journey)

            if not filtered_journeys:
                print("No valid journey options found (filtered out duplicate routes)")
                return None

            journeys = filtered_journeys

            print("\n" + "=" * 80)
            print(f"JOURNEY OPTIONS: {from_location} → {to_location}")
            print(f"Found {len(journeys)} option(s)")
            print("=" * 80)

            for i, journey in enumerate(journeys, 1):
                duration = journey.get('duration', 0)
                legs = journey.get('legs', [])

                # Get fare info
                fare_data = self._extract_fare(journey)
                fare_str = f"£{fare_data.get('total_cost', 0):.2f}" if fare_data.get('total_cost') else "N/A"

                # Build mode summary with station names
                route_summary = []
                for j, leg in enumerate(legs):
                    mode_name = leg.get('mode', {}).get('name', 'unknown')

                    # Get departure and arrival points
                    if j == 0:  # First leg - add departure point
                        dep_point = leg.get('departurePoint', {})
                        dep_name = dep_point.get('commonName', 'Unknown')
                        route_summary.append(dep_name)

                    # Add mode
                    route_summary.append(f"[{mode_name}]")

                    # Add arrival point
                    arr_point = leg.get('arrivalPoint', {})
                    arr_name = arr_point.get('commonName', 'Unknown')
                    route_summary.append(arr_name)

                route_str = " → ".join(route_summary)

                # Get start and end times
                start_time = journey.get('startDateTime', '')
                arrival_time = journey.get('arrivalDateTime', '')

                # Format times (extract time part)
                if start_time:
                    start_time = start_time.split('T')[1][:5] if 'T' in start_time else start_time
                if arrival_time:
                    arrival_time = arrival_time.split('T')[1][:5] if 'T' in arrival_time else arrival_time

                print(f"\nOption {i}:")
                print(f"  Duration: {duration} min | Fare: {fare_str} | Legs: {len(legs)}")
                print(f"  Time: {start_time} - {arrival_time}")
                print(f"  Route: {route_str}")

            print("\n" + "=" * 80)

            return data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching journey options: {str(e)}")
            return None

    def select_journey_option(self, from_location: str, to_location: str, **kwargs) -> Optional[Dict]:
        """
        Display all journey options and let user select one

        Args:
            from_location: Starting postcode
            to_location: Destination postcode
            **kwargs: Additional parameters (mode, via, journey_preference, etc.)

        Returns:
            Selected journey in the format returned by get_tfl_journey(), or None if error
        """
        journeys = self.get_all_journey_options(from_location, to_location, **kwargs)

        if not journeys:
            print("No journey options found")
            return None

        print("\n" + "=" * 80)
        print(f"JOURNEY OPTIONS: {from_location} → {to_location}")
        print(f"Found {len(journeys)} option(s)")
        print("=" * 80)

        for i, journey in enumerate(journeys, 1):
            duration = journey.get('duration', 0)
            legs = journey.get('legs', [])

            # Get fare info
            fare_data = self._extract_fare(journey)
            fare_str = f"£{fare_data.get('total_cost', 0):.2f}" if fare_data.get('total_cost') else "N/A"

            # Build mode summary with station names
            route_summary = []
            for j, leg in enumerate(legs):
                mode_name = leg.get('mode', {}).get('name', 'unknown')

                # Get departure and arrival points
                if j == 0:  # First leg - add departure point
                    dep_point = leg.get('departurePoint', {})
                    dep_name = dep_point.get('commonName', 'Unknown')
                    route_summary.append(dep_name)

                # Add mode
                route_summary.append(f"[{mode_name}]")

                # Add arrival point
                arr_point = leg.get('arrivalPoint', {})
                arr_name = arr_point.get('commonName', 'Unknown')
                route_summary.append(arr_name)

            route_str = " → ".join(route_summary)

            # Get start and end times
            start_time = journey.get('startDateTime', '')
            arrival_time = journey.get('arrivalDateTime', '')

            # Format times (extract time part)
            if start_time:
                start_time = start_time.split('T')[1][:5] if 'T' in start_time else start_time
            if arrival_time:
                arrival_time = arrival_time.split('T')[1][:5] if 'T' in arrival_time else arrival_time

            print(f"\nOption {i}:")
            print(f"  Duration: {duration} min | Fare: {fare_str} | Legs: {len(legs)}")
            print(f"  Time: {start_time} - {arrival_time}")
            print(f"  Route: {route_str}")

        print("\n" + "=" * 80)

        # Ask user to select
        while True:
            try:
                choice = input(f"\nSelect journey option (1-{len(journeys)}) or 'q' to quit: ").strip()

                if choice.lower() == 'q':
                    print("Journey selection cancelled")
                    return None

                choice_num = int(choice)
                if 1 <= choice_num <= len(journeys):
                    selected_journey = journeys[choice_num - 1]

                    # Format the result like get_tfl_journey() does
                    result = {
                        'success': True,
                        'duration_minutes': selected_journey.get('duration', 0),
                        'arrival_time': selected_journey.get('arrivalDateTime'),
                        'start_time': selected_journey.get('startDateTime'),
                        'legs': len(selected_journey.get('legs', [])),
                        'fare': self._extract_fare(selected_journey),
                        'raw_data': selected_journey
                    }

                    # Cache the selected journey
                    self.last_journey = result

                    print(f"\n✓ Selected Option {choice_num}")
                    return result
                else:
                    print(f"Please enter a number between 1 and {len(journeys)}")

            except ValueError:
                print("Invalid input. Please enter a number or 'q' to quit")
            except KeyboardInterrupt:
                print("\nJourney selection cancelled")
                return None

    def print_journey_instructions(self, journey: Optional[Dict] = None) -> None:
        """
        Print formatted journey instructions from TfL journey data

        Args:
            journey: Journey data from get_tfl_journey() (optional, will use last_journey)
        """
        if journey is None:
            journey = self.last_journey

        if journey is None:
            print("No journey data available. Call get_tfl_journey() first.")
            return

        if not journey.get('success'):
            print(f"Cannot print instructions: {journey.get('error', 'Unknown error')}")
            return

        raw_data = journey.get('raw_data', {})
        legs = raw_data.get('legs', [])

        if not legs:
            print("No journey instructions available")
            return

        print("\n" + "=" * 60)
        print("JOURNEY INSTRUCTIONS")
        print("=" * 60)
        print(f"Total Duration: {journey['duration_minutes']} minutes")
        print(f"Total Legs: {len(legs)}")

        if journey.get('fare', {}).get('total_cost'):
            print(f"Estimated Fare: £{journey['fare']['total_cost']:.2f}")

        print("=" * 60)

        for i, leg in enumerate(legs, 1):
            duration = leg.get('duration', 0)
            mode = leg.get('mode', {}).get('name', 'Unknown')

            # Get departure/arrival points
            departure = leg.get('departurePoint', {})
            arrival = leg.get('arrivalPoint', {})
            dep_name = departure.get('commonName', 'Unknown')
            arr_name = arrival.get('commonName', 'Unknown')

            print(f"\nLeg {i}: {mode.upper()}")
            print(f"  From: {dep_name}")
            print(f"  To: {arr_name}")
            print(f"  Duration: {duration} minutes")

            # Get instruction details
            instruction = leg.get('instruction', {})
            summary = instruction.get('summary', '')
            detailed = instruction.get('detailed', '')

            if summary:
                print(f"  Summary: {summary}")
            if detailed:
                print(f"  Details: {detailed}")

            # Get route name (for buses, tubes, etc.)
            route_options = leg.get('routeOptions', [])
            if route_options:
                for option in route_options:
                    route_name = option.get('name', '')
                    if route_name:
                        print(f"  Route: {route_name}")
                        break

            # Get disruptions if any
            disruptions = leg.get('disruptions', [])
            if disruptions:
                print(f"  ⚠ Disruptions: {len(disruptions)} active")

        print("\n" + "=" * 60)

    def visualize_journey(
        self,
        journey: Optional[Dict] = None,
        output_file: str = 'journey_map.html',
        open_browser: bool = True
    ) -> Optional[str]:
        """
        Visualize journey on an interactive map using Folium

        Args:
            journey: Journey data from get_tfl_journey() (optional, will use last_journey)
            output_file: Output HTML file path
            open_browser: Whether to open the map in browser automatically

        Returns:
            Path to HTML file if successful, None otherwise
        """
        if journey is None:
            journey = self.last_journey

        if journey is None:
            print("No journey data available. Call get_tfl_journey() first.")
            return None

        if not journey.get('success'):
            print(f"Cannot visualize: {journey.get('error', 'Unknown error')}")
            return None

        raw_data = journey.get('raw_data', {})
        legs = raw_data.get('legs', [])

        if not legs:
            print("No journey data to visualize")
            return None

        # Create map centered on London
        m = folium.Map(
            location=[51.5074, -0.1278],
            zoom_start=12,
            tiles='OpenStreetMap'
        )

        # Color scheme for different transport modes
        mode_colors = {
            'tube': '#003688',
            'bus': '#DC241F',
            'walking': '#00A575',
            'dlr': '#00A575',
            'overground': '#EE7C0E',
            'national-rail': '#0019A8',
            'tram': '#66CC00',
            'cycle': '#0098D4',
            'river-bus': '#00AFE8',
        }

        all_coords = []

        for i, leg in enumerate(legs, 1):
            mode_name = leg.get('mode', {}).get('name', 'unknown').lower()
            color = mode_colors.get(mode_name, '#666666')

            # Get departure point
            departure = leg.get('departurePoint', {})
            dep_lat = departure.get('lat')
            dep_lon = departure.get('lon')
            dep_name = departure.get('commonName', 'Unknown')

            # Get arrival point
            arrival = leg.get('arrivalPoint', {})
            arr_lat = arrival.get('lat')
            arr_lon = arrival.get('lon')
            arr_name = arrival.get('commonName', 'Unknown')

            if dep_lat and dep_lon:
                all_coords.append([dep_lat, dep_lon])

                # Add departure marker (only for first leg)
                if i == 1:
                    folium.Marker(
                        [dep_lat, dep_lon],
                        popup=f"<b>START</b><br>{dep_name}",
                        icon=folium.Icon(color='green', icon='play', prefix='fa'),
                        tooltip=dep_name
                    ).add_to(m)

            if arr_lat and arr_lon:
                all_coords.append([arr_lat, arr_lon])

            # Get path coordinates if available
            path = leg.get('path', {})
            line_string = path.get('lineString', [])

            if line_string:
                # TfL returns coordinates in different formats, handle both
                try:
                    # Try format: [[lat, lon], [lat, lon], ...]
                    if isinstance(line_string[0], list):
                        path_coords = [[coord[0], coord[1]] for coord in line_string]
                    # Try format: "lat,lon lat,lon lat,lon"
                    elif isinstance(line_string, str):
                        coords = line_string.strip('[]').split(',')
                        path_coords = []
                        for i in range(0, len(coords), 2):
                            if i + 1 < len(coords):
                                path_coords.append([float(coords[i]), float(coords[i+1])])
                    else:
                        path_coords = []
                except (IndexError, ValueError, TypeError):
                    # If parsing fails, draw straight line
                    if dep_lat and dep_lon and arr_lat and arr_lon:
                        path_coords = [[dep_lat, dep_lon], [arr_lat, arr_lon]]
                    else:
                        path_coords = []
            elif dep_lat and dep_lon and arr_lat and arr_lon:
                # If no path, draw straight line
                path_coords = [[dep_lat, dep_lon], [arr_lat, arr_lon]]
            else:
                path_coords = []

            # Draw path
            if path_coords:
                folium.PolyLine(
                    path_coords,
                    color=color,
                    weight=5,
                    opacity=0.8,
                    popup=f"Leg {i}: {mode_name.upper()}<br>{dep_name} → {arr_name}"
                ).add_to(m)

            # Add arrival marker (for all legs)
            if arr_lat and arr_lon:
                icon_type = 'stop' if i < len(legs) else 'flag-checkered'
                icon_color = 'blue' if i < len(legs) else 'red'

                folium.Marker(
                    [arr_lat, arr_lon],
                    popup=f"<b>{'STOP ' + str(i) if i < len(legs) else 'END'}</b><br>{arr_name}",
                    icon=folium.Icon(color=icon_color, icon=icon_type, prefix='fa'),
                    tooltip=arr_name
                ).add_to(m)

        # Fit map bounds to show all points
        if all_coords:
            m.fit_bounds(all_coords)

        # Add legend
        legend_html = '''
        <div style="position: fixed;
                    bottom: 50px; right: 50px; width: 200px; height: auto;
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius: 5px; padding: 10px">
        <h4 style="margin-top:0">Transport Modes</h4>
        '''

        for mode, color in mode_colors.items():
            legend_html += f'<p><span style="background:{color}; width:20px; height:10px; display:inline-block;"></span> {mode.title()}</p>'

        legend_html += f'''
        <hr>
        <p><b>Duration:</b> {journey.get('duration_minutes')} min</p>
        '''

        if journey.get('fare', {}).get('total_cost'):
            legend_html += f"<p><b>Fare:</b> £{journey['fare']['total_cost']:.2f}</p>"

        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))

        # Save map
        m.save(output_file)
        print(f"\n✓ Map saved to: {output_file}")

        # Open in browser
        if open_browser:
            import webbrowser
            webbrowser.open('file://' + os.path.abspath(output_file))
            print(f"✓ Opening map in browser...")

        return output_file

    def calculate_monthly_commute_cost(
        self,
        from_location: Optional[str] = None,
        to_location: Optional[str] = None,
        days_per_week: int = 5,
        use_travelcard: bool = True,
        journey: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate estimated monthly commute cost

        Args:
            from_location: Starting postcode (optional if using cached journey)
            to_location: Destination postcode (optional if using cached journey)
            days_per_week: Working days per week (default: 5)
            use_travelcard: Whether to use travelcard pricing (usually cheaper)
            journey: Journey data to use (optional, will use last_journey or fetch new)

        Returns:
            Dict with cost estimates
        """
        # Use provided journey, or cached journey, or fetch new one
        if journey is None:
            if from_location and to_location:
                journey = self.get_tfl_journey(from_location, to_location)
            elif self.last_journey:
                journey = self.last_journey
            else:
                return {
                    'success': False,
                    'error': 'No journey data available. Either provide from/to locations or call get_tfl_journey() first.'
                }

        if not journey.get('success'):
            return journey

        fare = journey.get('fare', {})
        single_fare = fare.get('total_cost') or 0

        # Check if fare data is available
        if single_fare == 0:
            # Try alternative fare sources
            if fare.get('off_peak_single'):
                single_fare = fare.get('off_peak_single')
            elif fare.get('peak_single'):
                single_fare = fare.get('peak_single')

        # Warn if still no fare
        fare_warning = None
        if single_fare == 0:
            fare_warning = "⚠ Fare information not available from TfL API. Cost estimates will be £0."

        # Estimates (rough calculations)
        daily_cost = single_fare * 2  # Return journey
        weekly_cost = daily_cost * days_per_week
        monthly_cost = weekly_cost * 4.33  # Average weeks per month
        annual_cost = monthly_cost * 12

        # Daily cap (approximate - varies by zones)
        daily_cap = single_fare * 2.5  # Rough estimate
        monthly_cap = daily_cap * 20  # Approximate monthly cap

        result = {
            'success': True,
            'single_fare': single_fare,
            'daily_cost': daily_cost,
            'weekly_cost': weekly_cost,
            'monthly_cost': monthly_cost,
            'monthly_cost_with_cap': min(monthly_cost, monthly_cap),
            'annual_cost': annual_cost,
            'duration_minutes': journey.get('duration_minutes'),
            'journey_info': journey
        }

        if fare_warning:
            result['warning'] = fare_warning

        return result

    def get_osrm_route(
        self,
        from_coords: Tuple[float, float],
        to_coords: Tuple[float, float],
        profile: str = 'driving'
    ) -> Dict:
        """
        Get route using OSRM (Open Source Routing Machine)

        Args:
            from_coords: (longitude, latitude) of start
            to_coords: (longitude, latitude) of end
            profile: 'driving', 'walking', or 'cycling'

        Returns:
            Dict with route information
        """
        from_lon, from_lat = from_coords
        to_lon, to_lat = to_coords

        url = f"{self.osrm_base_url}/route/v1/{profile}/{from_lon},{from_lat};{to_lon},{to_lat}"
        params = {'overview': 'false', 'steps': 'false'}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]

                return {
                    'success': True,
                    'distance_km': route['distance'] / 1000,
                    'distance_miles': route['distance'] / 1609.34,
                    'duration_minutes': route['duration'] / 60,
                    'duration_hours': route['duration'] / 3600,
                    'profile': profile
                }
            else:
                return {
                    'success': False,
                    'error': 'No route found'
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'OSRM request failed: {str(e)}'
            }

    @staticmethod
    def haversine_distance(
        coord1: Tuple[float, float],
        coord2: Tuple[float, float],
        unit: str = 'km'
    ) -> float:
        """
        Calculate straight-line distance between two points using Haversine formula

        Args:
            coord1: (longitude, latitude) of first point
            coord2: (longitude, latitude) of second point
            unit: 'km' or 'miles'

        Returns:
            Distance in specified unit
        """
        lon1, lat1 = coord1
        lon2, lat2 = coord2

        # Convert to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # Earth radius in km
        r = 6371

        distance_km = c * r

        if unit == 'miles':
            return distance_km * 0.621371
        return distance_km


# Example usage and testing
if __name__ == "__main__":
    print("Testing Travel Calculator...\n")

    calculator = TravelCalculator()

    # Test 1: TfL Journey with Interactive Selection
    print("=" * 50)
    print("Test 1: TfL Journey with Interactive Selection")
    print("=" * 50)
    from_loc = 'IG3 8EE'
    to_loc = 'EC2Y 5BL' #benoy: 'EC2Y 5BL' 1 Oxford St, London W1D 3BG
    time='0830'
    date='20251115'
    # time=None
    # date=None

    # Let user select from all available journey options
    journey = calculator.select_journey_option(from_loc, to_loc,time=time,date=date)

    if journey and journey.get('success'):
        print(f"\n✓ Journey Duration: {journey['duration_minutes']} minutes")
        print(f"✓ Number of legs: {journey['legs']}")
        fare = journey.get('fare', {})
        if fare.get('total_cost'):
            print(f"✓ Single fare: £{fare['total_cost']:.2f}")

        # Print detailed journey instructions (using cached journey)
        calculator.print_journey_instructions()

        # Visualize journey on map (using cached journey)
        calculator.visualize_journey()
    else:
        print(f"✗ No journey selected or error occurred")

    # Test 2: Monthly cost (using cached journey - no need to refetch)
    print("\n" + "=" * 50)
    print("Test 2: Monthly Commute Cost (using cached journey)")
    print("=" * 50)

    monthly = calculator.calculate_monthly_commute_cost(journey=journey)

    if monthly.get('success'):
        if monthly.get('warning'):
            print(f"\n{monthly['warning']}")
        print(f"✓ Single fare: £{monthly['single_fare']:.2f}")
        print(f"✓ Daily cost: £{monthly['daily_cost']:.2f}")
        print(f"✓ Monthly cost: £{monthly['monthly_cost']:.2f}")
        print(f"✓ Monthly (with cap): £{monthly['monthly_cost_with_cap']:.2f}")
        print(f"✓ Journey time: {monthly['duration_minutes']} minutes")
    else:
        print(f"✗ Error: {monthly.get('error')}")

    # Test 3: OSRM Route
    print("\n" + "=" * 50)
    print("Test 3: OSRM Driving Distance")
    print("=" * 50)

    # Westminster to Tower Bridge coordinates
    osrm = calculator.get_osrm_route(
        (-0.1276, 51.5014),  # Westminster
        (-0.0753, 51.5055)   # Tower Bridge
    )

    if osrm.get('success'):
        print(f"✓ Distance: {osrm['distance_km']:.2f} km ({osrm['distance_miles']:.2f} miles)")
        print(f"✓ Duration: {osrm['duration_minutes']:.1f} minutes")
    else:
        print(f"✗ Error: {osrm.get('error')}")

    # Test 4: Haversine distance
    print("\n" + "=" * 50)
    print("Test 4: Straight-line Distance (Haversine)")
    print("=" * 50)

    distance_km = calculator.haversine_distance(
        (-0.1276, 51.5014),  # Westminster
        (-0.0753, 51.5055)   # Tower Bridge
    )
    print(f"✓ Straight-line distance: {distance_km:.2f} km")

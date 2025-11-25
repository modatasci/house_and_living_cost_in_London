"""
Streamlit UI for London Housing Route Calculator
Allows users to calculate commute routes and costs between postcodes
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from route_calculator import TravelCalculator
from get_living_cost import CouncilTaxLookup
from get_living_cost import AverageRentCost
from post_code_data_processor import get_borough_from_postcode
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Where to live in London?",
    page_icon="🏠",
    layout="wide"
)

# Get TFL API key from Streamlit secrets or environment variables
def get_tfl_api_key():
    """Get TFL API key from Streamlit secrets (cloud) or environment (local)"""
    try:
        # Try Streamlit secrets first (for cloud deployment)
        return st.secrets["TFL_APP_KEY"]
    except (KeyError, FileNotFoundError, AttributeError):
        # Fall back to environment variable (for local development)
        return os.getenv("TFL_APP_KEY")

# Cache the lookup instances
@st.cache_resource
def get_council_tax_lookup():
    """Initialize and return CouncilTaxLookup instance"""
    return CouncilTaxLookup()

@st.cache_resource
def get_rent_lookup():
    """Initialize and return AverageRentCost instance"""
    return AverageRentCost()

# Initialize calculator in session state
if 'calculator' not in st.session_state:
    tfl_key = get_tfl_api_key()
    st.session_state.calculator = TravelCalculator(tfl_app_key=tfl_key)
if 'journey_result' not in st.session_state:
    st.session_state.journey_result = None
if 'all_journeys' not in st.session_state:
    st.session_state.all_journeys = None
if 'council_tax_data' not in st.session_state:
    st.session_state.council_tax_data = None
if 'rent_data' not in st.session_state:
    st.session_state.rent_data = None
if 'traveling_days' not in st.session_state:
    st.session_state.traveling_days = 5
if 'saved_comparisons' not in st.session_state:
    st.session_state.saved_comparisons = []
if 'comparison_counter' not in st.session_state:
    st.session_state.comparison_counter = 0

# Title and description
st.title("🏠 Where to live in London?")
st.markdown("Calculate travel costs, council tax, and rent prices between London postcodes")

# Sidebar for inputs
with st.sidebar:
    st.header("Journey Details")

    # Location inputs
    from_postcode = st.text_input(
        "From (Home Postcode)",
        value="IG3 8EE",
        placeholder="e.g., SW1A 1AA"
    ).strip()

    to_postcode = st.text_input(
        "To (Office/School Postcode)",
        value="EC2Y 5BL",
        placeholder="e.g., E1 6AN"
    ).strip()

    st.divider()

    # Advanced options
    with st.expander("Journey Planner Advanced Options"):
        transport_mode = st.selectbox(
            "Transport Mode",
            ["All modes", "Tube only", "Bus only", "Walking"],
            help="Restrict to specific transport modes"
        )

        mode_param = None
        if transport_mode == "Tube only":
            mode_param = "tube"
        elif transport_mode == "Bus only":
            mode_param = "bus"
        elif transport_mode == "Walking":
            mode_param = "walking"

        journey_preference = st.selectbox(
            "Journey Preference",
            ["Least time", "Least interchange", "Least walking"],
            help="Optimize for different criteria"
        )

        pref_param = None
        if journey_preference == "Least time":
            pref_param = "leasttime"
        elif journey_preference == "Least interchange":
            pref_param = "leastinterchange"
        elif journey_preference == "Least walking":
            pref_param = "leastwalking"

        # Journey time selector
        journey_time = st.selectbox(
            "Journey Time",
            ["Current Time", "Rush Hour (8:30 AM)", "Off-Peak (11:00 AM)"],
            index=0,
            help="Select journey time to see different travel durations and costs"
        )

        # Map time selection to API format
        time_param = None
        time_label = "Current Time"
        if journey_time == "Rush Hour (8:30 AM)":
            time_param = "0830"
            time_label = "Rush Hour"
        elif journey_time == "Off-Peak (11:00 AM)":
            time_param = "1100"
            time_label = "Off-Peak"

        traveling_days_sidebar = st.selectbox(
            "Traveling Days per Week",
            [5, 4, 3, 2, 1],
            index=[5, 4, 3, 2, 1].index(st.session_state.traveling_days) if st.session_state.traveling_days in [5, 4, 3, 2, 1] else 0,
            help="Number of days you commute per week"
        )
        if traveling_days_sidebar != st.session_state.traveling_days:
            st.session_state.traveling_days = traveling_days_sidebar    

    st.divider()

    # Housing details
    st.subheader("Housing Details")

    # Council Tax Band selector
    council_tax_band = st.selectbox(
        "Council Tax Band",
        ["A", "B", "C", "D", "E", "F", "G", "H"],
        index=3,  # Default to Band D
        help="Select your property's council tax band"
    )

    # Bedroom category selector for rent
    bedroom_category = st.selectbox(
        "Bedroom Category",
        ["Room", "Studio", "One Bedroom", "Two Bedrooms", "Three Bedrooms", "Four or More Bedrooms"],
        index=2,  # Default to One Bedroom
        help="Select bedroom category for average rent calculation"
    )

    st.divider()

    # Calculate button
    calculate_button = st.button("🔍 Calculate Costs", type="primary", use_container_width=True)

# Main content area
if calculate_button:
    if not from_postcode or not to_postcode:
        st.error("Please enter both home and office postcodes")
    else:
        with st.spinner("Fetching journey options from TfL..."):
            # Get all journey options
            kwargs = {}
            if mode_param:
                kwargs['mode'] = mode_param
            if pref_param:
                kwargs['journey_preference'] = pref_param
            if time_param:
                kwargs['time'] = time_param

            journeys = st.session_state.calculator.get_all_journey_options(
                from_postcode,
                to_postcode,
                **kwargs
            )

            if journeys:
                st.session_state.all_journeys = journeys
                # Select first journey by default
                st.session_state.journey_result = {
                    'success': True,
                    'duration_minutes': journeys[0].get('duration', 0),
                    'arrival_time': journeys[0].get('arrivalDateTime'),
                    'start_time': journeys[0].get('startDateTime'),
                    'legs': len(journeys[0].get('legs', [])),
                    'fare': st.session_state.calculator._extract_fare(journeys[0]),
                    'raw_data': journeys[0]
                }
                st.session_state.calculator.last_journey = st.session_state.journey_result
                # Store journey time selection
                st.session_state.journey_time_label = time_label
            else:
                st.error("No journey options found. Please check your postcodes and try again.")
                st.session_state.journey_result = None
                st.session_state.all_journeys = None

        # Calculate council tax for home postcode
        with st.spinner("Calculating council tax..."):
            try:
                council_tax_lookup = get_council_tax_lookup()
                council_tax_monthly = council_tax_lookup.calculate_monthly_council_tax(from_postcode)

                if council_tax_monthly:
                    st.session_state.council_tax_data = {
                        'borough': council_tax_monthly.get('Local authority'),
                        'band': council_tax_band,
                        'monthly': council_tax_monthly.get(f'Band {council_tax_band}', 0),
                        'annual': council_tax_monthly.get(f'Band {council_tax_band}', 0) * 12 if council_tax_monthly.get(f'Band {council_tax_band}') else 0,
                        'all_bands': council_tax_monthly
                    }
                else:
                    st.warning(f"Could not find council tax data for postcode: {from_postcode}")
                    st.session_state.council_tax_data = None
            except Exception as e:
                st.error(f"Error calculating council tax: {str(e)}")
                st.session_state.council_tax_data = None

        # Calculate average rent for home postcode
        with st.spinner("Calculating average rent..."):
            try:
                rent_lookup = get_rent_lookup()
                rent_info = rent_lookup.get_average_rent_by_postcode(
                    from_postcode,
                    bedroom_category=bedroom_category,
                    use_median=True
                )

                if rent_info:
                    st.session_state.rent_data = {
                        'borough': rent_info.get('borough'),
                        'postcode': from_postcode,
                        'bedroom_category': bedroom_category,
                        'monthly_rent': rent_info.get('monthly_rent', 0),
                        'annual_rent': rent_info.get('annual_rent', 0),
                        'lower_quartile': rent_info.get('lower_quartile'),
                        'upper_quartile': rent_info.get('upper_quartile'),
                        'all_categories': rent_lookup.get_all_bedroom_categories(from_postcode)
                    }
                else:
                    st.warning(f"Could not find rent data for postcode: {from_postcode}")
                    st.session_state.rent_data = None
            except Exception as e:
                st.error(f"Error calculating rent: {str(e)}")
                st.session_state.rent_data = None

# Display results
if st.session_state.journey_result and st.session_state.journey_result.get('success'):
    journey = st.session_state.journey_result

    # Display journey route summary
    st.markdown("---")
    route_header_col1, route_header_col2, route_header_col3 = st.columns([1, 0.3, 1])

    # From postcodes and boroughs
    with route_header_col1:
        # Get borough for "from" location
        from_borough = "Unknown"
        if st.session_state.council_tax_data:
            from_borough = st.session_state.council_tax_data.get('borough', 'Unknown')
        elif st.session_state.rent_data:
            from_borough = st.session_state.rent_data.get('borough', 'Unknown')


        st.markdown(f"""
        ### 🏠 From
        **Postcode:** {from_postcode}
        **Borough:** {from_borough}
        """)

    with route_header_col2:
        st.markdown("<div style='text-align: center; padding-top: 30px; font-size: 24px;'>→</div>", unsafe_allow_html=True)

    # To postcodes
    with route_header_col3:
        to_borough = get_borough_from_postcode(to_postcode)
        st.markdown(f"""
        ### 🏢 To
        **Postcode:** {to_postcode}
        **Borough:** {to_borough}
        """)

    st.markdown("---")

    #-------------------------------------------------------------------------------------------------------------------------
    # region Journey options and council tax band selectors
    selector_col1, selector_col2 = st.columns([2, 1])

    with selector_col1:
        # Journey options selector
        if st.session_state.all_journeys and len(st.session_state.all_journeys) > 1:
            st.subheader("Journey Options")

            # Create option labels
            option_labels = []
            for i, j in enumerate(st.session_state.all_journeys, 1):
                duration = j.get('duration', 0)
                fare = st.session_state.calculator._extract_fare(j)
                fare_str = f"£{fare.get('total_cost', 0):.2f}" if fare.get('total_cost') else "N/A"
                legs = j.get('legs', [])

                # Build route summary with stations and lines
                route_parts = []
                for leg in legs:
                    mode_name = leg.get('mode', {}).get('name', 'unknown')

                    # Get line name if available
                    route_options = leg.get('routeOptions', [])
                    line_name = route_options[0].get('name', '') if route_options else ''

                    if mode_name in ['tube', 'bus', 'overground', 'dlr', 'tram', 'national-rail']:
                        if line_name:
                            route_parts.append(line_name)
                        else:
                            route_parts.append(mode_name.title())
                    elif mode_name == 'walking' and len(legs) > 1:
                        # Only show walking if it's part of a multi-leg journey
                        continue

                route_summary = " → ".join(route_parts) if route_parts else "Walking only"

                option_labels.append(f"Option {i}: {duration} min | {fare_str} | {route_summary}")

            selected_option = st.selectbox(
                "Choose your preferred route:",
                options=range(len(st.session_state.all_journeys)),
                format_func=lambda x: option_labels[x],
                key="journey_selector"
            )

            # Update selected journey
            selected_journey = st.session_state.all_journeys[selected_option]
            st.session_state.journey_result = {
                'success': True,
                'duration_minutes': selected_journey.get('duration', 0),
                'arrival_time': selected_journey.get('arrivalDateTime'),
                'start_time': selected_journey.get('startDateTime'),
                'legs': len(selected_journey.get('legs', [])),
                'fare': st.session_state.calculator._extract_fare(selected_journey),
                'raw_data': selected_journey
            }
            st.session_state.calculator.last_journey = st.session_state.journey_result
            journey = st.session_state.journey_result

        # Traveling days selector
        traveling_days = st.selectbox(
            "Traveling Days per Week:",
            [5, 4, 3, 2, 1],
            index=[5, 4, 3, 2, 1].index(st.session_state.traveling_days) if st.session_state.traveling_days in [5, 4, 3, 2, 1] else 0,
            key="traveling_days_selector",
            help="Number of days you commute per week"
        )
        if traveling_days != st.session_state.traveling_days:
            st.session_state.traveling_days = traveling_days
            st.rerun()

    with selector_col2:
        # Housing selectors (council tax band and bedroom category)
        if st.session_state.council_tax_data or st.session_state.rent_data:
            st.subheader("Housing Options")



            # Council tax band selector
            if st.session_state.council_tax_data:
                current_band_index = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'].index(
                    st.session_state.council_tax_data.get('band', 'D')
                )

                selected_band = st.selectbox(
                    "Council Tax Band:",
                    ["A", "B", "C", "D", "E", "F", "G", "H"],
                    index=current_band_index,
                    key="band_selector",
                    help="Change council tax band to update calculations"
                )

                # Update council tax data if band changed
                if selected_band != st.session_state.council_tax_data.get('band'):
                    all_bands = st.session_state.council_tax_data.get('all_bands', {})
                    monthly_amount = all_bands.get(f'Band {selected_band}', 0)

                    st.session_state.council_tax_data['band'] = selected_band
                    st.session_state.council_tax_data['monthly'] = monthly_amount
                    st.session_state.council_tax_data['annual'] = monthly_amount * 12
                    st.rerun()

            # Bedroom category selector
            if st.session_state.rent_data:
                bedroom_categories = ["Room", "Studio", "One Bedroom", "Two Bedrooms", "Three Bedrooms", "Four or More Bedrooms"]
                current_category = st.session_state.rent_data.get('bedroom_category', 'One Bedroom')
                current_category_index = bedroom_categories.index(current_category) if current_category in bedroom_categories else 2

                selected_category = st.selectbox(
                    "Bedroom Category:",
                    bedroom_categories,
                    index=current_category_index,
                    key="category_selector",
                    help="Change bedroom category to update rent"
                )

                # Update rent data if category changed
                if selected_category != st.session_state.rent_data.get('bedroom_category'):
                    all_categories = st.session_state.rent_data.get('all_categories', {})
                    monthly_rent = all_categories.get(selected_category, 0)

                    st.session_state.rent_data['bedroom_category'] = selected_category
                    st.session_state.rent_data['monthly_rent'] = monthly_rent
                    st.session_state.rent_data['annual_rent'] = monthly_rent * 12
                    st.rerun()
    # endregion Journey options and housing selectors
    #-------------------------------------------------------------------------------------------------------------------------
    # region Key metrics

    st.subheader("💰 Cost Summary")

    # Calculate monthly commute cost
    monthly = st.session_state.calculator.calculate_monthly_commute_cost(journey=journey, days_per_week=st.session_state.traveling_days)
    monthly_commute = monthly.get('monthly_cost_with_cap', 0) if monthly.get('success') else 0

    # Get council tax
    monthly_council_tax = 0
    if st.session_state.council_tax_data:
        monthly_council_tax = st.session_state.council_tax_data.get('monthly', 0)

    # Get rent
    monthly_rent = 0
    if st.session_state.rent_data:
        monthly_rent = st.session_state.rent_data.get('monthly_rent', 0)

    # Calculate total monthly cost
    total_monthly = monthly_commute + monthly_council_tax + monthly_rent

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Journey Time", f"{journey['duration_minutes']} min")

    with col2:
        fare = journey.get('fare', {})
        fare_value = fare.get('total_cost', 0)
        if fare_value:
            st.metric("Single Fare", f"£{fare_value:.2f}")
        else:
            st.metric("Single Fare", "N/A")
            st.caption("⚠️ Fare information unavailable at the moment")

    with col3:
        if monthly_commute > 0:
            st.metric(f"Monthly Commute ({traveling_days} days a week)", f"£{monthly_commute:.2f}")
        else:
            st.metric("Monthly Commute", "N/A")
            st.caption("⚠️ Fare information unavailable at the moment")

    with col4:
        if monthly_rent > 0:
            bedroom_cat = st.session_state.rent_data.get('bedroom_category', 'N/A')
            st.metric(
                f"Rent ({bedroom_cat})",
                f"£{monthly_rent:.2f}"
            )
        else:
            st.metric("Monthly Rent", "N/A")

    with col5:
        if monthly_council_tax > 0:
            st.metric(
                f"Council Tax (Band {st.session_state.council_tax_data.get('band', 'D')})",
                f"£{monthly_council_tax:.2f}"
            )
        else:
            st.metric("Council Tax", "N/A")

    with col6:
        if total_monthly > 0:
            st.metric("Total Monthly", f"£{total_monthly:.2f}",
                     help="Commute + Rent + Council Tax")
        else:
            st.metric("Total Monthly", "N/A")

    # Save for comparison button
    st.markdown("")  # Add spacing
    save_col1, save_col2, save_col3 = st.columns([1, 2, 1])
    with save_col2:
        comparison_name = st.text_input(
            "Comparison Name (optional)",
            value="",
            placeholder=f"Comparison #{st.session_state.comparison_counter + 1}",
            key="comparison_name_input"
        )

        if st.button("💾 Save for Comparison", type="primary", use_container_width=True):
            # Get journey time label from session state
            journey_time_period = st.session_state.get('journey_time_label', 'Current Time')

            # Prepare comparison data
            comparison_data = {
                'Name': comparison_name if comparison_name.strip() else f"Comparison #{st.session_state.comparison_counter + 1}",
                'From Postcode': from_postcode,
                'From Borough': from_borough,
                'To Postcode': to_postcode,
                'To Borough': to_borough,
                'Journey Period': journey_time_period,
                'Journey Time (min)': journey['duration_minutes'],
                'Single Fare (£)': fare_value if fare_value else None,
                'Traveling Days/Week': traveling_days,
                'Monthly Commute (£)': monthly_commute if monthly_commute > 0 else None,
                'Council Tax Band': st.session_state.council_tax_data.get('band', 'N/A') if st.session_state.council_tax_data else 'N/A',
                'Monthly Council Tax (£)': monthly_council_tax if monthly_council_tax > 0 else None,
                'Bedroom Category': st.session_state.rent_data.get('bedroom_category', 'N/A') if st.session_state.rent_data else 'N/A',
                'Monthly Rent (£)': monthly_rent if monthly_rent > 0 else None,
                'Total Monthly (£)': total_monthly if total_monthly > 0 else None,
                'Saved At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Add to saved comparisons
            st.session_state.saved_comparisons.append(comparison_data)
            st.session_state.comparison_counter += 1
            st.success(f"✅ Saved: {comparison_data['Name']}")
            st.rerun()

        # View comparisons button (shown only if there are saved comparisons)
        if st.session_state.saved_comparisons:
            st.markdown("")
            # Create a link button using HTML
            num_comparisons = len(st.session_state.saved_comparisons)
            st.markdown(
                f"""
                <a href="#saved-comparisons" style="text-decoration: none;">
                    <button style="
                        width: 100%;
                        padding: 0.5rem 1rem;
                        background-color: #ffffff;
                        border: 1px solid #e0e0e0;
                        border-radius: 0.5rem;
                        cursor: pointer;
                        font-size: 1rem;
                        color: #262730;
                    ">
                        📊 View Saved Comparisons ({num_comparisons})
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )

    st.divider()
    # endregion Key metrics
    #-------------------------------------------------------------------------------------------------------------------------
    # region monthly cost breakdown
    
    # Monthly cost breakdown - Three columns
    col_left, col_middle, col_right = st.columns(3)

    # Commute cost breakdown
    with col_left:
        st.subheader("🚇 Commute Cost")

        monthly = st.session_state.calculator.calculate_monthly_commute_cost(journey=journey, days_per_week=st.session_state.traveling_days)

        if monthly.get('success'):
            st.metric("Daily", f"£{monthly['daily_cost']:.2f}")
            st.metric("Weekly", f"£{monthly['weekly_cost']:.2f}")
            st.metric("Monthly", f"£{monthly['monthly_cost']:.2f}")
            st.metric("Monthly (with cap)", f"£{monthly['monthly_cost_with_cap']:.2f}")

            if monthly.get('warning'):
                st.caption(monthly['warning'])
        else:
            st.error("Could not calculate monthly cost")

    # Rent breakdown
    with col_middle:
        st.subheader("🏘️ Average Rent")

        if st.session_state.rent_data:
            rent_data = st.session_state.rent_data

            st.info(f"**Borough:** {rent_data.get('borough', 'Unknown')}")

            st.metric(
                f"Monthly ({rent_data.get('bedroom_category', 'N/A')})",
                f"£{rent_data.get('monthly_rent', 0):.2f}"
            )

            st.metric(
                "Annual",
                f"£{rent_data.get('annual_rent', 0):.2f}"
            )

            # Show comparison across bedroom categories
            with st.expander("Compare Categories"):
                all_categories = rent_data.get('all_categories', {})
                if all_categories:
                    category_comparison = []
                    for category, monthly_price in all_categories.items():
                        annual_price = monthly_price * 12
                        category_comparison.append({
                            'Category': category,
                            'Monthly': f"£{monthly_price:.2f}"
                        })

                    if category_comparison:
                        st.table(category_comparison)
        else:
            st.warning("Rent data not available")

    # Council tax breakdown
    with col_right:
        st.subheader("🏛️ Council Tax")

        if st.session_state.council_tax_data:
            ct_data = st.session_state.council_tax_data

            st.info(f"**Borough:** {ct_data.get('borough', 'Unknown')}")

            st.metric(
                f"Monthly (Band {ct_data.get('band', 'D')})",
                f"£{ct_data.get('monthly', 0):.2f}"
            )

            st.metric(
                "Annual",
                f"£{ct_data.get('annual', 0):.2f}"
            )

            # Show comparison across bands
            with st.expander("Compare Bands"):
                bands_data = ct_data.get('all_bands', {})
                if bands_data:
                    band_comparison = []
                    for band_key in ['Band A', 'Band B', 'Band C', 'Band D', 'Band E', 'Band F', 'Band G', 'Band H']:
                        if band_key in bands_data:
                            band_letter = band_key.split()[1]
                            monthly_val = bands_data[band_key]
                            annual_val = monthly_val * 12
                            band_comparison.append({
                                'Band': band_letter,
                                'Monthly': f"£{monthly_val:.2f}"
                            })

                    if band_comparison:
                        st.table(band_comparison)
        else:
            st.warning("Council tax data not available")

    st.divider()
    # endregion monthly cost breakdown
    #-------------------------------------------------------------------------------------------------------------------------
    # region route details and map
    
    # Two columns for route details and map
    col1, col2 = st.columns([1, 1])

    # route details
    with col1:
        st.subheader("Route Details")

        # Display route legs
        raw_data = journey.get('raw_data', {})
        legs = raw_data.get('legs', [])

        for i, leg in enumerate(legs, 1):
            mode = leg.get('mode', {}).get('name', 'Unknown')
            departure = leg.get('departurePoint', {})
            arrival = leg.get('arrivalPoint', {})
            dep_name = departure.get('commonName', 'Unknown')
            arr_name = arrival.get('commonName', 'Unknown')
            duration = leg.get('duration', 0)

            # Get route name if available
            route_name = ""
            route_options = leg.get('routeOptions', [])
            if route_options:
                route_name = route_options[0].get('name', '')

            with st.container():
                st.markdown(f"**Leg {i}: {mode.upper()}** {f'({route_name})' if route_name else ''}")
                st.text(f"From: {dep_name}")
                st.text(f"To: {arr_name}")
                st.text(f"Duration: {duration} minutes")

                # Get instruction if available
                instruction = leg.get('instruction', {})
                summary = instruction.get('summary', '')
                if summary:
                    st.caption(f"ℹ️ {summary}")

                if i < len(legs):
                    st.markdown("---")
    # journey map
    with col2:
        st.subheader("Journey Map")

        # Generate map
        try:
            map_file = st.session_state.calculator.visualize_journey(
                journey=journey,
                output_file='temp_journey_map.html',
                open_browser=False
            )

            if map_file:
                # Read and display the map
                with open(map_file, 'r', encoding='utf-8') as f:
                    map_html = f.read()
                st.components.v1.html(map_html, height=500, scrolling=True)
        except Exception as e:
            st.warning(f"Could not generate map: {str(e)}")

    st.divider()
    # endregion route details and map
    #-------------------------------------------------------------------------------------------------------------------------

# Display saved comparisons (shown always, if there are any saved)
if st.session_state.saved_comparisons:
    st.markdown("---")
    # Add anchor for scrolling
    st.markdown('<div id="saved-comparisons"></div>', unsafe_allow_html=True)
    st.subheader("📊 Saved Comparisons")

    # Create DataFrame from saved comparisons
    df = pd.DataFrame(st.session_state.saved_comparisons)

    # Reorder columns for better display
    column_order = [
        'Name',
        'From Postcode',
        'From Borough',
        'To Postcode',
        'To Borough',
        'Journey Period',
        'Journey Time (min)',
        'Single Fare (£)',
        'Traveling Days/Week',
        'Monthly Commute (£)',
        'Council Tax Band',
        'Monthly Council Tax (£)',
        'Bedroom Category',
        'Monthly Rent (£)',
        'Total Monthly (£)',
        'Saved At'
    ]
    df = df[column_order]

    # Display the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # Action buttons
    action_col1, action_col2, action_col3 = st.columns([1, 1, 3])

    with action_col1:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.saved_comparisons = []
            st.session_state.comparison_counter = 0
            st.success("All comparisons cleared!")
            st.rerun()

    with action_col2:
        # Export to CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"london_housing_comparisons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Individual delete functionality
    with st.expander("🗑️ Delete Individual Comparisons"):
        for idx, comparison in enumerate(st.session_state.saved_comparisons):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(f"{comparison['Name']} - {comparison['From Postcode']} → {comparison['To Postcode']}")
            with col2:
                if st.button(f"Delete", key=f"delete_{idx}"):
                    st.session_state.saved_comparisons.pop(idx)
                    st.success(f"Deleted: {comparison['Name']}")
                    st.rerun()

if not st.session_state.journey_result or not st.session_state.journey_result.get('success'):
    # Initial state - show instructions
    st.info("👈 Enter your home and office/school postcodes (Full Postcode Format) in the sidebar and click 'Calculate Cost' to get started")

    # Example postcodes
    st.subheader("Example Postcodes")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Popular Home Areas:**
        - SW1A 1AA (Westminster)
        - E1 6AN (Whitechapel)
        - N1 9AG (Islington)
        """)

    with col2:
        st.markdown("""
        **Popular Office Areas:**
        - EC2Y 5BL (Liverpool Street)
        - WC2N 5DU (Trafalgar Square)
        - SE1 9SG (London Bridge)
        """)

# Footer
st.divider()
st.caption("**Data Sources:** TfL Journey Planner API • Office for National Statistics • London Datastore")
st.caption("Council tax and rent data are averages by borough and for reference only. Actual costs may vary.")

"""
Streamlit UI for London Housing Route Calculator
Allows users to calculate commute routes and costs between postcodes
"""

import streamlit as st
from route_calculator import TravelCalculator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="London Commute Calculator",
    page_icon="🚇",
    layout="wide"
)

# Initialize calculator in session state
if 'calculator' not in st.session_state:
    st.session_state.calculator = TravelCalculator()
if 'journey_result' not in st.session_state:
    st.session_state.journey_result = None
if 'all_journeys' not in st.session_state:
    st.session_state.all_journeys = None

# Title and description
st.title("🚇 London Commute Calculator")
st.markdown("Calculate travel routes, times, and costs between London postcodes")

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
        "To (Office Postcode)",
        value="EC2Y 5BL",
        placeholder="e.g., E1 6AN"
    ).strip()

    st.divider()

    # Advanced options
    with st.expander("Advanced Options"):
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

    st.divider()

    # Calculate button
    calculate_button = st.button("🔍 Calculate Route", type="primary", use_container_width=True)

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
            else:
                st.error("No journey options found. Please check your postcodes and try again.")
                st.session_state.journey_result = None
                st.session_state.all_journeys = None

# Display results
if st.session_state.journey_result and st.session_state.journey_result.get('success'):
    journey = st.session_state.journey_result

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

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Duration", f"{journey['duration_minutes']} min")

    with col2:
        fare = journey.get('fare', {})
        fare_value = fare.get('total_cost', 0)
        if fare_value:
            st.metric("Single Fare", f"£{fare_value:.2f}")
        else:
            st.metric("Single Fare", "N/A")

    with col3:
        st.metric("Number of Legs", journey['legs'])

    with col4:
        # Calculate monthly cost
        monthly = st.session_state.calculator.calculate_monthly_commute_cost(journey=journey)
        if monthly.get('success') and monthly.get('monthly_cost_with_cap', 0) > 0:
            st.metric("Monthly Cost", f"£{monthly['monthly_cost_with_cap']:.2f}")
        else:
            st.metric("Monthly Cost", "N/A")

    st.divider()

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

    # Monthly cost breakdown
    st.subheader("Monthly Commute Cost")

    monthly = st.session_state.calculator.calculate_monthly_commute_cost(journey=journey)

    if monthly.get('success'):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Daily Cost", f"£{monthly['daily_cost']:.2f}")

        with col2:
            st.metric("Weekly Cost", f"£{monthly['weekly_cost']:.2f}")

        with col3:
            st.metric("Monthly Cost", f"£{monthly['monthly_cost']:.2f}")

        with col4:
            st.metric("Monthly (with cap)", f"£{monthly['monthly_cost_with_cap']:.2f}")

        if monthly.get('warning'):
            st.warning(monthly['warning'])
    else:
        st.error("Could not calculate monthly cost")

else:
    # Initial state - show instructions
    st.info("👈 Enter your home and office postcodes in the sidebar and click 'Calculate Route' to get started")

    # Example postcodes
    st.subheader("Example Postcodes")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Popular Home Areas:**
        - IG3 8EE (Ilford)
        - SW1A 1AA (Westminster)
        - E1 6AN (Whitechapel)
        - N1 9AG (Islington)
        """)

    with col2:
        st.markdown("""
        **Popular Office Areas:**
        - EC2Y 5BL (Liverpool Street)
        - WC2N 5DU (Trafalgar Square)
        - E20 2ZQ (Stratford)
        - SE1 9SG (London Bridge)
        """)

# Footer
st.divider()
st.caption("Powered by TfL Journey Planner API | Data may be subject to TfL terms and conditions")

"""
This module provides functionality to retrieve council tax information for London boroughs.
It loads data from a CSV file and allows flexible borough name lookups. 
"""

import pandas as pd
import os
from typing import Optional, Dict

class CouncilTaxLookup:
    """Lookup council tax data for London boroughs"""

    def __init__(self, council_tax_data_path: Optional[str] = None, post_code_data_path: Optional[str] = None):
        """
        Initialize the lookup class

        Args:
            council_tax_data_path: Path to the council tax CSV file
        """
        if council_tax_data_path is None:
            # Default path relative to this script
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            council_tax_data_path = os.path.join(base_dir, 'data', 'council_tax', 'council_tax_2024_2025.csv')

        # load council tax data
        self.council_tax_data_path = council_tax_data_path 
        self.council_tax_data = pd.read_csv(self.council_tax_data_path)

        if post_code_data_path is None:
            # Default path relative to this script
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            post_code_data_path = os.path.join(base_dir, 'data', 'geodata','post_code', 'london_post_code_data.csv')
        
        # load post code data
        self.post_code_data_path = post_code_data_path
        self.post_code_data = pd.read_csv(self.post_code_data_path)

        # Placeholder for council tax info
        self.council_tax_info = None

    def get_council_tax_by_postcode(self, postcode: str) -> Optional[Dict]:
        """
        Get council tax information for a given postcode

        Args:
            postcode: The postcode to lookup
        Returns:
            A dictionary with council tax information or None if not found  
        """
        if not postcode:
            print("Missing/Invalid postcode provided.")
            return None

        # Normalize postcode for matching
        normalized_postcode = postcode.replace(" ", "").upper()

        # Find the borough code from postcode data
        borough_row = self.post_code_data[self.post_code_data['pcds'].str.replace(" ", "").str.upper() == normalized_postcode]

        if borough_row.empty:
            print(f"Postcode {postcode} not found in London boroughs.")
            return None

        borough_code = borough_row.iloc[0]['ladcd']

        # Find council tax info for the borough
        council_tax_row = self.council_tax_data[self.council_tax_data['Code'] == borough_code]

        if council_tax_row.empty:
            print(f"Council tax data not found for borough code {borough_code}.")
            return None

        # Convert row to dictionary
        self.council_tax_info = council_tax_row.iloc[0].to_dict()
        return self.council_tax_info
    
    def calculate_monthly_council_tax(self, postcode: str) -> dict:
        """
        Calculate the monthly council tax from the annual amount

        Args:
            annual_amount: The annual council tax amount
        Returns:
            The monthly council tax amount
        """
        
        council_tax_info = self.get_council_tax_by_postcode(postcode)
        
        

        # get all keys starting with 'Band '
        monthly_data = {
            key: round(value / 12, 2) if key.startswith('Band ') else value
            for key, value in council_tax_info.items()
        }

        return monthly_data
            

class AverageRentCost:
    """Lookup average rent cost for London boroughs"""

    def __init__(self, rent_data_path: Optional[str] = None, post_code_data_path: Optional[str] = None):
        """
        Initialize the lookup class

        Args:
            rent_data_path: Path to the average rent CSV file
            post_code_data_path: Path to the postcode data CSV file
        """
        if rent_data_path is None:
            # Default path relative to this script
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rent_data_path = os.path.join(base_dir, 'data', 'rent_price', 'londonrent.csv')

        # Load average rent data
        self.rent_data_path = rent_data_path
        self.rent_data = pd.read_csv(self.rent_data_path)

        if post_code_data_path is None:
            # Default path relative to this script
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            post_code_data_path = os.path.join(base_dir, 'data', 'geodata', 'post_code', 'london_post_code_data.csv')

        # Load postcode data
        self.post_code_data_path = post_code_data_path
        self.post_code_data = pd.read_csv(self.post_code_data_path)

        # Create borough name mapping for flexible matching
        self.borough_mapping = self._create_borough_mapping()

        # Placeholder for rent info
        self.rent_info = None

    def _create_borough_mapping(self) -> dict:
        """
        Create normalized borough name mapping from postcode data to rent data

        Returns:
            Dictionary mapping normalized borough names to rent data borough names
        """
        mapping = {}

        # Get unique boroughs from both datasets
        rent_boroughs = self.rent_data['Borough'].unique()

        # Create normalized mapping
        for borough in rent_boroughs:
            # Normalize: lowercase, remove spaces, remove '&' and 'and'
            normalized = borough.lower().replace(' ', '').replace('&', '').replace('and', '')
            mapping[normalized] = borough

            # Also create version with 'and' instead of '&'
            normalized_and = borough.lower().replace(' ', '').replace('&', 'and')
            mapping[normalized_and] = borough

        return mapping

    def _normalize_borough_name(self, borough: str) -> Optional[str]:
        """
        Normalize borough name for matching

        Args:
            borough: Borough name to normalize

        Returns:
            Official borough name from rent data or None if not found
        """
        normalized = borough.lower().replace(' ', '').replace('&', '').replace('and', '')

        # Try direct match first
        if normalized in self.borough_mapping:
            return self.borough_mapping[normalized]

        # Try with 'and' variant
        normalized_and = borough.lower().replace(' ', '').replace('&', 'and')
        return self.borough_mapping.get(normalized_and)

    def _get_borough_from_postcode(self, postcode: str) -> Optional[str]:
        """
        Get borough name from postcode

        Args:
            postcode: The postcode to lookup

        Returns:
            Borough name or None if not found
        """
        if not postcode:
            print("Missing/Invalid postcode provided.")
            return None

        # Normalize postcode for matching
        normalized_postcode = postcode.replace(" ", "").upper()

        # Find the borough name from postcode data
        borough_row = self.post_code_data[
            self.post_code_data['pcds'].str.replace(" ", "").str.upper() == normalized_postcode
        ]

        if borough_row.empty:
            print(f"Postcode {postcode} not found in London boroughs.")
            return None

        # Get borough name from postcode data
        borough_name = borough_row.iloc[0]['ladnm']
        return borough_name

    def get_average_rent_by_postcode(
        self,
        postcode: str,
        bedroom_category: str = 'One Bedroom',
        use_median: bool = True
    ) -> Optional[Dict]:
        """
        Get average rent for a given postcode and bedroom category

        Args:
            postcode: The postcode to lookup
            bedroom_category: Bedroom category - 'Room', 'Studio', 'One Bedroom',
                            'Two Bedrooms', 'Three Bedrooms', 'Four or More Bedrooms'
            use_median: If True, use median rent, otherwise use mean

        Returns:
            Dictionary with rent information or None if not found
        """
        # Get borough from postcode
        borough_name = self._get_borough_from_postcode(postcode)

        if not borough_name:
            return None

        # Normalize borough name to match rent data
        matched_borough = self._normalize_borough_name(borough_name)

        if not matched_borough:
            print(f"Borough '{borough_name}' not found in rent data.")
            return None

        # Filter rent data by borough and bedroom category
        rent_row = self.rent_data[
            (self.rent_data['Borough'] == matched_borough) &
            (self.rent_data['Bedroom Category'] == bedroom_category)
        ]

        if rent_row.empty:
            print(f"No rent data found for {matched_borough} - {bedroom_category}")
            return None

        # Get rent value (clean and convert to float)
        row_data = rent_row.iloc[0]

        rent_column = 'Median' if use_median else 'Mean'
        rent_value_str = str(row_data[rent_column])

        # Handle '..' (missing data) or empty values
        if rent_value_str == '..' or rent_value_str == 'nan':
            print(f"No {rent_column.lower()} rent data available for {matched_borough} - {bedroom_category}")
            return None

        # Remove commas and convert to float
        try:
            rent_value = float(rent_value_str.replace(',', ''))
        except ValueError:
            print(f"Invalid rent value: {rent_value_str}")
            return None

        # Return comprehensive information
        self.rent_info = {
            'borough': matched_borough,
            'postcode': postcode,
            'bedroom_category': bedroom_category,
            'monthly_rent': rent_value,
            'annual_rent': rent_value * 12,
            'data_type': rent_column.lower(),
            'count_of_rents': row_data['Count of rents'],
            'lower_quartile': row_data['Lower quartile'],
            'upper_quartile': row_data['Upper quartile']
        }

        return self.rent_info

    def get_all_bedroom_categories(self, postcode: str) -> Optional[Dict[str, float]]:
        """
        Get rent prices for all bedroom categories for a given postcode

        Args:
            postcode: The postcode to lookup

        Returns:
            Dictionary mapping bedroom categories to median rent prices
        """
        # Get borough from postcode
        borough_name = self._get_borough_from_postcode(postcode)

        if not borough_name:
            return None

        # Normalize borough name
        matched_borough = self._normalize_borough_name(borough_name)

        if not matched_borough:
            return None

        # Get all categories for this borough
        borough_data = self.rent_data[self.rent_data['Borough'] == matched_borough]

        if borough_data.empty:
            return None

        result = {}
        for _, row in borough_data.iterrows():
            category = row['Bedroom Category']
            median_str = str(row['Median'])

            if median_str != '..' and median_str != 'nan':
                try:
                    result[category] = float(median_str.replace(',', ''))
                except ValueError:
                    pass

        return result if result else None


if __name__ == "__main__":
    # Test the average rent lookup
    print("Testing AverageRentCost...\n")

    rent_lookup = AverageRentCost()

    # Test 1: Get rent by postcode
    print("=" * 60)
    print("Test 1: Get average rent for IG3 8EE (One Bedroom)")
    print("=" * 60)
    result = rent_lookup.get_average_rent_by_postcode("IG3 8EE", "One Bedroom")
    if result:
        print(f"Borough: {result['borough']}")
        print(f"Monthly Rent: £{result['monthly_rent']:.2f}")
        print(f"Annual Rent: £{result['annual_rent']:.2f}")

    # Test 2: Get all bedroom categories
    print("\n" + "=" * 60)
    print("Test 2: Get all bedroom categories for SW1A 1AA")
    print("=" * 60)
    all_cats = rent_lookup.get_all_bedroom_categories("SW1A 1AA")
    if all_cats:
        for category, price in all_cats.items():
            print(f"{category}: £{price:.2f}/month")
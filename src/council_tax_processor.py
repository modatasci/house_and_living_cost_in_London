"""
Council Tax Data Processor for London Housing Project

Processes council tax data from London Datastore Excel files and provides
lookup functions for council tax rates by borough and band.

Data source: https://data.london.gov.uk/dataset/council-tax-charges-bands-borough
"""

import pandas as pd
import os
from typing import Optional, Dict


class CouncilTaxProcessor:
    """Process and lookup council tax data for London boroughs"""

    def __init__(self, data_path: str = None):
        """
        Initialize the processor

        Args:
            data_path: Path to the council tax Excel file
        """
        if data_path is None:
            # Default path relative to this script
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, 'data', 'council_tax', 'council-tax-bands-borough.xlsx')

        self.data_path = data_path
        self.df = None
        self.borough_mapping = {}
        self._load_data()

    def _load_data(self, year: str = '2024-25'):
        """
        Load council tax data from Excel file

        Args:
            year: Tax year to load (default: 2024-25)
        """
        try:
            # Read the specific year sheet
            self.df = pd.read_excel(self.data_path, sheet_name=year, header=0)

            # Drop first row if it's NaN (metadata row)
            if pd.isna(self.df.iloc[0]['Code']):
                self.df = self.df.iloc[1:].reset_index(drop=True)

            # Clean column names
            self.df.columns = self.df.columns.str.strip()

            # Remove any rows with NaN in Local authority column
            self.df = self.df.dropna(subset=['Local authority'])

            # Create normalized borough name mapping for easier lookup
            self._create_borough_mapping()

            print(f"✓ Loaded council tax data for {year}")
            print(f"✓ Found {len(self.df)} London boroughs")

        except Exception as e:
            print(f"Error loading council tax data: {str(e)}")
            raise

    def _create_borough_mapping(self):
        """Create normalized borough name mapping for flexible lookups"""
        for idx, row in self.df.iterrows():
            borough_name = row['Local authority']
            # Create multiple normalized keys for flexible matching
            base = borough_name.lower().replace(' ', '')

            # Version 1: Replace & with 'and'
            normalized1 = base.replace('&', 'and')
            self.borough_mapping[normalized1] = borough_name

            # Version 2: Remove & entirely
            normalized2 = base.replace('&', '')
            self.borough_mapping[normalized2] = borough_name

            # Version 3: Keep original with spaces removed
            self.borough_mapping[base] = borough_name

    def _normalize_borough_name(self, borough: str) -> Optional[str]:
        """
        Normalize borough name for lookup

        Args:
            borough: Borough name to normalize

        Returns:
            Official borough name or None if not found
        """
        normalized = borough.lower().replace(' ', '').replace('&', 'and')
        return self.borough_mapping.get(normalized)

    def get_council_tax(
        self,
        borough: str,
        band: str = 'D',
        period: str = 'annual'
    ) -> Optional[float]:
        """
        Get council tax amount for a borough and band

        Args:
            borough: Borough name (case insensitive, flexible matching)
            band: Council tax band (A-H), default 'D'
            period: 'annual' or 'monthly'

        Returns:
            Council tax amount in £, or None if not found
        """
        # Normalize borough name
        official_borough = self._normalize_borough_name(borough)

        if official_borough is None:
            print(f"Warning: Borough '{borough}' not found")
            return None

        # Validate band
        band = band.upper().strip()
        if band not in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            print(f"Warning: Invalid band '{band}'. Must be A-H")
            return None

        # Get the row for this borough
        borough_row = self.df[self.df['Local authority'] == official_borough]

        if borough_row.empty:
            print(f"Warning: No data found for '{official_borough}'")
            return None

        # Get the tax amount
        column_name = f'Band {band}'
        tax_amount = borough_row[column_name].values[0]

        if pd.isna(tax_amount):
            print(f"Warning: No tax data for {official_borough}, Band {band}")
            return None

        # Return annual or monthly
        if period == 'monthly':
            return round(tax_amount / 12, 2)
        else:
            return round(tax_amount, 2)

    def get_all_bands_for_borough(self, borough: str) -> Optional[Dict[str, float]]:
        """
        Get council tax for all bands in a borough

        Args:
            borough: Borough name

        Returns:
            Dictionary of {band: annual_amount} or None if not found
        """
        official_borough = self._normalize_borough_name(borough)

        if official_borough is None:
            return None

        borough_row = self.df[self.df['Local authority'] == official_borough]

        if borough_row.empty:
            return None

        result = {}
        for band in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            column_name = f'Band {band}'
            amount = borough_row[column_name].values[0]
            if not pd.isna(amount):
                result[band] = round(amount, 2)

        return result

    def export_processed_data(self, output_path: str = None):
        """
        Export processed council tax data to CSV

        Args:
            output_path: Output CSV file path
        """
        if output_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(base_dir, 'data', 'processed')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, 'council_tax_2024_2025.csv')

        # Create a clean version with just the essential columns
        export_df = self.df.copy()

        # Save to CSV
        export_df.to_csv(output_path, index=False)
        print(f"✓ Exported processed data to: {output_path}")

    def get_borough_list(self) -> list:
        """Get list of all available boroughs"""
        return sorted(self.df['Local authority'].tolist())

    def print_summary(self):
        """Print summary of council tax data"""
        print("\n" + "=" * 60)
        print("COUNCIL TAX DATA SUMMARY")
        print("=" * 60)
        print(f"Number of boroughs: {len(self.df)}")

        # Calculate statistics for Band D (standard comparison)
        band_d_values = self.df['Band D'].dropna()
        print(f"\nBand D Statistics:")
        print(f"  Average: £{band_d_values.mean():.2f}")
        print(f"  Minimum: £{band_d_values.min():.2f} ({self.df.loc[band_d_values.idxmin(), 'Local authority']})")
        print(f"  Maximum: £{band_d_values.max():.2f} ({self.df.loc[band_d_values.idxmax(), 'Local authority']})")
        print("=" * 60 + "\n")


# Example usage and testing
if __name__ == "__main__":
    print("Testing Council Tax Processor...\n")

    # Initialize processor
    processor = CouncilTaxProcessor()

    # Print summary
    processor.print_summary()

    # Test 1: Get council tax for specific borough and band
    print("=" * 60)
    print("Test 1: Get council tax for Camden, Band D")
    print("=" * 60)
    tax = processor.get_council_tax('Camden', 'D')
    if tax:
        print(f"Annual: £{tax:.2f}")
        print(f"Monthly: £{processor.get_council_tax('Camden', 'D', period='monthly'):.2f}")

    # Test 2: Get all bands for a borough
    print("\n" + "=" * 60)
    print("Test 2: Get all bands for Westminster")
    print("=" * 60)
    all_bands = processor.get_all_bands_for_borough('Westminster')
    if all_bands:
        for band, amount in all_bands.items():
            print(f"Band {band}: £{amount:.2f} annual (£{amount/12:.2f} monthly)")

    # Test 3: Test flexible borough name matching
    print("\n" + "=" * 60)
    print("Test 3: Flexible borough name matching")
    print("=" * 60)
    test_names = ['barking and dagenham', 'BARKING & DAGENHAM', 'barkingandagenham']
    for name in test_names:
        tax = processor.get_council_tax(name, 'D')
        print(f"'{name}' -> £{tax:.2f}" if tax else f"'{name}' -> Not found")

    # Test 4: Export processed data
    print("\n" + "=" * 60)
    print("Test 4: Export processed data")
    print("=" * 60)
    processor.export_processed_data()

    # Test 5: List all boroughs
    print("\n" + "=" * 60)
    print("Test 5: Available boroughs")
    print("=" * 60)
    boroughs = processor.get_borough_list()
    print(f"Total: {len(boroughs)} boroughs")
    for borough in boroughs[:5]:
        print(f"  - {borough}")
    print(f"  ... and {len(boroughs) - 5} more")

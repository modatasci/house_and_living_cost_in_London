"""
This module prodives the mapping of post codes into the boroughs of London.

Postcodes are filter to London boroughs using the 'ladcd' column.
Borough codes for London start with 'E09'. From E09000001 to E09000033.

Data source: Office for National Statistics - Postcode to Administrative Areas May 2025
https://geoportal.statistics.gov.uk/datasets/7fc55d71a09d4dcfa1fd6473138aacc3/about
"""

# import libraries
import pandas as pd
import os

def get_borough_from_postcode(postcode: str) -> str:
    """
    Given a postcode and a dataframe of postcodes to boroughs,
    return the corresponding borough name.

    Args:
        postcode (str): The postcode to look up.
        postcode_df (pd.DataFrame): DataFrame containing postcode to borough mapping.

    Returns:
        str: The name of the borough corresponding to the postcode.
    """
    # Default path relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'geodata','post_code', 'PCD_OA21_LSOA21_MSOA21_LAD_MAY25_UK_LU.csv')

    # Load post code data
    postcode_df = pd.read_csv(data_path)
    match = postcode_df[postcode_df['pcds'] == postcode]
    if not match.empty:
        return match.iloc[0]['ladnm']
    else:
        return "Unknown"

def main():

    # Default path relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'geodata','post_code', 'PCD_OA21_LSOA21_MSOA21_LAD_MAY25_UK_LU.csv')

    # Load post code data
    post_code_df = pd.read_csv(data_path)

    # fill NaN in 'ladcd' with 'Unknown' to avoid issues during filtering
    post_code_df.loc[:, 'ladcd'] = post_code_df['ladcd'].fillna('Unknown')                                                           

    # Filter to only London boroughs (ladcd starting with 'E09')
    london_post_code_df = post_code_df[post_code_df['ladcd'].str.startswith('E09')]

    # take relevant columns only
    london_post_code_df = london_post_code_df[['pcds', 'ladcd', 'ladnm']]

    # Display number of ladnm (boroughs) found
    print(f"✓ Found {london_post_code_df['ladnm'].nunique()} London boroughs")

    # save to CSV for easier future use
    output_path = os.path.join(base_dir, 'data', 'geodata','post_code', 'london_post_code_data.csv')
    london_post_code_df.to_csv(output_path, index=False)
    print(f"✓ Saved London post code data to {output_path}")

if __name__ == "__main__":
    main()  
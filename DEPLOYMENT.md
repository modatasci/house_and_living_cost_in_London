# Deployment Guide - Streamlit Cloud

## Prerequisites
- GitHub account
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
- TfL API Key (from [api-portal.tfl.gov.uk](https://api-portal.tfl.gov.uk/))

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/modatasci/house_and_living_cost_in_London.git
   cd house_and_living_cost_in_London
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up secrets (choose one)**

   **Option A: Using .env file**
   ```bash
   # Create .env file in src/ directory
   echo "TFL_APP_KEY=your_api_key_here" > src/.env
   ```

   **Option B: Using Streamlit secrets**
   ```bash
   # Copy template and edit
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit .streamlit/secrets.toml and add your API key
   ```

4. **Run the app**
   ```bash
   streamlit run src/app.py
   ```

## Streamlit Cloud Deployment

### Step 1: Push to GitHub
```bash
git push origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Configure:
   - **Repository:** `modatasci/house_and_living_cost_in_London`
   - **Branch:** `main`
   - **Main file path:** `src/app.py`

4. Click **"Advanced settings"** and add secrets:
   ```toml
   TFL_APP_KEY = "your_tfl_api_key_here"
   ```

5. Click **"Deploy!"**

### Step 3: Wait for Deployment
- Initial deployment takes 2-5 minutes
- Streamlit Cloud will install dependencies from `requirements.txt`
- Once complete, your app will be live!

## Data Files Included

The following data files are committed to the repository:
- `data/geodata/post_code/london_post_code_data.csv` (9.1 MB)
- `data/council_tax/council_tax_2024_2025.csv` (4.6 KB)
- `data/rent_price/londonrent.csv` (13 KB)

Total: ~9.14 MB (well under GitHub's 100MB limit)

## Troubleshooting

### "No module named 'dotenv'"
- Ensure `requirements.txt` includes `python-dotenv>=1.0.0`

### "TFL API Key not found"
- **Local:** Check `.env` or `.streamlit/secrets.toml` exists and contains valid key
- **Cloud:** Verify secrets are configured in Streamlit Cloud dashboard

### "Data file not found"
- Ensure data files are committed to repository
- Check file paths in code match actual file locations

### App crashes on startup
- Check Streamlit Cloud logs for detailed error messages
- Verify all dependencies are in `requirements.txt`

## App Features

✅ Journey time calculation (Rush hour vs Off-peak)
✅ Council tax lookup by postcode
✅ Average rent prices by borough and bedroom category
✅ Save and compare multiple locations
✅ Export comparisons to CSV
✅ Interactive journey map

## Support

For issues or questions, please open an issue on GitHub:
https://github.com/modatasci/house_and_living_cost_in_London/issues

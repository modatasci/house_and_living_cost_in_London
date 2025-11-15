# TfL API Setup Guide

## Step 1: Register for API Key

1. Go to: **https://api-portal.tfl.gov.uk/**
2. Click **"Sign up"** or **"Login"**
3. Fill in registration form:
   - Email address
   - Password
   - Accept terms
4. Verify your email
5. Log in to the portal

## Step 2: Get Your API Credentials

1. Once logged in, go to **"Products"**
2. Subscribe to **"500 Requests per min."** (free tier)
3. Go to **"Profile"** → **"Subscriptions"**
4. You'll see your subscription with credentials:
   - **Primary Key** (or **App Key**) - This is what you need! Copy this.
   - **Secondary Key** (backup key)

**Note:** You only need the **App Key** (Primary Key). There's no separate `app_id` needed for TfL API.

## Step 3: Store API Key Securely

Create a `.env` file in your project root:

```bash
# .env
TFL_APP_KEY=your_primary_key_here
```

**Example:**
```bash
# .env
TFL_APP_KEY=abcd1234efgh5678ijkl9012mnop3456
```

**IMPORTANT:**
- Add `.env` to your `.gitignore` to keep credentials private!
- Only `TFL_APP_KEY` is required (not `app_id`)

## Step 4: Test Your API Key

```python
import requests

app_key = "YOUR_APP_KEY"
url = "https://api.tfl.gov.uk/Journey/JourneyResults/SW1A%201AA/to/E1%206AN"
params = {'app_key': app_key}

response = requests.get(url, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

If you get status 200, you're all set!

## API Documentation

- **Main docs:** https://api.tfl.gov.uk/
- **Journey Planner:** https://api.tfl.gov.uk/swagger/ui/index.html?url=/swagger/docs/v1#!/Journey
- **Swagger UI:** Explore all endpoints interactively

## Rate Limits

- **Free tier:** 500 requests/minute
- **Daily limit:** Check your subscription details
- **Best practice:** Cache results to minimize API calls

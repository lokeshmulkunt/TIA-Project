import requests
import json

# The GraphQL endpoint for Allbirds
url = "https://allbirds.com/api/2024-04/graphql.json"

# --- THE FIX: ADD A BROWSER USER-AGENT HEADER ---
headers = {
    "Content-Type": "application/json",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}
# --- END OF FIX ---

# This query gets the first 5 products and their prices
query = """
{
  products(first: 5) {
    edges {
      node {
        title
        handle 
        variants(first: 1) {
          edges {
            node {
              price {
                amount
                currencyCode
              }
            }
          }
        }
      }
    }
  }
}
"""

# --- SEND THE REQUEST ---
try:
    print(f"ℹ️  Querying the Shopify API for {url}...")
    response = requests.post(url, json={"query": query}, headers=headers)
    response.raise_for_status() 
    
    data = response.json()
    
    print("✅ Successfully received data:")
    print(json.dumps(data, indent=2))

except requests.exceptions.RequestException as e:
    print(f"❌ ERROR: Could not connect to the API. {e}")
except json.JSONDecodeError:
    print("❌ ERROR: Could not decode the JSON response. The store might be protected.")
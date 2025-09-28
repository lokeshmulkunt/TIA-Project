import requests
import json

# --- Configuration (Your stores) ---
SHOPIFY_STORES = [
    {
        "name": "TIA Store-A",
        "url": "https://tiastore-a.myshopify.com",
        "storefront_access_token": "34b31616261360c6cb5ab3b7a6e329f5"
    },
    {
        "name": "TIA Store-B",
        "url": "https://trackitall-tia.myshopify.com",
        "storefront_access_token": "6d9742469e7bd501ce13a18b5a949913"
    },
    {
        "name": "TIA Store-C",
        "url": "https://tia-store-c.myshopify.com",
        "storefront_access_token": "032e9d370a8b3db435af0f41a07c6bd2"
    },
    {
        "name": "TIA Store-D",
        "url": "https://tia-store-d.myshopify.com",
        "storefront_access_token": "46432135fd1cd84d0aa4d07471ce079c"
    }
]

def get_shopify_products(store_url, storefront_access_token, query_string=None):
    products_data = []
    graphql_url = f"{store_url}/api/2024-01/graphql.json"

    graphql_query = """
    query ProductList($cursor: String, $query: String) {
      products(first: 20, after: $cursor, query: $query) {
        pageInfo { hasNextPage, endCursor }
        edges {
          node {
            id
            title
            handle  # The URL-friendly version of the title
            onlineStoreUrl
            variants(first: 1) {
              edges { node { price { amount, currencyCode } } }
            }
          }
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Storefront-Access-Token": storefront_access_token
    }

    has_next_page = True
    cursor = None

    while has_next_page:
        variables = {"cursor": cursor}
        if query_string:
            variables["query"] = f"title:*{query_string}*"

        payload = {"query": graphql_query, "variables": variables}

        try:
            response = requests.post(graphql_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                print(f"❌ Shopify API Errors for {store_url}: {data['errors']}")
                break
            
            products_edge = data.get("data", {}).get("products", {}).get("edges", [])
            page_info = data.get("data", {}).get("products", {}).get("pageInfo", {})

            for edge in products_edge:
                product = edge["node"]
                title = product.get("title")
                url = product.get("onlineStoreUrl")
                handle = product.get("handle")
                
                # --- THIS IS THE FIX ---
                # If the API returns a null URL (because it's a dev store), build it ourselves.
                if not url and handle:
                    url = f"{store_url}/products/{handle}"
                # --- END OF FIX ---

                price_info = product.get("variants", {}).get("edges", [{}])[0].get("node", {}).get("price", {})
                price_amount = price_info.get("amount")
                currency_code = price_info.get("currencyCode")
                
                if title and price_amount:
                    products_data.append({
                        "source": store_url,
                        "product_title": title,
                        "price": float(price_amount),
                        "currency": currency_code,
                        "product_url": url # This will now have a value
                    })
            
            has_next_page = page_info.get("hasNextPage", False)
            if has_next_page:
                cursor = page_info.get("endCursor")

        except Exception as e:
            print(f"❌ An unexpected error occurred for {store_url}: {e}")
            break

    return products_data

def search_products_across_stores(search_query):
    all_found_products = []
    print(f"\nℹ️ Searching for '{search_query}'...")
    for store in SHOPIFY_STORES:
        print(f"  Fetching from {store['name']}...")
        products = get_shopify_products(store["url"], store["storefront_access_token"], search_query)
        if products:
            all_found_products.extend(products)
            print(f"    Found {len(products)} products.")
        else:
            print(f"    No products found or error.")
            
    all_found_products.sort(key=lambda p: p.get("price", float('inf')))
    return all_found_products

if __name__ == "__main__":
    test_product_query = "Iphone 16" 
    results = search_products_across_stores(test_product_query)
    if results:
        print("\n✅ Found products:")
        for product in results:
            print(f"  Title: {product['product_title']}, Price: {product['currency']} {product['price']:.2f}, URL: {product['product_url']}")
    else:
        print("\n❌ No products found.")
"""This module provides functions to interact with the Cloudprinter API for product retrieval."""

import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

URL_PRODUCT_INFO = "https://api.cloudprinter.com/cloudcore/1.0/products/info"
URL_QUOTE = "https://api.cloudprinter.com/cloudcore/1.0/orders/quote"

API_KEY = os.getenv("CLOUDPRINT_API_KEY")

headers = {"Content-Type": "application/json"}
payload = json.dumps({"apikey": API_KEY})

with open('src/products.json', "r") as f:
    products_string = f.read()  # Read the JSON as a string
    PRODUCTS = json.loads(products_string)  # Parse the string into a Python list of dictionaries

def filter_products_by_category(category_name: str):
    """Fetches products based on the given category name."""
    try:
        filtered_products = [
            product
            for product in PRODUCTS
            if product["category"].lower() == category_name.lower()
        ]

        if not filtered_products:
            return {"error": "No products found for the given category."}

        return filtered_products
    except requests.exceptions.RequestException as e: # Catch network related errors.
        print(f"ERROR: filter_products_by_category failed: {e}")
        return {"error": f"Network error: {e}"}
    except json.JSONDecodeError as e: # Catch json decode errors.
        print(f"ERROR: filter_products_by_category failed: {e}")
        return {"error": f"Json decode error: {e}"}
    except Exception as e: # catch other errors.
        print(f"ERROR: filter_products_by_category failed: {e}")
        return {"error": f"Unexpected error: {e}"}


def get_product_info_by_reference(reference: str):
    """Fetches detailed information about a product using its reference."""
    try:
        payload = json.dumps({"apikey": API_KEY, "reference": reference})

        response = requests.post(URL_PRODUCT_INFO, headers=headers, data=payload, timeout=10)

        return [response.json()]
    except requests.exceptions.RequestException as e:
        print(f"ERROR: get_product_info_by_reference failed: {e}")
        return {"error": f"Network error: {e}"}
    except json.JSONDecodeError as e:
        print(f"ERROR: get_product_info_by_reference failed: {e}")
        return {"error": f"Json decode error: {e}"}
    except Exception as e:
        print(f"ERROR: get_product_info_by_reference failed: {e}")
        return {"error": f"Unexpected error: {e}"}

def ffetch_pricing_info(country: str, items: list):
    """
    Fetches pricing information from the CloudPrinter API based on customer-provided inputs.

    Args:
        apikey (str): API access key for authenticating the request.
        currency (str): The currency for the price quote (ISO 4217). Defaults to "EUR".
        country (str): The country code where the order will ship to.
        state (str, optional): The end customer's state name (ANSI INCITS 38:2009 alpha-2). Required for US-based orders.
        items (list): A list of dictionaries representing the items in the order. Each dictionary must include:
            - reference (str): A unique identifier for the item.
            - product (str): The product ID.
            - count (str): The quantity of the product.
            - options (list, optional): A list of dictionaries representing additional configurations for the item. 
            Each dictionary must include:
                - type (str): The type of option (e.g., "pageblock_80off").
                - count (str): The count for the option.

    Returns:
        dict: A dictionary containing the following pricing information:
            - price (str): The total product sum for the order, excluding shipping and including VAT.
            - vat (str): The VAT part of the total product sum.
            - currency (str): The currency of the price quote.
            - invoice_currency (str): The currency of the invoice for the order.
            - invoice_exchange_rate (str): The exchange rate between the quote currency and invoice currency.
            - expire_date (str): The quote expiration date (48 hours from the request time).
            - subtotals (list): A list of objects representing subtotals for items, fees, and app fees.
                - items (str): The sum of the item costs.
                - fee (str): The sum of fees for the order.
                - app_fee (str): The sum of app fees for the order.
            - shipments (list): A list of objects representing shipment details, including:
                - total_weight (str): The total calculated weight of the shipment.
                - items (list): A list of dictionaries for each item in the shipment, including:
                    - reference (str): The item reference.
                - quotes (list): A list of available shipping options, including:
                    - quote (str): The unique quote ID.
                    - service (str): The shipping service level name.
                    - shipping_level (str): The shipping service level reference.
                    - shipping_option (str): A description of the shipping option.
                    - price (str): The price of the shipment, including VAT.
                    - vat (str): The VAT part of the shipment.
                    - currency (str): The currency of the shipment quote.
    """

    try:
        payload = json.dumps({
            "apikey": API_KEY,
            "country": country,
            "items": items
        })

        response = requests.post(URL_QUOTE, headers=headers, data=payload, timeout=10)
        response_data = response.json()

        if response.status_code == 200:
            return response_data  # Pricing details
        else:
            return {"error": response_data.get("error", "Unknown error occurred")}
    except requests.exceptions.RequestException as e:
        print(f"ERROR: fetch_pricing_info failed: {e}")
        return {"error": f"Network error: {e}"}
    except json.JSONDecodeError as e:
        print(f"ERROR: fetch_pricing_info failed: {e}")
        return {"error": f"JSON decode error: {e}"}
    except Exception as e:
        print(f"ERROR: fetch_pricing_info failed: {e}")
        return {"error": f"Unexpected error: {e}"}
    
def fetch_pricing_info(country: str, reference: str, count: str, options: list, uni = "ref_id_1234567"):
    """Fetches pricing quote for an order."""
    url = "https://api.cloudprinter.com/cloudcore/1.0/orders/quote"

    payload = json.dumps({
        "apikey": API_KEY,
        "country": country,
        "items": [
            {
                "reference": uni,
                "product": reference,
                "count": count,
                "options": options
            }
        ]
    })
    print(payload)

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        # response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        # Check for API-specific errors
        if "error" in data and "info" in data["error"]:
            return {"user_error": data["error"]["info"]}  # Return user-friendly error
        
        return data  # Return successful response

        # return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: get_order_quote failed: {e}")
        return {"error": f"Network error: {e}"}
    except json.JSONDecodeError as e:
        print(f"ERROR: get_order_quote failed: {e}")
        return {"error": f"Json decode error: {e}"}
    except Exception as e:
        print(f"ERROR: get_order_quote failed: {e}")
        return {"error": f"Unexpected error: {e}"}

# # Example input for the tool
# country = "NL"
# items = [
#     {
#         "reference": "ref_id_1234567",
#         "product": "textbook_pb_a4_p_bw",
#         "count": "1",
#         "options": [
#             {"type": "pageblock_80off", "count": "120"},
#             {"type": "total_pages", "count": "120"}
#         ]
#     }
# ]

# # Fetch pricing info
# pricing_details = fetch_pricing_info(country, items)

# # Example output
# if "error" in pricing_details:
#     print(f"Error fetching pricing: {pricing_details['error']}")
# else:
#     print(f"Pricing details: {pricing_details}")
"""This module provides functions to interact with the Cloudprinter API for product retrieval."""

import json
import requests
import os
import uuid
from dotenv import load_dotenv
from logger import setup_logger

load_dotenv()
logging = setup_logger()

URL_PRODUCT_INFO = "https://api.cloudprinter.com/cloudcore/1.0/products/info"
URL_QUOTE = "https://api.cloudprinter.com/cloudcore/1.0/orders/quote"

API_KEY = os.getenv("CLOUDPRINT_API_KEY")

headers = {"Content-Type": "application/json"}
payload = json.dumps({"apikey": API_KEY})

id = str(uuid.uuid4())

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
    
def fetch_pricing_info(country: str, reference: str, count: str, options: list, unii = str(id)):
    """Fetches pricing quote for an order."""
    url = "https://api.cloudprinter.com/cloudcore/1.0/orders/quote"

    payload = json.dumps({
        "apikey": API_KEY,
        "country": country,
        "items": [
            {
                "reference": unii,
                "product": reference,
                "count": count,
                "options": options
            }
        ]
    })
    logging.error(payload)

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        # response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()

        if "error" in data and "info" in data["error"]:
            return {"user_error": data["error"]["info"]}
        
        return data

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
    

def create_order(email: str, addresses: list, items: list, unii = str(id)):
    """
    Creates a print order through the Cloudprinter API.

    Submits an order with customer's email, delivery address, and item configuration 
    including files and options. The payload must match Cloudprinter's required format.

    Args:
        email (str): Customer's email address.
        addresses (list): A list with at least one address dict having keys:
            - type (e.g., "delivery")
            - company (optional), firstname, lastname
            - street1, zip, city, country (ISO code, e.g., "DE")
            - email, phone
        items (list): A list of item dicts, each including:
            - reference: A unique internal reference
            - product_reference: Product reference from Cloudprinter
            - shipping_level: e.g., "cp_ground"
            - title: Short product title
            - count: Quantity
            - files: A list with 1–2 file dicts:
                - type: "cover" or "book"
                - url: Public file URL
                - md5sum: MD5 checksum of the file
            - options: List of option dicts:
                - option_reference: Reference of the product option
                - count: Quantity for this option
        unii (str, optional): Unique identifier for the order (default: "ref_iddd_1234567")

    Returns:
        requests.Response: The raw response from Cloudprinter. Use `.json()` to parse.

    Example:
        create_order(
            email="user@example.com",
            addresses=[{
                "type": "delivery",
                "firstname": "John",
                "lastname": "Doe",
                "street1": "123 Fake Street",
                "zip": "5678 AB",
                "city": "Amsterdam",
                "country": "NL",
                "email": "user@example.com",
                "phone": "0123456789"
            }],
            items=[{
                "reference": "ref_id_1234567",
                "product_reference": "businesscard_ss_us_p_bc_fc",
                "shipping_level": "cp_ground",
                "title": "Business Card - Single Sided - Portrait",
                "count": 50,
                "files": [
                    {
                        "type": "cover",
                        "url": "https://example.com/businesscard-cover.pdf",
                        "md5sum": "abc123..."
                    },
                    {
                        "type": "book",
                        "url": "https://example.com/businesscard-inside.pdf",
                        "md5sum": "def456..."
                    }
                ],
                "options": [
                    {"option_reference": "paper_250ecb", "count": 50},
                    {"option_reference": "product_finish_none", "count": 50},
                    {"option_reference": "right_angled_corners", "count": 50}
                ]
            }]
        )
    """

    url = "https://api.cloudprinter.com/cloudapps/1.0/orders/add"

    payload = {
        "reference": unii,
        "email": email,
        "addresses": addresses,
        "items": items
    }
    logging.error(payload)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer afdaefa5af4439f622395592ca07050a55c4d085',
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return response.text

    except requests.exceptions.RequestException as e:
        print(f"ERROR: create_order failed: {e}")
        return {"error": f"Network error: {e}"}
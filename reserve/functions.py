import json
import requests

URL_PRODUCTS = "https://api.cloudprinter.com/cloudcore/1.0/products"
URL_PRODUCT_INFO = "https://api.cloudprinter.com/cloudcore/1.0/products/info"

API_KEY = "bed884d6def704a005fa85b2605dac91"

headers = {'Content-Type': 'application/json'}
payload = json.dumps({"apikey": API_KEY})

response = requests.post(URL_PRODUCTS, headers=headers, data=payload)
PRODUCTS = json.loads(response.text)

def filter_products_by_category(category_name: str):
    """Fetches products based on the given category name."""
    try:
        filtered_products = [
            product for product in PRODUCTS if product["category"].lower() == category_name.lower()
        ]
        
        if not filtered_products:
            return {"error": "No products found for the given category."}

        return filtered_products
    except Exception as e:
        print(f"ERROR: filter_products_by_category failed: {e}")
        return {"error": str(e)}

def get_product_info_by_reference(reference: str):
    """Fetches detailed information about a product using its reference."""
    try:
        payload = json.dumps({
            "apikey": API_KEY,
            "reference": reference
        })
        
        response = requests.post(URL_PRODUCT_INFO, headers=headers, data=payload)
        
        return [response.json()]
    except Exception as e:
        print(f"ERROR: get_product_info_by_reference failed: {e}")
        return {"error": str(e)}

# print(type(get_product_info_by_reference('businesscard_ds_30x70_mm_p_bc_fc')))
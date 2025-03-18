import json

# Sample JSON data (Replace this with your actual JSON data)
json_data = '''
[
    {
        "category": "Wall decoration",
        "name": "Alu wall decor 24.00x36.00 in FC DWF",
        "note": "Aluminum wall decoration - Die Cut - 24.00x36.00 in Portrait - FC Digital Wide Format",
        "reference": "wall_decor_2400x3600_in_alu_fc",
        "availability": "Regional"
    },
    {
        "category": "Business card",
        "name": "Business card SS US P FC TNR",
        "note": "Business card - Single Sided - Cut to Size - 2.00x3.50 in - Portrait - FC TNR",
        "reference": "businesscard_ss_us_p_bc_fc",
        "availability": "Regional"
    }
]
'''

# Convert JSON string to Python list
products = json.loads(json_data)

# Function to filter by category
def filter_by_category(category_name):
    return [item for item in products if item["category"].lower() == category_name.lower()]

# User Input (e.g., from a chatbot)
user_input = "wall decoration"

# Filtering
filtered_products = filter_by_category(user_input)

# Output the result
print(json.dumps(filtered_products, indent=4))

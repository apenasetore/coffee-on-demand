import os

from dotenv import load_dotenv
import embedded.coffee_api.http_requests as http_requests

load_dotenv()

COFFEE_API_URL = os.getenv('COFFEE_API_URL')
COFFEE_API_KEY = os.getenv('COFFEE_API_KEY')

def get_customers():
    try:
        response = http_requests.get(f'{COFFEE_API_URL}/customer', {"x-api-key": COFFEE_API_KEY})
        return response.json() 
    except Exception as e:
        print(f"Error while fetching customers: {e}")
        return {}
    
def add_customer(firstname: str, lastname: str):
    try:
        response = http_requests.post(f'{COFFEE_API_URL}/customer', {"firstname": firstname, "lastname": lastname}, {"x-api-key": COFFEE_API_KEY})
        return response.json() 
    except Exception as e:
        print(f"Error while adding customer {firstname} {lastname}: {e}")
        return {}

def get_purchases(customer_id: int):
    try:
        response = http_requests.get(f'{COFFEE_API_URL}/purchase', {"x-api-key": COFFEE_API_KEY}, {"customer_id": customer_id})
        return response.json()
    except Exception as e:
        print(f"Error while fetching purchases for customer {customer_id}: {e}")
        return {}

def get_coffees(only_active: bool = True):
    try:
        response = http_requests.get(f'{COFFEE_API_URL}/coffee', {"x-api-key": COFFEE_API_KEY}, {"only_active": "true" if only_active else "false"})
        return response.json()
    except Exception as e:
        print(f"Error while fetching coffees: {e}")
        return {}
    
def add_notification(content: str):
    try:
        response = http_requests.post(f'{COFFEE_API_URL}/notification', {"content": content}, {"x-api-key": COFFEE_API_KEY})
        return response.json() 
    except Exception as e:
        print(f"Error while adding notification {content}: {e}")
        return {}
    
def add_picture(customer_id: int, image_base64: str):
    try:
        response = http_requests.post(f'{COFFEE_API_URL}/picture', {"customer_id": customer_id, "image_base64": image_base64}, {"x-api-key": COFFEE_API_KEY})
        return response.json() 
    except Exception as e:
        print(f"Error while adding picture to customer {customer_id}: {e}")
        return {}
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
    
def create_payment(value: float):
    try:
        response = http_requests.get(f'{COFFEE_API_URL}/payment/createPayment?value={value}')
        return response.json() 
    except Exception as e:
        print(f"Error while creating payment: {e}")
        return {}

def verify_payment(payment_id: int):
    print(f'{COFFEE_API_URL}/payment/checkPayment?paymentId={payment_id}')
    try:
        response = http_requests.get(f'{COFFEE_API_URL}/payment/checkPayment?paymentId={payment_id}')
        return response.json() 
    except Exception as e:
        print(f"Error while verifying payment {payment_id}: {e}")
        return {}
    
def add_purchase(customer_id: int, weight: int, coffee_id: int):
    try:
        response = http_requests.post(f'{COFFEE_API_URL}/purchase', {"customer_id": customer_id, "weight": weight, "coffee_id": coffee_id}, {"x-api-key": COFFEE_API_KEY})
        return response.json() 
    except Exception as e:
        print(f"Error while adding purchase for customer {customer_id}: {e}")
        return {}

def update_coffee_quantity(coffee_id: int, weight: int):
    try:
        response = http_requests.patch(f'{COFFEE_API_URL}/coffee', {"weight": weight, "coffee_id": coffee_id}, {"x-api-key": COFFEE_API_KEY})
        return response.json() 
    except Exception as e:
        print(f"Error while updating quantity of {coffee_id}: {e}")
        return {}
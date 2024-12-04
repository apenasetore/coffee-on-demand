# Import the requests library
import requests


def get(url, headers=None, query_params=None):
    try:
        response = requests.get(url, headers=headers, params=query_params)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"GET request failed: {e}")


def post(url, data, headers=None):
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response

    except requests.RequestException as e:
        print(f"POST request failed: {e}")

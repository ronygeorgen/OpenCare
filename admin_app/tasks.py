import requests
from celery import shared_task

@shared_task
def make_api_call():
# Make your API call here
    try:
        response = requests.get('https://your-api-endpoint.com/api/')
# Process response as needed
        print(f"API call made: Status Code {response.status_code}")
        return f"API call successful: {response.status_code}"
    except Exception as e:
        print(f"API call failed: {str(e)}")
        return f"API call failed: {str(e)}"

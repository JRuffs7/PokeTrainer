import requests


def MakeApiCall(domain, endpoint, *params):
  try:
    response = requests.get(f"{domain}/{endpoint}/{'&'.join(params)}")
    if response.status_code == 200:
      return response.json()
    raise Exception(
        f"Api call failed with status code: {response.status_code}\n{domain}/{endpoint}/{'&'.join(params)}"
    )
  except Exception as e:
    print(e)
    return None


def MakeFullApiCall(endpoint):
  try:
    response = requests.get(endpoint)
    if response.status_code == 200:
      return response.json()
    raise Exception(
        f"Api call failed with status code: {response.status_code}\n{endpoint}"
    )
  except Exception as e:
    print(e)
    return None

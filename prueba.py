import requests

response = requests.get(
    'https://api.factiliza.com/v1/dni/info/27427864',
    headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MTQ3MyIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6ImNvbnN1bHRvciJ9.tuJcKE7mDIfobCcJhVXecRuDSVJTfmgSfRMcia44Zvk'}
)
print(response.status_code)
print(response.text)
print(response.headers)
import requests

ZABBIX_URL = "http://10.144.2.194/zabbix/api_jsonrpc.php"

async def zabbix_login(username, password):
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": username,
            "password": password
        },
        "id": 1,
        "auth": None
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            return result['result']
        else:
            raise Exception("Credenciales incorrectas.")
    else:
        raise Exception(f"Error en la autenticación: {response.status_code}")
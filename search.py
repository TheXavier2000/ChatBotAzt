import requests

ZABBIX_URL = "http://10.144.2.194/zabbix/api_jsonrpc.php"

# Función para buscar hosts por nombre
async def search_host_by_name(auth_token, host_name,host_type):
    if host_type=="Equipos Networking":
       group=50
    elif host_type=="Clientes":
         group=51
    elif host_type=="Rectificadores":
         group=53
    elif host_type=="Plantas":
         group=76


         
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "name"],
            "groupids":group,
            "search": {"name": host_name}
        },
        "id": 2,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])
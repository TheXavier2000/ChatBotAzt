import requests
import time
from config import ZABBIX_URL

# Función para autenticarse en Zabbix
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

# Función para buscar hosts por nombre
def search_host_by_name(auth_token, host_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "name"],
            "search": {"name": host_name}  # Coincidencia parcial de nombre
        },
        "id": 2,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    
    try:
        response = requests.post(ZABBIX_URL, json=payload, headers=headers)
        response_data = response.json()

        # Depuración: Ver la respuesta de Zabbix
        print(f"Respuesta de Zabbix: {response_data}")

        return response_data.get('result', [])
    except Exception as e:
        print(f"Error al buscar hosts: {e}")
        return []


# Función para obtener problemas en un host específico
def get_problems(auth_token, host_id, filter_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "output": "extend",
            "hostids": host_id,
            "time_from": int(time.time() - 12 * 3600),  # Últimas 12 horas
            "recent": True,
            "search": {"name": filter_name},
            "sortfield": ["eventid"],
            "sortorder": "DESC"
        },
        "id": 3,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])

# Función para obtener gráficas en un host específico
def get_graphs(auth_token, host_id, filter_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "graph.get",
        "params": {
            "output": ["graphid", "name"],
            "hostids": host_id,
            "search": {"name": filter_name},
        },
        "id": 4,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])

# Función para obtener ítems por host con un filtro
def get_items(auth_token, host_id, filter_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid", "name"],
            "hostids": host_id,
            "search": {"name": filter_name},
        },
        "id": 5,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])

# Función para generar la URL de la gráfica o del elemento
def generate_graph_url(graph_id=None, item_id=None, chart_type="chart.php"):
    base_url = f"http://10.144.2.194/zabbix/{chart_type}"
    if graph_id:
        # URL para gráficos
        url = f"{base_url}?graphid={graph_id}&from=now-12h&to=now&height=201&width=1188&profileIdx=web.charts.filter"
        return url
    elif item_id:
        # URL para elementos
        url = f"{base_url}?itemids[]={item_id}&from=now-12h&to=now&height=201&width=1188&profileIdx=web.charts.filter"
        return url
    else:
        raise ValueError("Debe proporcionar un graph_id o un item_id.")


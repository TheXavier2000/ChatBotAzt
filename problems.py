import requests
import time
from io import BytesIO


ZABBIX_URL = "http://10.144.2.194/zabbix/api_jsonrpc.php"

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
            "sortfield": ["eventid"],
            "sortorder": "DESC"
        },
        "id": 3,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])

def get_graphs(auth_token, host_id,item_tipo):
        
    payload = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["itemid", "name"],
                "hostids": host_id,
                "search": {"name": item_tipo},
                  "sortfield": "name"  # Utilizar el valor actual de tipo
            },

            "id": 5,
            "auth": auth_token
        }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    graphs = response.json()  # Aquí asumo que la API devuelve un JSON
    print("Gráficas obtenidas:", graphs)  # Verifica si las gráficas están siendo devueltas
    return response.json().get('result', [])

def get_inter1(auth_token, host_id):
    # Payload modificado para buscar "Gigabit" en los gráficos
    payload = {
        "jsonrpc": "2.0",
        "method": "graph.get",  # Buscamos gráficos
        "params": {
            "output": ["graphid", "name"],  # Buscamos "graphid" y "name"
            "hostids": host_id,
            "search": {"name": "Gigabit"}  # Buscamos gráficos con "Gigabit" en el nombre
        },
        "id": 5,
        "auth": auth_token
    }

    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    
    # Asumimos que la respuesta es un JSON
    graphs = response.json()
    result = response.json().get('result', [])  # Extraemos la lista de resultados
    print(result)
    
    if not result:
        print("No se encontraron gráficos con 'Gigabit'.")
        return []  # Si no hay resultados, retornamos una lista vacía

    # Creamos un diccionario para almacenar graphid y nombre
    filtered_graphs = {}

    # Recorremos los resultados para extraer los nombres y graphid
    for item in result:
        if isinstance(item, dict) and 'name' in item and 'graphid' in item:
            graph_name = item['name'].lower()

            # Filtramos solo aquellos gráficos que contienen 'network traffic' y excluimos 'bits' o 'bytes'
            if 'network traffic' in graph_name and not ('bits' in graph_name or 'bytes' in graph_name):
                # Extraemos el nombre antes del paréntesis (si existe)
                name_before_colon = item['name'].split('Network')[0].strip()
                filtered_graphs[name_before_colon] = item['graphid']  # Guardamos el graphid asociado

        else:
            print(f"Elemento inesperado en result: {item}")

    # Si se encuentran gráficos con 'Gigabit' y 'network traffic', los mostramos
    if filtered_graphs:
        print("Gráficos con 'Gigabit' y 'network traffic':")
        for name, graphid in filtered_graphs.items():
            print(f"Nombre: {name}, graphid: {graphid}")
    else:
        print("No se encontraron gráficos con 'Gigabit' y 'network traffic'.")

    # Devolvemos el diccionario con nombres y graphid
    return filtered_graphs

def get_inter2(auth_token, host_id):
    # Payload modificado para buscar "Gigabit" en los gráficos
    payload = {
        "jsonrpc": "2.0",
        "method": "graph.get",  # Buscamos gráficos
        "params": {
            "output": ["graphid", "name"],  # Buscamos "graphid" y "name"
            "hostids": host_id,
            "search": {"name": "Eth-"}  # Buscamos gráficos con "Gigabit" en el nombr
        },
        "id": 5,
        "auth": auth_token
    }

    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    
    # Asumimos que la respuesta es un JSON
    graphs = response.json()
    result = response.json().get('result', [])  # Extraemos la lista de resultados
    print(result)
    
    if not result:
        print("No se encontraron gráficos con 'Gigabit'.")
        return []  # Si no hay resultados, retornamos una lista vacía

    # Creamos un diccionario para almacenar graphid y nombre
    filtered_graphs = {}

    # Recorremos los resultados para extraer los nombres y graphid
    for item in result:
        if isinstance(item, dict) and 'name' in item and 'graphid' in item:
            graph_name = item['name'].lower()

            # Filtramos solo aquellos gráficos que contienen 'network traffic' y excluimos 'bits' o 'bytes'
            if 'network traffic' in graph_name and not ('bits' in graph_name or 'bytes' in graph_name):
                # Extraemos el nombre antes del paréntesis (si existe)
                name_before_colon = item['name'].split('Network')[0].strip()
                filtered_graphs[name_before_colon] = item['graphid']  # Guardamos el graphid asociado

        else:
            print(f"Elemento inesperado en result: {item}")

    # Si se encuentran gráficos con 'Gigabit' y 'network traffic', los mostramos
    if filtered_graphs:
        print("Gráficos con 'Gigabit' y 'network traffic':")
        for name, graphid in filtered_graphs.items():
            print(f"Nombre: {name}, graphid: {graphid}")
    else:
        print("No se encontraron gráficos con 'Gigabit' y 'network traffic'.")

    # Devolvemos el diccionario con nombres y graphid
    return filtered_graphs

def get_inter3(auth_token, host_id):
    # Payload modificado para buscar "Gigabit" en los gráficos
    payload = {
        "jsonrpc": "2.0",
        "method": "graph.get",  # Buscamos gráficos
        "params": {
            "output": ["graphid", "name"],  # Buscamos "graphid" y "name"
            "hostids": host_id,
            "search": {"name": "LAG"}  # Buscamos gráficos con "Gigabit" en el nombre
        },
        "id": 5,
        "auth": auth_token
    }

    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    
    # Asumimos que la respuesta es un JSON
    graphs = response.json()
    result = response.json().get('result', [])  # Extraemos la lista de resultados
    print(result)
    
    if not result:
        print("No se encontraron gráficos con 'Gigabit'.")
        return []  # Si no hay resultados, retornamos una lista vacía

    # Creamos un diccionario para almacenar graphid y nombre
    filtered_graphs = {}

    # Recorremos los resultados para extraer los nombres y graphid
    for item in result:
        if isinstance(item, dict) and 'name' in item and 'graphid' in item:
            graph_name = item['name'].lower()

            # Filtramos solo aquellos gráficos que contienen 'network traffic' y excluimos 'bits' o 'bytes'
            if 'network traffic' in graph_name and not ('bits' in graph_name or 'bytes' in graph_name):
                # Extraemos el nombre antes del paréntesis (si existe)
                name_before_colon = item['name'].split('Network')[0].strip()
                filtered_graphs[name_before_colon] = item['graphid']  # Guardamos el graphid asociado

        else:
            print(f"Elemento inesperado en result: {item}")

    # Si se encuentran gráficos con 'Gigabit' y 'network traffic', los mostramos
    if filtered_graphs:
        print("Gráficos con 'Gigabit' y 'network traffic':")
        for name, graphid in filtered_graphs.items():
            print(f"Nombre: {name}, graphid: {graphid}")
    else:
        print("No se encontraron gráficos con 'Gigabit' y 'network traffic'.")

    # Devolvemos el diccionario con nombres y graphid
    return filtered_graphs

def get_inter_cliente(auth_token, host_id):
    """
    Filtra gráficas de interfaces específicas para Clientes.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "graph.get",
        "params": {
            "output": ["graphid", "name"],
            "hostids": host_id,
            "search": {"name": "Interface"}  # Filtro por texto que contenga "Interface"
        },
        "id": 6,
        "auth": auth_token
    }

    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    result = response.json().get('result', [])

    # Procesar los resultados
    filtered_graphs = {
        item['name']: item['graphid']
        for item in result
        if 'Interface' in item['name']  # Condición para incluir nombres con "Interface"
    }

    return filtered_graphs

def get_hosts_by_location(auth_token, location_value):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "name"],  # Solo se obtienen hostid y name
            "filter": {
                "site_state": location_value  # Filtra por 'site_state'
            }
        },
        "auth": auth_token,
        "id": 1
    }

    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)

    if response.status_code == 200:
        try:
            hosts = response.json().get('result', [])
            return hosts
        except ValueError:
            print("Error al procesar la respuesta JSON.")
            return []
    else:
        print(f"Error en la solicitud de consulta de hosts: {response.status_code} - {response.text}")
        return []


def get_problems_by_hosts(auth_token, filter_value):
    payload = {
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "output": "extend",
            "selectAcknowledges": "extend",
            "selectTags": "extend",
            "selectSuppressionData": "extend",
            "search": {
                "host": filter_value
            },
            "severities": [4],  
            "recent": True,
            "sortfield": ["eventid"],
            "sortorder": "DESC"
        },
        "auth": auth_token,
        "id": 4
    }

    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)

    if response.status_code == 200:
        try:
            problems = response.json().get('result', [])
            # Imprimir resultados en la terminal
            print(f"Resultados para {filter_value}:")
            for problem in problems:
                print(f"ID: {problem['eventid']}, Problema: {problem['name']}")
            return problems
        except ValueError:
            print("Error al procesar la respuesta JSON.")
            return []
    else:
        print(f"Error en la solicitud de consulta: {response.status_code} - {response.text}")
        return []



def generate_graph_url(graph_id=None, item_id=None, chart_type="chart.php"):
    #item_id=255223
    base_url = f"http://10.144.2.194/zabbix/{chart_type}"
    if graph_id:
        # URL para gráficos
        url = f"{base_url}?graphid={graph_id}&from=now-12h&to=now&height=201&width=1188&profileIdx=web.charts.filter"
        return url
    elif item_id:
        # URL para elementos
       url = f"{base_url}?itemids[]={item_id}&from=now-12h&to=now&height=201&width=1188&profileIdx=web.charts.filter"
       #url = f"{base_url}?graphid={item_id}&from=now-12h&to=now&height=201&width=1188&profileIdx=web.charts.filter"
       #url = f"http://10.144.2.194/zabbix/chart2.php?grapdids={item_id}&width=900&height=200"

       return url
    else:
        raise ValueError("Debe proporcionar un graph_id o un item_id.")

def download_image(url):
    headers = {
        'Cookie': 'zbx_session=eyJzZXNzaW9uaWQiOiJmNTcxNmQ3YzkxNmNhYjc5YTIxMTczMTM1MzI5MjQzNSIsInNlcnZlckNoZWNrUmVzdWx0Ijp0cnVlLCJzZXJ2ZXJDaGVja1RpbWUiOjE3MjY1OTE1NzUsInNpZ24iOiJjZjEwNzZkMzNkNDgwODQ2NjdkNGJlMjkwMzY5NmUyMmMyZTQxNTk3NzdkYjAzYTAyMGQ3NjFlNmU1MjA0MTliIn0%3D',  # Reemplaza con tu token de sesión
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Lanza una excepción si ocurre un error HTTP

        if 'image' in response.headers.get('Content-Type', ''):
            return BytesIO(response.content)
        else:
            raise Exception("El contenido descargado no es una imagen.")
    
    except requests.RequestException as e:
        raise Exception(f"Error al descargar la imagen: {e}")
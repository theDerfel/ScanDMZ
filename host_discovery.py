import os
import xml.etree.ElementTree as ET
import uuid
import mysql.connector
from datetime import datetime

# Conexão com o banco de dados
conn = mysql.connector.connect(
    host='localhost',
    user='nmapython',
    password='nmapython',
    database='dmzmap'
)

cursor = conn.cursor()

# Função para criar tabelas no banco de dados
def database():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dmz_scans(
            host_id VARCHAR(36) NOT NULL PRIMARY KEY, 
            scan_id VARCHAR(36), 
            endtime DATETIME, 
            status VARCHAR(10), 
            address VARCHAR(15), 
            hostname VARCHAR(255),
            FOREIGN KEY (scan_id) REFERENCES dmz_scans(scan_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dmz_scans(
            scan_id VARCHAR(36) NOT NULL PRIMARY KEY, 
            scan_type VARCHAR(10), 
            scan_date DATETIME
        )
    ''')

# Função para extrair informações do XML e inseri-las no banco de dados
def host_discovery(file_path, scan_id):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Encontrar o atributo startstr do elemento root
    endtime = root.get('startstr')
    try:
        # Converter o atributo startstr para datetime e formatar como string
        scan_date = datetime.strptime(endtime, '%a %b %d %H:%M:%S %Y')
        formatted_scan_date = scan_date.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        print(f"Erro ao converter endtime '{endtime}': {e}")
        formatted_scan_date = None
    
    for host in root.findall('host'):
        host_id = str(uuid.uuid4())
        status = host.find('status').get('state')
        address = host.find('address').get('addr')
        hostname_element = host.find('hostnames/hostname')
        hostname = hostname_element.get('name') if hostname_element is not None else 'N/A'
        
        cursor.execute('''
            INSERT INTO dmz_hosts (host_id, scan_id, endtime, status, address, hostname)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (host_id, scan_id, formatted_scan_date, status, address, hostname))

    # Commit para salvar as mudanças no banco de dados
    conn.commit()

# Função para processar todos os arquivos XML na pasta
def process_all_xml_files(folder_path):
    scan_id = str(uuid.uuid4())
    scan_date = datetime.now()
    cursor.execute('''
        INSERT INTO dmz_scans (scan_id, scan_type, scan_date) 
        VALUES (%s, %s, %s)
    ''', (scan_id, 'hosts', scan_date))
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xml'):
            file_path = os.path.join(folder_path, file_name)
            try:
                host_discovery(file_path, scan_id)
            except Exception as e:
                print(f"Erro ao processar o arquivo {file_name}: {e}")

# Caminho para a pasta contendo os arquivos XML
folder_path = 'hosts/'

# Criar tabelas no banco de dados
database()

# Processar todos os arquivos XML na pasta
process_all_xml_files(folder_path)

# Fechar a conexão com o banco de dados
cursor.close()
conn.close()

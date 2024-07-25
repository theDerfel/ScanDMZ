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
            scan_id VARCHAR(36) NOT NULL PRIMARY KEY, 
            scan_type VARCHAR(10), 
            scan_date DATETIME
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dmz_ports(
            port_id VARCHAR(36) NOT NULL PRIMARY KEY, 
            scan_id VARCHAR(36), 
            port_number VARCHAR(6), 
            port_state VARCHAR(10), 
            port_protocol VARCHAR(3), 
            port_ip VARCHAR(15), 
            service_type VARCHAR(20), 
            service_version VARCHAR(40), 
            scan_date DATETIME,
            FOREIGN KEY (scan_id) REFERENCES dmz_scans(scan_id)
        )
    ''')

# Função para extrair informações do XML e inseri-las no banco de dados
def xmlToDB(file_path, scan_id):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Encontrar o atributo endtime do elemento host
    host = root.find('host')
    endtime = host.get('endtime')
    scan_date = datetime.utcfromtimestamp(int(endtime))
    
    # Encontrar o atributo address do elemento host
    address = host.find('address').get('addr')
    
    for port in host.findall('ports/port'):
        port_id = str(uuid.uuid4())
        protocol = port.get('protocol')
        portid = port.get('portid')
        state = port.find('state').get('state')
        service = port.find('service')
        service_name = service.get('name') if service is not None else 'N/A'
        service_vendor = service.get('vendor') if service is not None and 'vendor' in service.attrib else 'N/A'
        if state != 'closed':
            cursor.execute('''
                INSERT INTO dmz_ports (port_id, scan_id, port_number, port_state, port_protocol, port_ip, service_type, service_version, scan_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (port_id, scan_id, portid, state, protocol, address, service_name, service_vendor, scan_date))

    # Commit para salvar as mudanças no banco de dados
    conn.commit()

# Função para processar todos os arquivos XML na pasta "ports"
def process_all_xml_files(folder_path):
    scan_id = str(uuid.uuid4())
    scan_date = datetime.now()
    cursor.execute('''
        INSERT INTO dmz_scans (scan_id, scan_type, scan_date) 
        VALUES (%s, %s, %s)
    ''', (scan_id, 'port', scan_date))
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xml'):
            file_path = os.path.join(folder_path, file_name)
            try:
                xmlToDB(file_path, scan_id)
            except:
                pass

# Caminho para a pasta contendo os arquivos XML
folder_path = 'ports'

# Criar tabelas no banco de dados
database()

# Processar todos os arquivos XML na pasta "ports"
process_all_xml_files(folder_path)

# Fechar a conexão com o banco de dados
cursor.close()
conn.close()

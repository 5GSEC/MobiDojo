from flask import Blueprint, render_template, jsonify
import subprocess
from datetime import datetime

function2_bp = Blueprint('function2', __name__, template_folder='/')

@function2_bp.route('/')
def show():
    return render_template('function2.html')

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, cwd='oai', check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    
@function2_bp.route('/turn_on_core', methods=['POST'])
def turn_on_core():
    success, output = run_command('docker-compose -f docker-compose-1gnb3slices.yaml up -d')
    return jsonify({'message': 'Core Network turned on' if success else f'Error: {output}'})

@function2_bp.route('/turn_off_core', methods=['POST'])
def turn_off_core():
    success, output = run_command('docker-compose -f docker-compose-1gnb3slices.yaml stop')
    return jsonify({'message': 'Core Network turned off' if success else f'Error: {output}'})

@function2_bp.route('/turn_on_base', methods=['POST'])
def turn_on_base():
    success, output = run_command('docker-compose -f docker-compose-1gnb3slices-gnbue.yaml up -d oai-gnb')
    return jsonify({'message': 'Base Station turned on' if success else f'Error: {output}'})

@function2_bp.route('/turn_off_base', methods=['POST'])
def turn_off_base():
    success, output = run_command('docker-compose -f docker-compose-1gnb3slices-gnbue.yaml stop oai-gnb')
    return jsonify({'message': 'Base Station turned off' if success else f'Error: {output}'})

@function2_bp.route('/turn_on_ue', methods=['POST'])
def turn_on_ue():
    success, output = run_command('docker-compose -f docker-compose-1gnb3slices-gnbue.yaml up -d oai-nr-ue1 oai-nr-ue2')
    return jsonify({'message': 'UEs turned on' if success else f'Error: {output}'})

@function2_bp.route('/turn_off_ue', methods=['POST'])
def turn_off_ue():
    success, output = run_command('docker-compose -f docker-compose-1gnb3slices-gnbue.yaml stop oai-nr-ue1 oai-nr-ue2')
    return jsonify({'message': 'UEs turned off' if success else f'Error: {output}'})

@function2_bp.route('/turn_on_all', methods=['POST'])
def turn_on_all():
    success1, _ = run_command('docker-compose -f docker-compose-1gnb3slices.yaml up -d')
    success2, _ = run_command('docker-compose -f docker-compose-1gnb3slices-gnbue.yaml up -d oai-gnb oai-nr-ue1 oai-nr-ue2')
    return jsonify({'message': 'All components turned on' if success1 and success2 else 'Error occurred while turning on components'})

@function2_bp.route('/turn_off_all', methods=['POST'])
def turn_off_all():
    success, output = run_command('docker-compose -f docker-compose-1gnb3slices-gnbue.yaml down --remove-orphans')
    return jsonify({'message': 'All components turned off' if success else f'Error: {output}'})

@function2_bp.route('/get_containers', methods=['GET'])
def get_containers():
    result = subprocess.run(['docker', 'ps', '-a'], capture_output=True, text=True)
    containers = result.stdout.split('\n')[1:-1]

    container_status = []
    for container in containers:
        parts = container.split()
        name = parts[-1]
        status = 'healthy' if '(healthy)' in container else 'unhealthy'
        
        if 'ue' in name.lower():
            group = 'UE'
        elif 'gnb' in name.lower():
            group = 'Base Station'
        else:
            group = 'Core Network'

        container_status.append({
            'name': name,
            'status': status,
            'group': group
        })

    return jsonify({'containers': container_status})

@function2_bp.route('/save_log/<container_name>', methods=['POST'])
def save_log(container_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"~/MobiDojo/logs/{timestamp}_{container_name}.log"
    success, output = run_command(f"docker logs {container_name} > {filename} 2>&1")
    return jsonify({'message': f'Log saved to {filename}' if success else f'Error: {output}'})

@function2_bp.route('/save_pcap/<container_name>', methods=['POST'])
def save_pcap(container_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"~/MobiDojo/pcaps/{timestamp}_{container_name}.pcap"
    success, output = run_command(f"docker cp {container_name}:/home/pcap.pcap {filename}")
    return jsonify({'message': f'PCAP saved to {filename}' if success else f'Error: {output}'})

@function2_bp.route('/capture_core', methods=['POST'])
def capture_core():
    date_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    pcap_file = f"~/MobiDojo/pcaps/{date_string}_core.pcap"
    command = f"sudo tshark -i demo-oai -f \"not host 192.168.70.154 and not host 192.168.70.155\" -w {pcap_file}"
    gnome_terminal_command = f"gnome-terminal -- bash -c '{command}; exec bash'"
    
    try:
        subprocess.Popen(gnome_terminal_command, shell=True)
        return jsonify({'message': 'Core network capture started successfully'})
    except Exception as e:
        return jsonify({'message': f'Error starting capture: {str(e)}'}), 500
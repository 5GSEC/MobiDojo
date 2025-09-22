from flask import Blueprint, render_template, request, jsonify
import subprocess
import os

function5_bp = Blueprint('function5', __name__)

@function5_bp.route('/')
def function5():
    return render_template('function5.html')


@function5_bp.route('/launch_spector', methods=['POST'])
def launch_spector():
    attack_type = request.form.get('attack_type')
    val1 = request.form.get('val1')
    val2 = request.form.get('val2')
    addon = request.form.get('addon')

    # Validate input values
    valid_ranges = {
        '1': (1, 999), '2': (1, 999), '3': (1, 999),
        '4': (1, 4), '5': (1, 999), '6': (1, 999), '7': (1, 2)
    }
    
    if attack_type not in valid_ranges or not val1.isdigit() or not valid_ranges[attack_type][0] <= int(val1) <= valid_ranges[attack_type][1]:
        return jsonify({"status": "error", "message": f"Invalid val1 for attack type {attack_type}."})
    
    command_map = {
        '1': f" --bts-attack {val1} --bts-delay {val2}",
        '2': f" --blind-dos-attack {val1} --RRC-TMSI {val2}",
        '3': f" --dnlink-dos-attack {val1}",
        '4': f" --dnlink-imsi-extr {val1}",
        '5': f" --uplink-dos-attack {val1}",
        '6': f" --uplink-imsi-extr {val1}",
        '7': f" --null-cipher-integ {val1}"
    }
    
    command = command_map.get(attack_type, "")
    if addon == 'emergency':
        command += " --rrc-911"
    
    # Check if the attack-nr-ue container exists
    check_command = "docker ps -a --filter name=attack-nr-ue --format '{{.Names}}'"
    
    try:
        check_process = subprocess.Popen(check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check_stdout, check_stderr = check_process.communicate()
        
        container_exists = "attack-nr-ue" in check_stdout.decode('utf-8')
        
        if container_exists:
            # Container exists, restart it
            restart_command = "docker restart attack-nr-ue"
            restart_process = subprocess.Popen(restart_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            restart_stdout, restart_stderr = restart_process.communicate()
            
            if restart_process.returncode == 0:
                return jsonify({"status": "success", "message": "Attack container restarted successfully"})
            else:
                return jsonify({"status": "error", "message": f"Failed to restart container: {restart_stderr.decode('utf-8')}"})
        else:
            # Container doesn't exist, create new one
            docker_command = (
            f"docker run -d --network=host --privileged "
            f"--name attack-nr-ue "
            f"-v {os.getcwd()}/attack.conf:/opt/oai-nr-ue/etc/nr-ue.conf "
            f"-e USE_ADDITIONAL_OPTIONS='--rfsim --log_config.global_log_options level,nocolor,time -E --sa -r 106 --numerology 1 -C 3619200000 --opt.type pcap --opt.path /home/pcap_attack-nr-ue.pcap --rfsimulator.serveraddr 192.168.70.153 {command}' "
            f"-it seranai/oai-nr-ue:nr.attack.v2.1.0 "
            )
            
            process = subprocess.Popen(docker_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                container_id = stdout.decode('utf-8').strip()
                # terminal_command = f"gnome-terminal -- bash -c 'docker exec -it {container_id[:12]} /bin/bash; exec bash'"
                # subprocess.Popen(terminal_command, shell=True)
                return jsonify({"status": "success", "message": f"Attack started in container {container_id[:12]}"})
            else:
                return jsonify({"status": "error", "message": f"Failed to start container: {stderr.decode('utf-8')}"})
                
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@function5_bp.route('/launch_replay', methods=['POST'])
def launch_replay():
    pcap_file = request.form.get('pcap_file')
    if pcap_file:
        try:
            replay_dir = os.path.join(os.path.dirname(__file__), '..', '5greplay')
            command = f"sudo ./5greplay replay -t pcap/{pcap_file}"
            gnome_terminal_command = f"gnome-terminal -- bash -c 'cd {replay_dir} && {command}; exec bash'"
            subprocess.Popen(gnome_terminal_command, shell=True)
            return jsonify({"status": "success", "message": "Replay launched successfully in a new terminal"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "error", "message": "No PCAP file selected"})

@function5_bp.route('/manual_modify', methods=['POST'])
def manual_modify():
    try:
        modify_dir = os.path.join(os.path.dirname(__file__), '..', 'pcap_modifier')
        command = "python3 build.py"
        subprocess.Popen(command, cwd=modify_dir, shell=True)
        return jsonify({"status": "success", "message": "Manual Modify launched successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@function5_bp.route('/auto_modify', methods=['POST'])
def auto_modify():
    try:
        modify_dir = os.path.join(os.path.dirname(__file__), '..', 'pcap_modifier')
        command = "python3 mutator.py"
        gnome_terminal_command = f"gnome-terminal -- bash -c 'cd {modify_dir} && {command}; exec bash'"
        subprocess.Popen(gnome_terminal_command, shell=True)
        return jsonify({"status": "success", "message": "Auto Modify launched successfully in a new terminal"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def init_function5(app, socketio):
    pass

from flask import Blueprint, render_template, request, jsonify
import subprocess

function3_bp = Blueprint('function3', __name__)

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

@function3_bp.route('/', methods=['GET', 'POST'])
def function3():
    if request.method == 'POST':
        selected_container = request.form.get('container', 'ALL')
        logs = []
        error_count = 0
        warning_count = 0
        container_set = set()

        success, output = run_command('docker ps -a --format "{{.Names}}"')
        if not success:
            return jsonify({'error': f'Failed to retrieve container names: {output}'}), 500

        container_names = output.strip().split('\n')
        
        if selected_container == 'ALL':
            containers_to_check = container_names
        else:
            containers_to_check = [selected_container]

        for container in containers_to_check:
            # Limit docker logs to the latest 3000 lines
            success, container_logs = run_command(f'docker logs --tail 3000 {container}')
            if success:
                for line in container_logs.split('\n'):
                    if '[error]' in line.lower() or '[warning]' in line.lower():
                        logs.append(f"{container}: {line}")
                        container_set.add(container)
                        if '[error]' in line.lower():
                            error_count += 1
                        else:
                            warning_count += 1

        return jsonify({
            'logs': logs,
            'error_count': error_count,
            'warning_count': warning_count,
            'containers': list(container_names)  # Always return all container names
        })

    return render_template('function3.html')
import argparse
import sys
import os
import subprocess
import shutil

# Configuration
SSH_KEY_PATH = os.path.join(os.getcwd(), "Stores", "ssh-key-2026-02-08.key")
REMOTE_USER = "ubuntu"
# Actual VPS IP from deploy_vps.bat
REMOTE_HOST_IP = "145.241.226.107" 
REMOTE_DEST_DIR = "/home/ubuntu/ai_brain"

def run_command(command):
    """
    Executes a shell command. On Windows, forces use of cmd /c if needed.
    """
    try:
        if os.name == 'nt':
            # Use cmd /c for Windows compatibility as requested
            # For subprocess list args, we don't strictly need cmd /c unless using shell builtins
            # But user asked for it applied to 'local global rules', so we ensure it.
            # However, for pure executables like scp, direct call is better.
            # We'll use shell=False for safety and list args.
            result = subprocess.run(command, check=True, text=True, capture_output=True, timeout=30)
        else:
            result = subprocess.run(command, check=True, text=True, capture_output=True, timeout=30)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print(e.stderr)
        return False

def generate_deployment_script(service_name):
    """
    Generates a local deployment script that uses SCP to transfer files.
    """
    print(f"Executing deployment for service '{service_name}' to Remote_Oracle_Ubuntu...")
    
    # 1. Verify SSH Key
    if not os.path.exists(SSH_KEY_PATH):
        print(f"Error: SSH key not found at {SSH_KEY_PATH}")
        return

    # 2. Define Source Path (AI_Brain directory)
    # We deploy the entire AI_Brain folder + .env + setup_remote.sh
    source_dir = os.path.join(os.getcwd(), "AI_Brain")
    env_file = os.path.join(os.getcwd(), ".env")
    setup_script = os.path.join(os.getcwd(), "AI_Brain", "setup_remote.sh")

    if not os.path.exists(source_dir):
        print(f"Error: AI_Brain directory not found at {source_dir}")
        return

    # 3. Create Remote Directory via SSH first
    mkdir_cmd = [
        "ssh", "-i", SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        f"{REMOTE_USER}@{REMOTE_HOST_IP}",
        f"mkdir -p {REMOTE_DEST_DIR}"
    ]
    print(f"Creating remote directory: {' '.join(mkdir_cmd)}")
    run_command(mkdir_cmd)

    # 4. Deploy AI_Brain Directory
    print(f"Deploying AI_Brain Codebase...")
    scp_code_cmd = [
        "scp", "-i", SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-r",
        source_dir,
        f"{REMOTE_USER}@{REMOTE_HOST_IP}:{REMOTE_DEST_DIR}" # Results in /home/ubuntu/ai_brain/AI_Brain
    ]
    run_command(scp_code_cmd)

    # 5. Deploy .env (Securely)
    print(f"Deploying Environment Config (.env)...")
    scp_env_cmd = [
        "scp", "-i", SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        env_file,
        f"{REMOTE_USER}@{REMOTE_HOST_IP}:{REMOTE_DEST_DIR}/.env"
    ]
    run_command(scp_env_cmd)

    # 6. Deploy Setup Script
    print(f"Deploying Setup Script...")
    scp_setup_cmd = [
        "scp", "-i", SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        setup_script,
        f"{REMOTE_USER}@{REMOTE_HOST_IP}:{REMOTE_DEST_DIR}/setup_remote.sh"
    ]
    run_command(scp_setup_cmd)

    # 7. Make Setup Script Executable
    chmod_cmd = [
        "ssh", "-i", SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        f"{REMOTE_USER}@{REMOTE_HOST_IP}",
        f"chmod +x {REMOTE_DEST_DIR}/setup_remote.sh"
    ]
    run_command(chmod_cmd)

    print("Deployment Files Transferred.")
    print(f"To finish setup, run: ssh -i {SSH_KEY_PATH} {REMOTE_USER}@{REMOTE_HOST_IP} '{REMOTE_DEST_DIR}/setup_remote.sh'")

def provision_service(target_host, service_name):
    """
    Provisioning logic for the AI Brain ecosystem.
    """
    print(f"Provisioning service '{service_name}' to target: {target_host}")

    if target_host == "Remote_Oracle_Ubuntu":
        print("Target is Remote. Initiating automated pipeline...")
        generate_deployment_script(service_name)
    elif target_host == "Local_Snapdragon":
        print("Target is Local. Verifying local environment...")
        # Local setup verification
        service_path = os.path.join(os.getcwd(), "AI_Brain", service_name)
        if os.path.exists(service_path):
             print(f"Service found locally at {service_path}.")
        else:
             print(f"Service '{service_name}' not found locally. Please create it first.")
    else:
        print(f"Unknown target host: {target_host}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI Brain Provisioning Service")
    parser.add_argument("--target-host", choices=["Local_Snapdragon", "Remote_Oracle_Ubuntu"],
                        default="Local_Snapdragon", help="Target host for provisioning")
    parser.add_argument("--service", required=True, help="Name of the service/skill to provision (folder name)")

    args = parser.parse_args()

    provision_service(args.target_host, args.service)

if __name__ == "__main__":
    main()

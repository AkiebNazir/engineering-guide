import os
import logging
import paramiko
from paramiko.ssh_exception import SSHException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_sftp_file(host: str, port: int, user: str, pkey_path: str, remote_path: str, local_path: str):
    """
    Connects to an SFTP server using an SSH key and downloads a file.
    """
    logging.info(f"Connecting to SFTP server {host}:{port} as {user}...")
    
    try:
        # Setup SSH Client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key
        try:
            private_key = paramiko.RSAKey.from_private_key_file(pkey_path)
        except Exception as e:
            logging.error(f"Failed to load SSH private key: {e}")
            raise
            
        ssh.connect(hostname=host, port=port, username=user, pkey=private_key, timeout=10)
        logging.info("SSH connection established. Opening SFTP session...")
        
        sftp = ssh.open_sftp()
        logging.info(f"Downloading {remote_path} to {local_path}...")
        
        sftp.get(remote_path, local_path)
        logging.info("Download complete.")
        
        sftp.close()
        ssh.close()
    except SSHException as e:
        logging.error(f"SSH/SFTP error occurred: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise

def main():
    logging.info('Starting Data Engineering Project: 05_ftp_file_downloader (Paramiko SFTP)')
    host = os.getenv("SFTP_HOST", "sftp.example.com")
    port = int(os.getenv("SFTP_PORT", 22))
    user = os.getenv("SFTP_USER", "demo")
    pkey_path = os.getenv("SFTP_PKEY_PATH", "/path/to/private/key")
    remote_path = os.getenv("SFTP_REMOTE_PATH", "/incoming/data.csv")
    local_path = os.getenv("LOCAL_DOWNLOAD_PATH", "./data.csv")
    
    try:
        # In a real environment, you must provide a valid key path
        if not os.path.exists(pkey_path):
            logging.warning(f"Private key not found at {pkey_path}. Ensure it exists for actual execution.")
            
        download_sftp_file(host, port, user, pkey_path, remote_path, local_path)
    except Exception as e:
        logging.error("SFTP download pipeline failed.", exc_info=True)

if __name__ == '__main__':
    main()

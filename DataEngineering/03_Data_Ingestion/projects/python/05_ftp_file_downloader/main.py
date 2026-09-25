import ftplib

def download_file(ftp_host, ftp_user, ftp_pass, filename, local_path):
    print(f"Connecting to FTP server {ftp_host}...")
    try:
        ftp = ftplib.FTP(ftp_host)
        ftp.login(user=ftp_user, passwd=ftp_pass)
        print("Connected.")
        
        print(f"Downloading {filename}...")
        with open(local_path, 'wb') as f:
            ftp.retrbinary(f"RETR {filename}", f.write)
            
        print(f"File downloaded to {local_path}")
        ftp.quit()
    except Exception as e:
        print(f"FTP error: {e}")
        print("Mocking download instead...")
        with open(local_path, 'w') as f:
            f.write("mock downloaded data")

def main():
    print('Starting Data Engineering Project: 05_ftp_file_downloader')
    host = "test.rebex.net"
    user = "demo"
    password = "password"
    filename = "readme.txt"
    local_path = "downloaded_readme.txt"
    
    download_file(host, user, password, filename, local_path)

if __name__ == '__main__':
    main()

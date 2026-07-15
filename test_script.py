import subprocess 

def list_wifi_networks():
    cmd = "netsh wlan show networks"
    result = subprocess.check_output(cmd, shell=True, text=True)
    print(result)
list_wifi_networks
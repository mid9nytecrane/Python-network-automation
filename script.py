# from netmiko import ConnectHandler

# cisco_881 = {
#     'device_type': 'cisco_ios',
#     'host':   '10.10.10.10',
#     'username': 'test',
#     'password': 'password',
#     'port' : 8022,          # optional, defaults to 22
#     'secret': 'secret',     # optional, defaults to ''
# }

# net_connect = ConnectHandler(**cisco_881)
# output = net_connect.send_command('show ip int brief')
# print(output)
#!/usr/bin/env python3

# Import libraries
from netmiko import ConnectHandler
import getpass, yaml, time, logging

print("\n*** F5 Migration Script ***\n\nPlease enter credentials\n")

# Capture credentials
admin = getpass.getpass('Admin Username: ')
adminpword = getpass.getpass(prompt='\nAdmin Password: ')

# Load script variables via YAML
try:
	with open('F5.yaml', 'r') as vars:
		config_data = yaml.safe_load(vars)

except Exception as e:
		logging.info(f"Error importing YAML vars: {e}")

# Setup Netmiko constructs
def setup_connections(config_data, admin, adminpword):
	devices = config_data.get('devices',[])[0]
	devices = {
		'nc_legfw1': {'host': devices['legipfw1'], 'device_type': 'f5_ltm'},  
		'nc_legfw2': {'host': devices['legipfw2'], 'device_type': 'f5_ltm'},
		'nc_newfw1': {'host': devices['newipfw1'], 'device_type': 'f5_ltm'},
		'nc_newfw2': {'host': devices['newipfw2'], 'device_type': 'f5_ltm'},
		'nc_rtr1': {'host': devices['router1'], 'device_type': 'cisco_xe'},
		'nc_rtr2': {'host': devices['router2'], 'device_type': 'cisco_xe'},	
	}	
	connections = {}
	try:
		for name, device_info in devices.items():
			connections[name] = ConnectHandler(
			device_type=device_info['device_type'],
			host=device_info['host'],
			username=admin,
			password=adminpword
			)
	except Exception as e:
		logging.info(f"Error connecting to devices: {e}")

	time.sleep(0.5)
	return connections

# Delete Self-IPs on legacy infra
def delete_sip(connection, cmd_chgpart, cmd_delsip, cmd_chksip, sip_part, sip_name):
	try:
		# Send SIP delete commands
		connection.send_command(f"{cmd_chgpart};{cmd_delsip}", expect_string=sip_part)
		
		# Introduce pause to allow ConfigSync to operate
		time.sleep(0.3)
		
		# Check if SIP deleted correctly
		check = connection.send_command(f"{cmd_chksip}", expect_string=sip_part)
		if "not found" in check:
			logging.info(f"Self-IP {sip_name} deleted successfully on legacy FW!\n")
		else:
			raise Exception(f"Error deleting SIP - {sip_name}")
	
	except Exception as e:
		logging.info(f"Error deleting Self-IPs: {e}")

# Create Self-IPs on new infra
def create_sip(connection, cmd_chgpart, cmd_addsip, cmd_chksip, sip_part, sip_name):
	
	try:
		# Send SIP create commands
		connection.send_command(f"{cmd_chgpart};{cmd_addsip}", expect_string=sip_part)
		
		# Introduce pause to allow ConfigSync to operate
		time.sleep(0.3)
		
		# Check if SIP was created correctly
		check = connection.send_command(f"{cmd_chksip}", expect_string=sip_part)
		if (f"net self {sip_name}") in check:
			logging.info(f"Self-IP {sip_name} created successfully on new FW'!\n")
		else:
			raise Exception(f"Error creating SIP {sip_name}")

	except Exception as e:
		logging.info(f"Error creating Self-IPs: {e}")

# Delete pools on legacy infra
def delete_pool(connection, cmd_delpl, cmd_chkpl, pl_name):
	try:
		# Send pool delete commands
		connection.send_command(f"{cmd_delpl}", expect_string="LEGACY")
		
		# Introduce pause to allow ConfigSync to operate
		time.sleep(0.3)
		
		# Check if pool was deleted correctly
		check = connection.send_command(f"{cmd_chkpl}", expect_string="LEGACY")
		if "not found" in check:
			logging.info(f"Pool {pl_name} deleted successfully on legacy FW!\n")
		else:
			raise Exception(f"Error deleting vs - {vs_name}")
	
	except Exception as e:
		logging.info(f"Error deleting pools: {e}")

# Create virtual-servers on new infra
def create_vsvr(connection, cmd_addvs, cmd_chkvs, vs_name):
	try:
		# Send virtual-server create commands
		connection.send_command(f"{cmd_addvs}", expect_string="DEV")
		
		# Introduce pause to allow ConfigSync to operate
		time.sleep(0.3)
		
		# Check if virtual-server was created correctly	   
		check = connection.send_command(f"{cmd_chkvs}", expect_string="DEV")
		if (f"ltm virtual {vs_name}") in check:
			logging.info(f"Virtual-server {vs_name} created successfully on new FW!\n")
		else:
			raise Exception(f"Error creating vs - {vs_name}")
	
	except Exception as e:
		logging.info(f"Error creating virtual-server: {e}")

# Delete virtual-servers on legacyy infra
def delete_vsvr(connection, cmd_delvs, cmd_chkvs, vs_name):
	try:
		# Send virtual-server delete commands
		connection.send_command(f"{cmd_delvs}", expect_string="LEGACY")
		
		# Introduce pause to allow ConfigSync to operate
		time.sleep(0.3)
		
		# Check if virtual-server was deleted correctly	   
		check = connection.send_command(f"{cmd_chkvs}", expect_string="LEGACY")
		if "not found" in check:
			logging.info(f"Virtual-server {vs_name} deleted successfully from legacy FW!\n")
		else:
			raise Exception(f"Error deleting virtual-server: {vs_name}")
	
	except Exception as e:
		logging.info(f"Error deleting virtual-server: {e}")

# Function to process F5 Self-IPs
def process_sips(config_data, connections):
   
	# Load in SIPs from YAML and iterate through list of dictionaries
	self_ips = config_data.get('sips',[])
	for self_ip in self_ips:
		sip_name = self_ip['name']
		sip_address = self_ip['address']
		sip_part = self_ip['partition']
		sip_netmask = self_ip['netmask']
		sip_vlan = self_ip['vlan']
		sip_fw = self_ip['fw']
		sip_tg = self_ip['tg']
		
		#Declare function variables
		cmd_chgpart = f"cd /{sip_part}"
		cmd_delsip = f"delete net self {sip_name}"
		cmd_chksip = f"list net self {sip_name}"
		cmd_addsip = f"create net self {sip_name} address {sip_address}/{sip_netmask} vlan {sip_vlan} traffic-group {sip_tg}"
		
		#Evaluate SIP type and process using del/create SIP functions
		try:
			if "legfw" in sip_fw:
				if "legfw1" in sip_fw:
					delete_sip(connections['nc_legfw1'], cmd_chgpart, cmd_delsip, cmd_chksip, sip_part, sip_name)
				elif "legfw2" in sip_fw:
					delete_sip(connections['nc_legfw2'], cmd_chgpart, cmd_delsip, cmd_chksip, sip_part, sip_name)
				else:
					delete_sip(connections['nc_legfw2'], cmd_chgpart, cmd_delsip, cmd_chksip, sip_part, sip_name)
			else:
				if "newfw1" in sip_fw:
					create_sip(connections['nc_newfw1'], cmd_chgpart, cmd_addsip, cmd_chksip, sip_part, sip_name)
				elif "newfw2" in sip_fw:
					create_sip(connections['nc_newfw2'], cmd_chgpart, cmd_addsip, cmd_chksip, sip_part, sip_name)
				else:
					create_sip(connections['nc_newfw2'], cmd_chgpart, cmd_addsip, cmd_chksip, sip_part, sip_name)
		
		except Exception as e:
			logging.info(f"Error processing Self-IPs: {e}")		   

# Function to process LTM activities
def process_ltm(config_data, connections):

	# Use script flags to determine whether LTM work is required
	flags = config_data.get('flags',[])
	for flag in flags:
		pools = flag['pools']
		vsvr = flag['vsvr']

	# If VLAN has virtual-servers requiring deletion
	if 'ja' in vsvr:
		vsvrdata = config_data.get('vs',[])
		
		try:
			for vs in vsvrdata:
				# Del VS from legacy infra
				vs_name = vs['vsname']
				cmd_delvs = f"cd /P-LEGACY/;{vs['vsdel']}"
				cmd_chkvs = f"list ltm virtual {vs_name}"
				delete_vsvr(connections['nc_legfw2'], cmd_delvs, cmd_chkvs, vs_name)
				
				# Add VS to new infra
				cmd_addvs = f"cd /P-DEV/;{vs['vsadd']}"
				create_vsvr(connections['nc_newfw1'], cmd_addvs, cmd_chkvs, vs_name)
		
		except Exception as e:
			logging.info(f"Error processing virtual-servers: {e}")
			
	# If VLAN has pools requiring deletion
	if 'ja' in pools:
		pooldata = config_data.get('pools',[])
		
		try:
			# Iterate through pools and delete from legacy FWs
			for pool in pooldata:

				#Del pool
				pl_name = pool['poolname']
				cmd_delpl = f"cd /P-LEGACY/;{pool['pooldel']}"
				cmd_chkpl = f"list ltm pool {pl_name}"
				delete_pool(connections['nc_legfw2'], cmd_delpl, cmd_chkpl, pl_name)
		
		except Exception as e:
			logging.info(f"Error processing pools: {e}")

# Function to update front-end routing
def process_rtrs(config_data, connections):
	try:
		#Iterate through YAML vars and execute.
		statroutes = config_data.get('routes',[])

		for routes in statroutes:
			ips = routes['ips']
			mask = routes['mask']
			vrf = routes['vrf']
			nh = routes['nh']
			name = routes['name']

		sroute = (f"ip route vrf {vrf} {ips} {mask} {nh} name {name}")
		connections['nc_rtr1'].send_config_set(sroute)
		logging.info(f"Static route for {ips} / {mask} in vrf {vrf} created on DAYZ-RTR-001!\n")
		connections['nc_rtr2'].send_config_set(sroute)
		logging.info(f"Static route for {ips} / {mask} in vrf {vrf} created on DAYZ-RTR-002!\n")

	except Exception as e:
		logging.info(f"Error creating route: {e}")
			
# Main process function
def main():

	print("\nScript output: \n")
	
	# Setup logging
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d %b %y - %H:%M:%S')
	
	# Connect to devices via function
	logging.info("Device connections:\n")
	connections = setup_connections(config_data, admin, adminpword)
	logging.info("\n\nNetmiko connections established\n")
	
	# Start duration timer
	start_time = time.perf_counter()
	
	# Process LTM where required
	process_ltm(config_data, connections)
	
	# Process Self-IPs
	process_sips(config_data, connections)
	
	# Process routing
	process_rtrs(config_data, connections)
	
	#Process script duration
	end_time = time.perf_counter()
	timediff = end_time - start_time
	print(f"Time elapsed: {timediff:.2f} seconds.")

# Call main function
if __name__ == "__main__":
	main()
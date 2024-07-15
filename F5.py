#!/usr/bin/env python3

# Import libraries
from netmiko import ConnectHandler
import getpass, yaml, time, logging
import sys



ltm_self_banner = """
██╗  ████████╗███╗   ███╗              ███████╗███████╗██╗     ███████╗    ██╗██████╗ 
██║  ╚══██╔══╝████╗ ████║              ██╔════╝██╔════╝██║     ██╔════╝    ██║██╔══██╗
██║     ██║   ██╔████╔██║    █████╗    ███████╗█████╗  ██║     █████╗      ██║██████╔╝
██║     ██║   ██║╚██╔╝██║    ╚════╝    ╚════██║██╔══╝  ██║     ██╔══╝      ██║██╔═══╝ 
███████╗██║   ██║ ╚═╝ ██║              ███████║███████╗███████╗██║         ██║██║     
╚══════╝╚═╝   ╚═╝     ╚═╝              ╚══════╝╚══════╝╚══════╝╚═╝         ╚═╝╚═╝     
"""

ltm_pool_banner = """
██╗  ████████╗███╗   ███╗              ██████╗  ██████╗  ██████╗ ██╗     
██║  ╚══██╔══╝████╗ ████║              ██╔══██╗██╔═══██╗██╔═══██╗██║     
██║     ██║   ██╔████╔██║    █████╗    ██████╔╝██║   ██║██║   ██║██║     
██║     ██║   ██║╚██╔╝██║    ╚════╝    ██╔═══╝ ██║   ██║██║   ██║██║     
███████╗██║   ██║ ╚═╝ ██║              ██║     ╚██████╔╝╚██████╔╝███████╗
╚══════╝╚═╝   ╚═╝     ╚═╝              ╚═╝      ╚═════╝  ╚═════╝ ╚══════╝
"""

routing_banner = """
██████╗  ██████╗ ██╗   ██╗████████╗██╗███╗   ██╗ ██████╗  
██╔══██╗██╔═══██╗██║   ██║╚══██╔══╝██║████╗  ██║██╔════╝  
██████╔╝██║   ██║██║   ██║   ██║   ██║██╔██╗ ██║██║  ███╗  
██╔══██╗██║   ██║██║   ██║   ██║   ██║██║╚██╗██║██║   ██║ 
██║  ██║╚██████╔╝╚██████╔╝   ██║   ██║██║ ╚████║╚██████╔╝ 
╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝  
"""

device_banner = """
██████╗ ███████╗██╗   ██╗██╗ ██████╗███████╗     ██████╗ ██████╗ ███╗   ██╗███╗   ██╗███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔══██╗██╔════╝██║   ██║██║██╔════╝██╔════╝    ██╔════╝██╔═══██╗████╗  ██║████╗  ██║██╔════╝██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
██║  ██║█████╗  ██║   ██║██║██║     █████╗      ██║     ██║   ██║██╔██╗ ██║██╔██╗ ██║█████╗  ██║        ██║   ██║██║   ██║██╔██╗ ██║███████╗
██║  ██║██╔══╝  ╚██╗ ██╔╝██║██║     ██╔══╝      ██║     ██║   ██║██║╚██╗██║██║╚██╗██║██╔══╝  ██║        ██║   ██║██║   ██║██║╚██╗██║╚════██║
██████╔╝███████╗ ╚████╔╝ ██║╚██████╗███████╗    ╚██████╗╚██████╔╝██║ ╚████║██║ ╚████║███████╗╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║███████║
╚═════╝ ╚══════╝  ╚═══╝  ╚═╝ ╚═════╝╚══════╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
"""





admin = ""
adminpword = ""
config_data = ""

def initial_setup():
    global config_data
    global admin
    global adminpword
    
    print("\n*** F5 Migration Script ***\n\nPlease enter credentials\n")

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d %b %y - %H:%M:%S')
    
    
    #Capture credentials
    admin = getpass.getpass('Admin Username: ')
    adminpword = getpass.getpass(prompt='\nAdmin Password: ')

    try:
       # Load script variables via YAML
        with open('F5.yaml', 'r') as vars:
            config_data = yaml.safe_load(vars)
            return True
            
    except Exception as e:
            logging.info(f"Error importing YAML vars: {e}")
            return False

# Setup Netmiko constructs
def setup_connections(config_data, admin, adminpword):
    devices = config_data.get('devices',[])[0]
    

    devices = {
        'nc_legfw1': {'host': devices['legipfw1'], 'device_type': 'f5_tmsh'},  
        'nc_legfw2': {'host': devices['legipfw2'], 'device_type': 'f5_ltm'},
        'nc_newfw1': {'host': devices['newipfw1'], 'device_type': 'f5_ltm'},
        'nc_newfw2': {'host': devices['newipfw2'], 'device_type': 'f5_ltm'},
        'nc_rtr1': {'host': devices['router1'], 'device_type': 'cisco_xe'},
        'nc_rtr2': {'host': devices['router2'], 'device_type': 'cisco_xe'}, 
    }
    
    
    connections = {}

    try:
        for name, device_info in devices.items():
            print(f"Attempting connection to: {name} - {device_info['host']}\n")
            
			connections[name] = ConnectHandler(
			device_type=device_info['device_type'],
			host=device_info['host'],
			username=admin,
			password=adminpword
			)
                
                
    except Exception as e:
        logging.info(f"\n%%ERROR%% <------------\nError connecting to devices: {e} \n%%ERROR%% <------------")
        sys.exit(100)

    time.sleep(0.5)
    return connections

# Delete Self-IPs on legacy infra
def delete_sip(connection, cmd_chgpart, cmd_delsip, cmd_chksip, sip_part, sip_name):
    try:
        # Send SIP delete commands

        d_cmd = connection.send_command(f"{cmd_chgpart};{cmd_delsip}",r'\(/' + sip_part + r'\)')
        
        if "Syntax Error" in d_cmd:
            raise Exception(f"delete sip command unsuccesful - {d_cmd}!\n")
            sys.exit(202)
        
        # Introduce pause to allow ConfigSync to operate
        time.sleep(0.3)
        
        # Check if SIP deleted correctly
        check = connection.send_command(f"{cmd_chksip}", expect_string=r'\(/' + sip_part + r'\)')
        if "not found" in check:
            logging.info(f"Self-IP {sip_name} deleted successfully on legacy FW!\n")
        else:
            raise Exception(f"Error deleting SIP - {debug_txt}")
            sys.exit(201)
    
    except Exception as e:
        logging.info(f"Error deleting Self-IPs: {e}")
        sys.exit(200)
        
# Create Self-IPs on new infra
def create_sip(connection, cmd_chgpart, cmd_addsip, cmd_chksip, sip_part, sip_name):
    
    try:
        # Send SIP create commands
        c_cmd = connection.send_command(f"{cmd_chgpart};{cmd_addsip}", expect_string=sip_part)
        
        if "Syntax Error" in c_cmd:
            raise Exception(f"delete sip command unsuccesful - {c_cmd}!\n")
            sys.exit(302)
        
        # Introduce pause to allow ConfigSync to operate
        time.sleep(0.3)
        
        # Check if SIP was created correctly
        check = connection.send_command(f"{cmd_chksip}", expect_string=sip_part)
        if (f"net self {sip_name}") in check:
            logging.info(f"Self-IP {sip_name} created successfully on new FW'!\n")
        else:
            raise Exception(f"Error creating SIP {sip_name}")
            sys.exit(301)
    except Exception as e:
        logging.info(f"Error creating Self-IPs: {e}")
        sys.exit(300)
        
# Delete pools on legacy infra
def delete_pool(connection, cmd_delpl, cmd_chkpl, pl_name,pool_part):
    try:
        # Send pool delete commands
        d_cmd = connection.send_command(f"{cmd_delpl}", expect_string=r'\(/' + pool_part + r'\)')
        if "Syntax Error" in d_cmd:
            raise Exception(f"delete pool command unsuccesful - {d_cmd}!\n")
            sys.exit(402)
        
        # Introduce pause to allow ConfigSync to operate
        time.sleep(0.3)
        
        # Check if pool was deleted correctly
        check = connection.send_command(f"{cmd_chkpl}", expect_string=r'\(/' + pool_part + r'\)')
        if "not found" in check:
            logging.info(f"Pool {pl_name} deleted successfully on legacy FW!\n")
        else:
            raise Exception(f"Error deleting pool - {pl_name}")
            sys.exit(401)
            
    except Exception as e:
        logging.info(f"Error deleting pools: {e}")
        sys.exit(400)
        
# Create virtual-servers on new infra
def create_vsvr(connection, cmd_addvs, cmd_chkvs, vs_name,vs_part):

    try:
        # Send virtual-server create commands

        c_cmd = connection.send_command(f"{cmd_addvs}",expect_string=r'\(/' + vs_part,cmd_verify=False)
        
        if "Syntax Error" in c_cmd or "references" in c_cmd or "not found" in c_cmd:
            raise Exception(f"create pool command unsuccesful - {c_cmd}!\n")
            sys.exit(502)
        
        
        # Introduce pause to allow ConfigSync to operate
        time.sleep(0.3)

        # Check if virtual-server was created correctly    
        check = connection.send_command(f"{cmd_chkvs}", expect_string=r'\(/' + vs_part)

        if (f"ltm virtual {vs_name}") in check:
            logging.info(f"Virtual-server {vs_name} created successfully on new FW!\n")
        else:
            raise Exception(f"Error creating vs - {vs_name}")
            sys.exit(501)
    
    except Exception as e:
        logging.info(f"Error creating virtual-server: {e}")
        logging.info(check)
        sys.exit(500)

# Delete virtual-servers on legacyy infra
def delete_vsvr(connection, cmd_delvs, cmd_chkvs, vs_name,vs_part):
    try:
        # Send virtual-server delete commands
        d_cmd = connection.send_command(f"{cmd_delvs}", expect_string=r'\(/' + vs_part + r'\)')
        
       
        if "Syntax Error" in d_cmd:
            raise Exception(f"delete virtual server command unsuccesful - {d_cmd}!\n")
            sys.exit(602)
        
        # Introduce pause to allow ConfigSync to operate
        time.sleep(0.3)
        
        # Check if virtual-server was deleted correctly
        check = connection.send_command(f"{cmd_chkvs}", expect_string=r'\(/' + vs_part + r'\)')
        if "not found" in check:
            logging.info(f"Virtual-server {vs_name} deleted successfully from legacy FW!\n")
        else:
            raise Exception(f"Error deleting virtual-server: {vs_name}")
            sys.exit(601)
            
    except Exception as e:
        logging.info(f"Error deleting virtual-server: {e}")
        logging.info(check)
        sys.exit(600)
        
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
                    
            if "newfw" in sip_fw:
                if "newfw1" in sip_fw:
                    create_sip(connections['nc_newfw1'], cmd_chgpart, cmd_addsip, cmd_chksip, sip_part, sip_name)
                elif "newfw2" in sip_fw:
                    create_sip(connections['nc_newfw2'], cmd_chgpart, cmd_addsip, cmd_chksip, sip_part, sip_name)
                else:
                    create_sip(connections['nc_newfw2'], cmd_chgpart, cmd_addsip, cmd_chksip, sip_part, sip_name)
                    
            if "newfw" not in sip_fw and "legfw" not in sip_fw:
                raise Exception(f"fw variable in YAML file doesnt follow pattern: {sip_fw}")
                sys.exit(701)
                
        except Exception as e:
            logging.info(f"Error processing Self-IPs: {e}")
            sys.exit(700)

# Function to process LTM activities
def process_ltm(config_data, connections):

    # Use script flags to determine whether LTM work is required
    flags = config_data.get('flags',[])
    for flag in flags:
        pools = flag['pools']
        vsvr = flag['vsvr']

    # If VLAN has virtual-servers requiring deletion
    if 'ja' not in vsvr:
        logging.info(f"YAML File set to ignore virtual servers, skipping. <--------------------")
    
    if 'ja' in vsvr:
        vsvrdata = config_data.get('vs',[])
        
        try:
            for vs in vsvrdata:
                # Del VS from legacy infra
                vs_name = vs['vsname']
                vs_del_part = vs['vsdelpartition']
                vs_add_part = vs['vsaddpartition']
                cmd_delvs = f"cd /{vs_del_part}/;{vs['vsdel']}"
                cmd_chkvs = f"list ltm virtual {vs_name}"
                delete_vsvr(connections['nc_legfw2'], cmd_delvs, cmd_chkvs, vs_name,vs_del_part)
                time.sleep(0.3)
                # Add VS to new infra
                cmd_addvs = f"cd /{vs_add_part}/;{vs['vsadd']}"
                create_vsvr(connections['nc_newfw1'], cmd_addvs, cmd_chkvs, vs_name,vs_add_part)
        
        except Exception as e:
            logging.info(f"Error processing virtual-servers: {e}")
            sys.exit(800)
            
    # If VLAN has pools requiring deletion
    if 'ja' not in pools:
        logging.info(f"YAML File set to ignore pools, skipping. <-----------------")
    
    if 'ja' in pools:
        pooldata = config_data.get('pools',[])
        
        try:
            # Iterate through pools and delete from legacy FWs
            for pool in pooldata:

                #Del pool
                pl_name = pool['poolname']
                pool_part = pool['partition']
                cmd_delpl = f"cd /{pool_part}/;{pool['pooldel']}"
                cmd_chkpl = f"list ltm pool {pl_name}"
                
                delete_pool(connections['nc_legfw1'], cmd_delpl, cmd_chkpl, pl_name,pool_part)
        
        except Exception as e:
            logging.info(f"Error processing pools: {e}")
            sys.exit(900)
            
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
     

        
        
        route_add = connections['nc_rtr1'].send_config_set(sroute)
        logging.info(f" route add: {route_add}")
        logging.info(f"Static route for {ips} / {mask} in vrf {vrf} created on {name}!\n")
        
        
        
        
        
        route_add = connections['nc_rtr2'].send_config_set(sroute)
        logging.info(f" route add: {route_add}")
        logging.info(f"Static route for {ips} / {mask} in vrf {vrf} created on {name}!\n")

    except Exception as e:
        logging.info(f"Error creating route: {e}")
        sys.exit(1000)
            
# Main process function
def main():

    try:
        
        print("\nMain Script output: \n")
       
        
        # Connect to devices via function

        
        logging.info("\n" + device_banner + "\n")
        connections = setup_connections(config_data, admin, adminpword)
        logging.info("\n\nNetmiko connections established\n")
        descision = input("\ntype yes and press enter to continue: anything else and enter will exit\n:")
        descision = str(descision).lstrip().rstrip()
        

        if 'yes' != descision and 'YES' != descision and 'Yes' != descision:
            print("User exited script")
            return #early exit
            
        # Start duration timer
        start_time = time.perf_counter()
        
        
        # Process LTM where required
        logging.info("\n" + ltm_pool_banner + "\n")
        process_ltm(config_data, connections)
        
        # Process Self-IPs
        logging.info("\n" + ltm_self_banner + "\n")
        process_sips(config_data, connections)
        
        # Process routing
        logging.info("\n" + routing_banner + "\n")
        process_rtrs(config_data, connections)
        logging.info("\nRouting Changes Completed\n")
        
        
        #Process script duration
        end_time = time.perf_counter()
        timediff = end_time - start_time
        print(f"Time elapsed: {timediff:.2f} seconds.")

    except (Exception,SystemExit) as e:
            print(f"Script Exited with the above errors \nExit Code : {e}")
            return


# Call main function
if __name__ == "__main__":
    if initial_setup():
        main()
        print("Script Completed")
        #exit
    else:
        print("Error main script never started")
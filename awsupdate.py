
from fabric.api import *
import boto.ec2

def upload_file(host_string, user = "ubuntu", key_filename = "mykey.pem", bash_script = "newfile.sh"):
	# print hosts
	with settings(host_string=host_string, user=user, key_filename = key_filename):
		put(bash_script, bash_script)
		run("chmod +x "+bash_script)
		run("./"+bash_script)

def c2e():
	access, secret = get_key_and_secret()
	host_list = []
	for region in boto.ec2.regions():
		connection = boto.ec2.connect_to_region(region.name,
												aws_access_key_id=access,
												aws_secret_access_key=secret)
		conn_instances = connection.get_all_instances()
		if conn_instances:
			for i in conn_instances:
				ins = i.instances
				if ins:
					for j in ins:
						host_list.append(j.dns_name)
	return host_list

def get_key_and_secret():
	return [map(lambda s: s.strip(), line.split("="))[1] for line in open("rootkey.csv")]
	
if __name__ == "__main__":
	hosts = c2e()
	for h in hosts:
		upload_file(h)

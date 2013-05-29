# Log file data processing 
# 
__author__ = 'Hongwei Jin'
__copyright__ = "Copyright 2013, CRN @ NRECA"
__status__ = "developing"

import re
from datetime import datetime
import urllib

SYSTEM_LOG_FILENAME = 'system.log'
PROCESS_LOG_FILENAME = 'process.log'
STD_LOG_FILENAME = 'std.log'


# # TODO: unique user detect
def unique_user_detect():
    """ detect user's IP address
            return the list of user's IP
    """
    unique_visitors = []
    file_handler = open(STD_LOG_FILENAME, 'r')
    for line in file_handler:
        temp = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line, re.M | re.I)
        if temp != None:
            if temp.group() not in unique_visitors:
                unique_visitors.append(temp.group())  
    file_handler.close()
    return unique_visitors 
    

# # TODO: total hits weekly
def total_hits_count():
    """ calculate the total hits
            return the number of total hits
    """ 
    total_hits = 0  
    
    file_handler = open(STD_LOG_FILENAME, 'r')
    for line in file_handler:
        temp = re.search(r'GET.*200', line, re.M | re.I)
        if temp == None:
            continue
        else:
            total_hits += 1 
    file_handler.close()
    return total_hits

# # TODO:
def system_load_balance():
    """ get the system load balance, including average CPU percentage, virtual memory percentage, and swap percentage
            return three list: average CPU percentage, virtual memory percentage, and swap percentage
    """
    cpu_usage = []
    vir_mem_usage = []
    swap_mem_usage = []
    file_handler = open(SYSTEM_LOG_FILENAME, 'r')
    for line in file_handler:
        temp1 = re.search(r'CPU.+\[.+\]', line, re.M | re.I)
        if temp1 == None:
            continue
        else:
            temp = re.search(r'\[.+\]', temp1.group(), re.M | re.I)
            list = temp.group()[1:-1].split(', ')
            sum = 0
            for i in list:
                sum = sum + float(i)
            cpu_usage.append(sum / len(list)) 
    file_handler.close()  
    
    file_handler2 = open(SYSTEM_LOG_FILENAME, 'r')      
    for line2 in file_handler2:
        temp2 = re.search(r'RAM.+\[.+\]', line2, re.M | re.I)
        if temp2 == None:
            continue
        else:
            temp = re.search(r'\[.+\]', temp2.group(), re.M | re.I)
            list = temp.group()[1:-1].split(', ')
            vir_mem_usage.append(float(list[0]))
            swap_mem_usage.append(float(list[1]))
    file_handler2.close()        
    return cpu_usage, vir_mem_usage, swap_mem_usage;

# # TODO:
def get_log_time():
    """ get the system
    """
    time_stamps = []
    file_handler = open(SYSTEM_LOG_FILENAME, 'r')
    for line in file_handler:
        str = line.split(' - ')
        date_obj = datetime.strptime(str[0], '%Y-%m-%d %H:%M:%S,%f')
        time_stamps.append(str[0])
        file_handler.next()  # read every two line, skip the next line
        
    file_handler.close()
    return time_stamps

def get_geo_latlong():
    """ get the geography info of IP address
            return a list of tuples with latitude and longitude 
    """
    user_list = unique_user_detect()
    geo = []
    for i in user_list:
        ip_address = 'http://api.hostip.info/get_html.php?ip=' + str(i) + '&position=true'
        response = urllib.urlopen(ip_address).read()
        lati = re.search(r'Latitude:.+\n', response, re.M | re.I)
        longi = re.search(r'Longitude:.+\n', response, re.M | re.I)
        geo_lat = lati.group()[:-2].split(':')[1]
        geo_log = longi.group()[:-2].split(':')[1]
        geo.append((geo_lat, geo_log))
    return geo

if __name__ == '__main__':
    [c, vm, sm] = system_load_balance()
    print c, vm, sm
    
    print get_log_time()
    print total_hits_count()
    

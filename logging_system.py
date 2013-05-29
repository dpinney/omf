# logging_system.py: 
#    Main part of Logging System
# 
# 1. log some system info, such as critics, errors, warning, debugs, info.
# 2. log some user info, such as user id, user resources, which should include cpu usage, memory usage, disk usage, and time consuming etc.
# *3. email administrator the when some fatal info need to be noticed.

__author__ = "Hongwei Jin"
__copyright__ = "Copyright 2013, CRN @ NRECA"
__status__ = "Developing"
  

import logging.handlers
from flask import Flask, request
import datetime, time   
import os, sys
import psutil
import threading

SYSTEM_LOG_FILENAME = './logs/system.log'
PROCESS_LOG_FILENAME = './logs/process.log'
STD_LOG_FILENAME = './logs/std.log'
DELAY_TIME = 6       	# period of seconds to log process info
SYSTEM_DELAY_TIME = 60 	# period of seconds to log system info


class Process_usage:
    """ utility of process, such as peaks of real and virtual memory usage, and cpu times
    """
    memory_real = []
    memory_virtual = []
    peak = []
    cpu_times = []
    def __init__(self, pid):
        self.pid = pid
    
    def memory_record(self, real_usage, virtual_usage=0):
        self.memory_real.append(float(real_usage))
        self.memory_virtual.append(float(virtual_usage))
    
    def memory_percent_record(self, percent):
        self.peak.append(percent)
    
    def cpu_times_record(self, cpu_time):
        self.cpu_times.append(float(cpu_time))
        
    def clear(self):
        self.memory_real = []
        self.memory_virtual = []
        self.peak = []
        self.cpu_times = []
    
class background_thread(threading.Thread):
    def __init__(self, backFun, funArgs):
        threading.Thread.__init__(self)
        self.backFun = backFun
        self.funArgs = funArgs
         
    def run(self):
        self.backFun(*self.funArgs)


class logging_system:
#     app = None
    def __init__(self, app):
        self.app = app
		# flask logger
        app.logger.setLevel(logging.DEBUG)  # use the native logger of flask
    
    """ werkzeug logger
    """
    handler = logging.handlers.RotatingFileHandler(
        STD_LOG_FILENAME,
        'a',
        maxBytes=100 * 1024 * 1024,
        backupCount=20
        )
    
    formatter = logging.Formatter(\
        "%(asctime)s - %(levelname)s - %(name)s: \t%(message)s")
    handler.setFormatter(formatter)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    log.info(sys.stdout)
    log.error(sys.stderr)
    
    
    
    
    ####################################################################################
    # ## PART ONE: GENERAL LOGGING 
    # ## INCLUDING CRITICAL, ERROR, DEBUG, WARNING, INFO
    ####################################################################################
    
    """ Encapsulated logger method in python
    """
    # # TODO: 
    def logger_critical(self,critical_message,app):
        app.logger.critical(critical_message)
    
    # # TODO: 
    def logger_error(self,error_message,app):
        app.logger.error(error_message)
    
    # # TODO: 
    def logger_debug(self,debug_message,app):
        app.logger.debug(self,debug_message,app)
        
    # # TODO:
    def logger_info(self,info_message,app):
        app.logger.info(info_message)
    
    # # TODO: 
    def logger_warning(self,warning_message,app):
        app.logger.warning(warning_message)
    
    
    
    ####################################################################################
    # ## PART TWO: USER INFO LOGGING  
    # ## INCLUDING USER ID, USER RESOURCES, 
    # ##     WHICH SHOULD INCLUDE CPU USAGE, MEMORY USAGE, TIME CONSUMING, ETC. 
    ####################################################################################
    
   
    def logging_process_info(self,app):
        """ log process info to file
            it will record every DELAY_TIME seconds to file
        """   
        ## TODO:
        #  maybe it will need to get other PID for analysis part and MilSoft_to_GridLabD
        pro = psutil.Process(os.getpid())
        p = Process_usage(os.getpid())
        while True:
            if len(p.peak) < DELAY_TIME:
                
                p.memory_percent_record(pro.get_memory_percent())
                p.memory_record(pro.get_memory_info().__getattribute__('rss'), pro.get_memory_info().__getattribute__('vms'))
                p.cpu_times_record(pro.get_cpu_times().__getattribute__('user'))
                time.sleep(1)
                # print p.peak
            else:
                handler = logging.handlers.RotatingFileHandler(
                PROCESS_LOG_FILENAME,
                'a',
                maxBytes=100 * 1024 * 1024, # file will rotate every 100MB
                backupCount=20
                )
            
                formatter = logging.Formatter(\
                    "%(asctime)s - %(levelname)s - %(name)s: \t%(message)s")
                handler.setFormatter(formatter)
                app.logger.addHandler(handler)
                app.logger.info('Peak percent:' + str(max(p.peak)) + ' RSS: ' + str(max(p.memory_real)) + \
                                ' VMS: ' + str(max(p.memory_virtual)) + ' CPU_times: ' + str(max(p.cpu_times)))
                
                # For purpose of multi_handlers
                # Empty the list of memory info
                p.clear()
                app.logger.removeHandler(handler) 
        
    # # TODO:
    #     need to specify some format
    def logging_system_info(self,app):
        """ log system info to file
            it will record every SYSTEM_DELAY_TIME seconds to file
        """
        
        while True:
            handler = logging.handlers.RotatingFileHandler(
            SYSTEM_LOG_FILENAME,
            'a',
            maxBytes=100 * 1024 * 1024,
            backupCount=20
            )
        
            formatter = logging.Formatter(\
                "%(asctime)s - %(levelname)s - %(name)s: \t%(message)s")
            handler.setFormatter(formatter)
            app.logger.addHandler(handler)
            self.system_cpu_usage(app)
            self.system_memory_usage(app)
            app.logger.removeHandler(handler)
            
            time.sleep(SYSTEM_DELAY_TIME)
            # print 'Running here'
            
        
    
    
    def process_cpu_usage(self,current_process,app):
        """ get the process CPU running times, log into files
        """
        app.logger.info('CPU times: ' + current_process.get_cpu_times())
        # print 'Here is the CPU usage'
        
    # # TODO: 
    #     need to specify some format
    def system_cpu_usage(self,app):
        """ get the system CPU utilization percentage
        """
        app.logger.info('CPU percent: ' + str(psutil.cpu_percent(interval=0, percpu=True)))
        
        # print 'Here is the sys cpu percentage'
    
    # # TODO: 
    #     need to specify some format
    def process_memory_usage(self,current_process,app):
        """ get the process RAM utilization, 
            including peak utilization, real and virtual memory usage
        """
        app.logger.info('RAM: (percent) ' + str(current_process.get_memory_percent()) + ' ' + str(current_process.get_memory_info()))
        # print 'Here is the Memory usage' 
        
    # # TODO: 
    #     need to specify some format
    def system_memory_usage(self,app):
        """ get the system RAM utilization percentage
            including virtual RAM and swap RAM
        """
    #     print psutil.virtual_memory().__getattribute__('percent')
    
        app.logger.info('RAM (virtual), (swap): [' + str(psutil.virtual_memory().__getattribute__('percent')) +', '
                         + str(psutil.swap_memory().__getattribute__('percent')) + ']')  
        # # # print 'Here is the sys memory usage'
 
    def logging_run(self,app):
        thread_logging_process = background_thread(logging_system(app).logging_process_info, (app,))
        thread_logging_system = background_thread(logging_system(self.app).logging_system_info, (app,))
        thread_logging_process.start()
        thread_logging_system.start()
        
    
    ####################################################################################
    # ## PART THREE: ADMINISTRION MESSAGE NOTICE  
    # ## NOTICE ADMINISTRATOR WHEN SOME FATAL INFO NEED TO BE NOTICED.  
    ####################################################################################
    
    # # TODO:   
    # def email_notice():
    #     raise NotImplementedError
        # if error raised in system, send email to administrator

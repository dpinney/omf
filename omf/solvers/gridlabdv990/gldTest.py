import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
import traceback
import platform, re
import subprocess, random, webbrowser, multiprocessing
import pprint as pprint
import copy
import os.path


proc = subprocess.Popen(['./gridlabd', 'feeder.glm'], stdout=subprocess.PIPE, shell=True)
(out, err) = proc.communicate()
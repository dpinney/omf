'''
USAGE 1: python directConverter.py x.std y.seq
OUTPUT: z.glm
(Uses milToGridlab.py)

USAGE 2: python directConverter.py x.mdb
OUTPUT: y.glm
(Uses cymeToGridlab.py)

'''

from os.path import splitext
import sys, omf

def main():
	pass

if __name__ == '__main__':
  file_name, extension = splitext(sys.argv[1])
  if (extension == '.std' or extension == '.seq'):
    
  elif (extension == '.mdb'):
    pass
  else:
    raise Exception("FILE DOES NOT SUPPORT CONVERSION FOR EXTENSION: ", extension)

'''
USAGE 1: python directConverter.py x.std y.seq
OUTPUT: z.glm
(Uses milToGridlab.py)

USAGE 2: python directConverter.py x.mdb
OUTPUT: y.glm
(Uses cymeToGridlab.py)

'''

import os.path
import sys

def is_valid_file(parser, file_name):
  valid_names = ["mdb", "seq", "std"]

  # Check to see that file exists. 
  if not os.path.exists(file_name):
    parser.error("FILE %s DOES NOT EXIST." % file_name)
  suffix = os.path.splitext(file_name)[1][1:]

  # Check to ensure that no invalid name is being passed.
  if suffix not in valid_names:
    parser.error("FILE SUFFIX FOR %s INVALID." % file_name)

  print "VALID MATCH CONFIRMED FOR FILE %s." % file_name
  return file_name


def main():

  parser = argparse.ArgumentParser()
  parser.add_argument("--std", help="Single std file. Must go with seq file.", type=lambda f: is_valid_file(parser, f))
  parser.add_argument("--seq", help="Single seq file. Must go with std file.", type=lambda f: is_valid_file(parser, f))
  parser.add_argument("--mdb", help="Single mdb file, with both network and database exported to the same file.", type=lambda f: is_valid_file(parser, f))

  # parser.add_argument("-of", "output_file", action="store_true")  For later-store in new folder.
  
  args = parser.parse_args()

  if (args.std and args.seq):
    pass
  elif (args.mdb):
    pass
  else:
    # Raise exception.

if __name__ == "__main__"
  main()

'''
USAGE 1: python directConverter.py x.std y.seq
OUTPUT: z.glm
(Uses milToGridlab.py)

USAGE 2: python directConverter.py x.mdb
OUTPUT: y.glm
(Uses cymeToGridlab.py)

'''
from os.path import exists, splitext

import sys
import milToGridlab as mil

def handleMilFile(std, seq, failure = False):
  ''' Conversion routine for the std and seq files. '''
    # Attempt to open std and seq files and conver to glm.
  try:
    with open(std) as std_file, open(seq) as seq_file:
      glm, x_scale, y_scale = mil.covert(std_file.read(), seq_file.read())
  
  # Write to new glm file.
    with open(std.replace('.std', '.glm'), 'w') as output_file:
      output_file.write(feeder.sortedWrite(glm))
      print 'GLM FILE WRITTEN FOR %s AND %s' % std, seq
  except:
    failure = True
    print 'FAILED TO CONVERT STD AND SEQ FILES FOR %s AND %s' % std, seq
  return failure

def handleMdbFile(mdb, failure = False):
  ''' Convert mdb database to glm file. '''
  try:

  # Convert to string for conversion.
  
    if isinstance(mdb, list):
      mdb = ' '.join(mdb)
    glm, x_scale, y_scale = convertCymeModel(mdb)
    with open(mdb.replace('.mdb', '.glm'), 'w') as output_file:
      output_file.write(feeder.sortedWrite(glm))
  except: 
    failure = True
    print 'FAILED TO CONVERT MDB FILE FOR %s' % mdb
  return failure

def is_valid_file(parser, file_name):
  ''' Check validity of user input '''
  valid_names = ["mdb", "seq", "std"]

  # Check to see that file exists. 
  if not exists(file_name):
    parser.error("FILE %s DOES NOT EXIST." % file_name)
  suffix = splitext(file_name)[1][1:]

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

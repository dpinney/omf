import os

if __name__ == "__main__":

### GRIDLAB-D

### read in glm file.

  xlm_file = glm_input.replace('.glm', '.xml')
  os.system('gridlabd %s - %s' % (glm_input, output_file))

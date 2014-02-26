'''
Created on Feb 24, 2014

@author: afisher
'''
import warnings
import create_4
import create_13
import create_34
import create_37
import create_123

def create_feeder(node,load_factor,residential_penetration):
	if load_factor <= 0:
		raise RuntimeError("Invalid argument for load_factor. Must be greater than 0")
	if residential_penetration < 0:
		warnings.warn("residential_penetration < 0. Setting to 0.")
		residential_penetration = 0
	if residential_penetration > 1:
		warnings.warn("residential_penetration > 1. Setting to 1.")
		residential_penetration = 1
	if node == 4:
		print('Creating IEEE 4 node test feeder.')
		ieee_feeder = create_4.create(load_factor,residential_penetration)
	elif node == 13:
		print('Creating IEEE 13 node test feeder.')
		ieee_feeder = create_13.create(load_factor,residential_penetration)
	elif node == 34:
		print('Creating IEEE 34 node test feeder.')
		ieee_feeder = create_34.create(load_factor,residential_penetration)
	elif node == 37:
		print('Creating IEEE 37 node test feeder.')
		ieee_feeder = create_37.create(load_factor,residential_penetration)
	elif node == 123:
		print('Creating IEEE 123 node test feeder.')
		ieee_feeder = create_123.create(load_factor,residential_penetration)
	else:
		raise RuntimeError("Invalid argument for node. Valid arguments are 4, 13, 34, 37, 123")
	
	return ieee_feeder
def main():
	pass
if __name__ == '__main__':
	main
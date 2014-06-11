

def is_prime(n):
	"""Returns True or False depending on if n is prime"""
	for i in range(2, int(n**0.5)+1):
		if n/i == float(n)/i:
			return False
	return True

def getnthprime(n):
	"""Gets the nth prime number"""
	i = 1
	current = 2
	while True:
		if is_prime(current):
			if i == n:
				return current
			i+=1
		current+=1


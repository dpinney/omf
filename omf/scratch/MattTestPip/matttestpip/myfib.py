
from matttestpip import getprimes

print "The 10th prime is", getprimes.getnthprime(10)

def fib(n):
	"""Simple Fibonacci function"""
	if n == 1 or n == 2:
		return 1
	return fib(n-1)+fib(n-2)


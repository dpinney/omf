import subprocess, os

'''
Okay, what are we trying to do? Write some code that outputs a movie.

'''


def ffmpegMovie():
	# Turn a folder full of pngs into an mp4 using ffmpeg.
	try: os.remove('outVolts.mp4')
	except: pass
	subprocess.call('ffmpeg -framerate 10 -i images/volts%03d.png -s:v 1000x1000 -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p outVolts.mp4', shell=True)

def ffmpegStreamingMovie():
	# Same as ffmpegMovie() but create images 1 at a time to reduce filesystem usage.
	# Not currently working. Problem is with the ffmpeg options.
	from subprocess import Popen, PIPE
	import numpy as np, matplotlib.pyplot as plt
	fps, duration = 24, 100
	p = Popen('ffmpeg -y -f image2pipe -vcodec mjpeg -r 24 -vcodec mpeg4 -q:a 5 -r 24 outStream.avi', stdin=PIPE, shell=True)
	for i in range(fps * duration):
		# im = Image.new('RGB', (300, 300), (i, 1, 1))
		# Random lasers.
		fig1 = plt.figure(frameon=False)
		plt.clf()
		plt.axis('off')
		data = np.random.rand(2, 25)
		plt.plot(data, 'r-')
		plt.savefig(p.stdin, format='png')
		# im.save(p.stdin, 'JPEG')
	p.stdin.close()
	p.wait()

def matplotAnimationLibMovie():
	# Use matplotlib's animation library to directly output an mp4.
	import numpy as np
	import matplotlib
	matplotlib.use('TKAgg')
	from matplotlib import pyplot as plt
	from matplotlib import animation
	def update_line(num, data, line):
		line.set_data(data[...,:num])
		return line,
	fig1 = plt.figure()
	data = np.random.rand(2, 25)
	l, = plt.plot([], [], 'r-')
	plt.xlim(0, 1)
	plt.ylim(0, 1)
	plt.xlabel('x')
	plt.title('test')
	line_ani = animation.FuncAnimation(fig1, update_line, 25, fargs=(data, l),
		interval=50, blit=True)
	line_ani.save('outLines.mp4')
	fig2 = plt.figure()
	x = np.arange(-9, 10)
	y = np.arange(-9, 10).reshape(-1, 1)
	base = np.hypot(x, y)
	ims = []
	for add in np.arange(15):
		ims.append((plt.pcolor(x, y, base + add, norm=plt.Normalize(0, 30)),))
	im_ani = animation.ArtistAnimation(fig2, ims, interval=50, repeat_delay=3000,
		blit=True)
	im_ani.save('outSurface.mp4', metadata={'artist':'Guido'})

def myApproach(steps):
	# Create an mp4 from a bunch of matplotlib plots.
	# How's RAM usage? FINE!
	# On dpinney's macbook: 50 MB for 15 images, 325 MB for 8760 images.
	# Virtual memory usage? FINE!
	# On dpinney's macbook: 2.5 GB for both 15 and 8760 images.
	# Time taken? About 15 minutes for 8760.
	# Output size? 15 MB for 8760 images.
	import numpy as np
	import matplotlib
	matplotlib.use('TKAgg')
	from matplotlib import pyplot as plt
	from matplotlib import animation
	myFig = plt.figure()
	images = []
	for step in xrange(steps):
		x = np.random.randn(5)
		images.append(plt.plot(x))
	im_ani = animation.ArtistAnimation(myFig, images, interval=50, repeat_delay=3000, blit=True)
	# Note that Chrome must get h264 video.
	im_ani.save('outBest.mp4', codec='h264', metadata={'artist':'Guido'})

# matplotAnimationLibMovie()
# ffmpegMovie()
myApproach(15)
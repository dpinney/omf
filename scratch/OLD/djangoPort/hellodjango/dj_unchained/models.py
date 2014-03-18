from django.db import models

# Create your models here.

class Post(models.Model):
	title = models.CharField(max_length=200)
	text = models.TextField()
	author = models.CharField(max_length=200)

	def __unicode__(self):
		return self.title

class Comment(models.Model):
	post = models.ForeignKey(Post)
	text = models.TextField()
	author = models.CharField(max_length=200)

	

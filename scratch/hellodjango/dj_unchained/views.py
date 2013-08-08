# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.core.urlresolvers import reverse

from models import *
def root(request):
	fields = {"posts":Post.objects.order_by("-id")}
	return TemplateResponse(request, "root.html", fields)

def new_post(request):
	return TemplateResponse(request,
							"post.html",
							{"p":Post.objects.create(title=request.POST["title"],
												author=request.POST["author"],
												text=request.POST["text"])})

def comment(request):
	return TemplateResponse(request,
							"comment.html",
							{"c":Comment.objects.create(text=request.POST["text"],
						   author=request.POST["author"],
						   post=Post.objects.get(id=request.POST["post_id"]))})

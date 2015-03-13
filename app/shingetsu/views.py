from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from shingetsu.models import *

class ping(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		response = HttpResponse()
		response.write("PONG\n"+str(addr))
		s = Session()
		if not s.query(Node).filter(Node.host == addr).first():
			s.add(Node(host=addr))
			s.commit()
		s.close()
		return response

class node(View):
	pass

class join(View):
	pass

class bye(View):
	pass

class have(View):
	pass

class get(View):
	pass

class head(View):
	pass

class update(View):
	pass

class recent(View):
	pass

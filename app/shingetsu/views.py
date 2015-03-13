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
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		response = HttpResponse()
		s = Session()
		nodeAddr = s.query(Node.host).filter(Node.host != addr).value(Node.host)
		if nodeAddr is not None:
			response.write(str(nodeAddr))
		return response

class join(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		if kwargs['node']:
			addr = kwargs['node']
		response = HttpResponse()
		s = Session()
		thisNode = s.query(Node).filter(Node.host == addr).first()
		otherNode = s.query(Node).filter(Node.host != addr).first()
		linkedNodeCount = s.query(Node).filter(Node.linked == True).count()

		welcome = False
		if thisNode:
			welcome = True
			thisNode.linked = True
			s.commit()
		elif linkedNodeCount < 5:
			welcome = True
			s.add(Node(host=addr, linked=True))
			s.commit()

		if welcome:
			response.write('WELCOME')
			if otherNode:
				response.write('\n'+str(otherNode.host))
		return response


class bye(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		if kwargs['node']:
			addr = kwargs['node']
		response = HttpResponse()
		s = Session()
		thisNode = s.query(Node).filter(Node.host == addr).first()
		if thisNode:
			thisNode.linked = False
			s.commit()
			response.write('BYEBYE')
		return response

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

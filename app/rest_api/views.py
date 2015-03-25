from django.views.generic import View
from django.http import HttpResponse, JsonResponse
import json

class versions(View):
	def dispatch(self, request, *args, **kwargs):
		obj = {'version':[
				"0.1",
			]}
		return JsonResponse(obj)


from django.views.generic import View
from django.http import HttpResponse, JsonResponse

class versions(View):
	def dispatch(self, request, *args, **kwargs):
		obj = {'version':[
				"0.1",
			]}
		return JsonResponse(obj)


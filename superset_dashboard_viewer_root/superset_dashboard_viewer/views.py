
from django import views
from django.shortcuts import render

from .models import Tab


class TabsView(views.View):
    template_name = "tabs.html"

    def get(self, request, *args, **kwargs):

        tabs = Tab.objects.filter(visible=True).order_by("position")

        tabs = [tab.__dict__ for tab in tabs]

        for tab in tabs:
            for key in ["_state", "visible", "position"]:
                del tab[key]

        context = {
            "tabs": tabs
        }

        return render(request, self.template_name, context)


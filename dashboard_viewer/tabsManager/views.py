from django import views
from django.shortcuts import render
from rest_framework import views as rest_views
from rest_framework.response import Response
from shared.utils.markdown import ConstanceProxy

from .models import Button, Tab, TabGroup


def convert_button_to_dict(button):
    final_btn = {}
    for attr in ["title", "icon"]:
        final_btn[attr] = getattr(button, attr)

    if isinstance(button, Tab):
        final_btn["url"] = button.url

    return final_btn


def get_menu():
    """
    :return: Organized structure with single tabs, group tabs and its sub tabs. Follows the following strcture
    ```
    [
      {
        "title": "Button 1",
        "icon": "fa-icon",
        "url": "http://..."
      },
      (
        {
          "title": "Group Button 1",
          "icon": "fa-icon",
        },
        [
          {
            "title": "Within Group Button 1",
            "icon": "fa-icon",
            "url": "http://..."
          },
          {
            "title": "Within Group Button 2",
            "icon": "fa-icon",
            "url": "http://..."
          },
          #...
        )
      ],
      {
        "title": "Button 2",
        "icon": "fa-icon",
        "url": "http://..."
      },
      #...
    ]
    ```
    :rtype: list
    """
    # get all base visible buttons, ordered by their position and title fields
    buttons = list(Button.objects.filter(visible=True).order_by("position", "title").select_subclasses())

    # association between a TabGroup and its SubTabs (Tab with the group field not None)
    group_mappings = {}
    for i, btn in enumerate(buttons):
        if isinstance(btn, Tab):
            if btn.group is None:
                buttons[i] = convert_button_to_dict(btn)
            else:
                if btn.group in group_mappings:
                    # append the button to the already created sub tabs list
                    group_mappings[btn.group].append(convert_button_to_dict(btn))
                else:
                    # create the list of the sub tabs for the associated group
                    group_mappings[btn.group] = [convert_button_to_dict(btn)]

        elif isinstance(btn, TabGroup):
            # if the list of sub tabs for this groups wasn't created yet, then use a new one
            group_sub_buttons = group_mappings.get(btn, [])
            buttons[i] = (
                convert_button_to_dict(btn),
                group_sub_buttons  # note that this list is the same as the one on group_mappings
            )
            group_mappings[btn] = group_sub_buttons

    return [btn for btn in buttons if not isinstance(btn, Tab)]


class APITabsView(rest_views.APIView):
    def get(self, request):
        return Response(get_menu())


class LandingPageView(views.View):
    template_name = "landing_page.html"

    def get(self, request, *_, **__):
        context = {
            "constance_config": ConstanceProxy(),
            "tabs": get_menu(),
        }

        return render(request, self.template_name, context)


class TabsView(views.View):
    template_name = "tabs.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            "tabs": get_menu(),
            "constance_config": ConstanceProxy()
        })

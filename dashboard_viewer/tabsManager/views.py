from django import views
from django.conf import settings
from django.shortcuts import render
from rest_framework import views as rest_views
from rest_framework.response import Response

from .models import Button, Logo, Tab, TabGroup


def convert_button_to_dict(button):
    final_btn = {}
    for attr in ["title", "icon"]:
        final_btn[attr] = getattr(button, attr)

    if isinstance(button, Tab):
        final_btn["url"] = button.url

    return final_btn


def get_menu():
    # get all base visible buttons, ordered by their position and title fields
    buttons = (
        Button.objects.filter(visible=True)
        .order_by("position", "title")
        .select_subclasses()
    )

    groups = []
    for btn in buttons:
        if isinstance(btn, TabGroup):
            groups.append(btn)
    group_mappings = {group: [] for group in groups}  # tabs within a group
    single_tabs = [
        btn for btn in buttons if isinstance(btn, Tab)
    ]  # button without sub tabs

    # associate each tab to its group, if it has one
    for i in range(len(single_tabs))[::-1]:
        tab = single_tabs[i]
        if tab.group is not None:
            if tab.group in group_mappings:
                group_mappings[tab.group].insert(0, convert_button_to_dict(tab))
            del single_tabs[i]

    # merge and convert both single tabs and groups keeping their order
    final_menu = []
    groups_idx = single_tabs_idx = 0
    while groups_idx < len(groups) and single_tabs_idx < len(single_tabs):
        if groups[groups_idx].position == single_tabs[single_tabs_idx].position:
            if groups[groups_idx].title <= single_tabs[single_tabs_idx].title:
                final_menu.append(
                    (
                        convert_button_to_dict(groups[groups_idx]),
                        group_mappings[groups[groups_idx]],
                    )
                )
                groups_idx += 1
            else:
                final_menu.append(convert_button_to_dict(single_tabs[single_tabs_idx]))
                single_tabs_idx += 1
        elif groups[groups_idx].position < single_tabs[single_tabs_idx].position:
            final_menu.append(
                (
                    convert_button_to_dict(groups[groups_idx]),
                    group_mappings[groups[groups_idx]],
                )
            )
            groups_idx += 1
        else:
            final_menu.append(convert_button_to_dict(single_tabs[single_tabs_idx]))
            single_tabs_idx += 1

    if groups_idx < len(groups) and len(groups) > 0:
        for i in range(groups_idx, len(groups)):
            final_menu.append(
                (
                    convert_button_to_dict(groups[i]),
                    group_mappings[groups[i]],
                )
            )
    elif len(single_tabs) > 0:  # single_tabs_idx < len(single_tabs)
        for i in range(single_tabs_idx, len(single_tabs)):
            final_menu.append(convert_button_to_dict(single_tabs[i]))

    return final_menu


class APITabsView(rest_views.APIView):
    def get(self, request):
        return Response(get_menu())


class TabsView(views.View):
    template_name = "tabs.html"

    def get(self, request, *_, **__):
        logo_obj = Logo.load()
        logo = dict()
        if logo_obj:
            logo["image_container_css"] = logo_obj.image_container_css
            logo["image_css"] = logo_obj.image_css
            logo["image_on_hover_css"] = logo_obj.image_on_hover_css

            if logo_obj.image:
                logo["image_src"] = f"/{settings.MEDIA_URL}{logo_obj.image}"
            else:
                logo["image_src"] = logo_obj.url

        context = {
            "tabs": get_menu(),
            "logo": logo,
        }

        return render(request, self.template_name, context)

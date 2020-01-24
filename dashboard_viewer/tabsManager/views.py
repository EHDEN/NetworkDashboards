
from django import views
from django.shortcuts import render

from .models import Tab, TabGroup, Button


class TabsView(views.View):
    template_name = "tabs.html"

    def get(self, request, *args, **kwargs):

        # get all base visible buttons, ordered by their position and title fields
        buttons = Button.objects.filter(visible=True).order_by("position", "title").select_subclasses()

        groups = []
        for btn in buttons:
            if isinstance(btn, TabGroup):
                groups.append(btn)
        group_mappings = {group: [] for group in groups}  # tabs within a group
        single_tabs = [btn for btn in buttons if isinstance(btn, Tab)]  # button without sub tabs

        # associate each tab to its group, if it has one
        for i in range(len(single_tabs))[::-1]:
            tab = single_tabs[i]
            if tab.group is not None:
                group_mappings[tab.group].append(tab)
                del single_tabs[i]

        # merge and convert both single tabs and groups keeping their order
        final_menu = []
        groups_idx = single_tabs_idx = 0
        while groups_idx < len(groups) and single_tabs_idx < len(single_tabs):
            if groups[groups_idx].position == single_tabs[single_tabs_idx].position:
                if groups[groups_idx].title <= single_tabs[single_tabs_idx].title:
                    final_menu.append(groups[groups_idx])  # TODO convert to dict
                    groups_idx += 1
                else:
                    final_menu.append(single_tabs[single_tabs_idx])  # TODO convert to dict
                    single_tabs_idx += 1
            elif groups[groups_idx].position < single_tabs[single_tabs_idx].position:
                final_menu.append(groups[groups_idx])  # TODO convert to dict
                groups_idx += 1
            else:
                final_menu.append(single_tabs[single_tabs_idx])  # TODO convert to dict
                single_tabs_idx += 1

        if groups_idx < len(groups) and len(groups) > 0:
            for i in range(groups_idx, len(groups)):
                final_menu.append(groups[i])  # TODO convert to dict
        elif len(single_tabs) > 0:  # single_tabs_idx < len(single_tabs)
            final_menu.append(single_tabs[single_tabs_idx:])  # TODO convert to dict

        context = {
            "tabs": single_tabs,  # TODO final_menu
        }

        return render(request, self.template_name, context)

from django.test import TestCase

from .models import TabGroup, Tab, Button
from .views import get_menu


class GetMenuTestCase(TestCase):

    def tearDown(self):
        Button.objects.all().delete()
    
    def test_only_visible_should_appear(self):
        """
        Only the buttons selected to be visible must be returned.
        """
        Tab.objects.create(title="t1", icon="ic1", position=1, visible=True)
        Tab.objects.create(title="t2", icon="ic2", position=2, visible=False)
        Tab.objects.create(title="t3", icon="ic3", position=3, visible=True)
        Tab.objects.create(title="t4", icon="ic4", position=4, visible=False)
        Tab.objects.create(title="t5", icon="ic5", position=5, visible=True)
        Tab.objects.create(title="t6", icon="ic6", position=6, visible=False)
        Tab.objects.create(title="t7", icon="ic7", position=7, visible=False)

        result = get_menu()

        self.assertEqual(len(result), 3)

    def test_group_not_visible(self):
        """
        If a group button is not visible, then the entire group, the button itself
         and its sub button, must not be returned.
        """
        group1 = TabGroup.objects.create(title="t1", icon="ic1", position=0, visible=True)
        Tab.objects.create(title="t2", icon="ic2", position=0, visible=True, group=group1)
        Tab.objects.create(title="t3", icon="ic3", position=1, visible=True, group=group1)
        group2 = TabGroup.objects.create(title="t4", icon="ic4", position=1, visible=False)
        Tab.objects.create(title="t5", icon="ic5", position=0, visible=True, group=group2)
        Tab.objects.create(title="t6", icon="ic6", position=1, visible=True, group=group2)

        result = get_menu()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0]["title"], "t1")
        self.assertEqual(len(result[0][1]), 2)

    def test_global_tabs_sort(self):
        """
        The first layer buttons (buttons with no group and the main buttons of a
         group ) must be sorted by their position then by title
        """
        Tab.objects.create(title="t5", icon="ic5", position=-5, visible=True)
        Tab.objects.create(title="t3", icon="ic3", position=-2, visible=True)
        Tab.objects.create(title="t4", icon="ic4", position=-2, visible=True)
        Tab.objects.create(title="t2", icon="ic2", position=-2, visible=True)
        Tab.objects.create(title="t1", icon="ic1", position=0, visible=True)

        result = get_menu()

        self.assertEqual(len(result), 5)
        self.assertSequenceEqual([tab["title"] for tab in result], [f"t{n}" for n in "52341"])

    def test_tabs_sort_within_group(self):
        """
        The buttons within a group must also be sorted by the same criteria, but only
        considering the buttons within the same group.
        """

        Tab.objects.create(title="t1", icon="ic1", position=0, visible=True)
        group1 = TabGroup.objects.create(title="t2", icon="ic2", position=1, visible=True)
        Tab.objects.create(title="t7", icon="ic7", position=-5, visible=True, group=group1)
        Tab.objects.create(title="t5", icon="ic5", position=-1, visible=True, group=group1)
        Tab.objects.create(title="t6", icon="ic6", position=-1, visible=True, group=group1)
        Tab.objects.create(title="t4", icon="ic4", position=2, visible=True, group=group1)
        Tab.objects.create(title="t3", icon="ic3", position=2, visible=True)

        result = get_menu()

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["title"], "t1")
        self.assertEqual(result[2]["title"], "t3")

        self.assertEqual(result[1][0]["title"], "t2")
        self.assertSequenceEqual([tab["title"] for tab in result[1][1]], [f"t{n}" for n in "7564"])

    def test_only_clickables_have_url(self):
        """
        All the clickable buttons (buttons with no group and buttons within a group) must have a url associated field.
        """
        Tab.objects.create(title="t1", icon="ic1", position=0, visible=True, url="http://site1")
        group1 = TabGroup.objects.create(title="t2", icon="ic2", position=1, visible=True)
        Tab.objects.create(title="t4", icon="ic4", position=0, visible=True, group=group1, url="http://site4")
        Tab.objects.create(title="t3", icon="ic3", position=2, visible=True, url="http://site3")

        result = get_menu()

        self.assertIn("url", result[0])
        self.assertNotIn("url", result[1][0])
        self.assertIn("url", result[1][1][0])
        self.assertIn("url", result[2])

        self.assertEqual(result[0]["url"], "http://site1")
        self.assertEqual(result[1][1][0]["url"], "http://site4")
        self.assertEqual(result[2]["url"], "http://site3")

    def test_all_content(self):
        Tab.objects.create(title="t1", icon="ic1", position=-1, visible=True, url="http://site1")
        group1 = TabGroup.objects.create(title="t2", icon="ic2", position=0, visible=True)
        Tab.objects.create(title="t4", icon="ic4", position=0, visible=True, group=group1, url="http://site4")
        Tab.objects.create(title="t3", icon="ic3", position=2, visible=True, url="http://site3")

        result = get_menu()

        self.assertListEqual(result,
            [
                {
                    "title": "t1",
                    "icon": "ic1",
                    "url": "http://site1"
                },
                (
                    {
                        "title": "t2",
                        "icon": "ic2",
                    },
                    [
                        {
                            "title": "t4",
                            "icon": "ic4",
                            "url": "http://site4"
                        },
                    ]
                ),
                {
                    "title": "t3",
                    "icon": "ic3",
                    "url": "http://site3"
                },
            ]
        )

# Code Documentation


### Apps {-}

<h3>Materialized Queries Manager</h3>

admin changes

<h4>Models</h4>

managed model

<h3>Tabs Manager</h3>

Currently, this app is not being used and the URL mapping was delete.
To use it again uncomment the tabsManager [line](https://github.com/EHDEN/NetworkDashboards/blob/master/dashboard_viewer/dashboard_viewer/urls.py#L29) on the dashboard_viewer/dashboard_viewer/urls.py file.
Then you can access the tabs page through the `[BASE_RUL]/tabs/` URL.

<h4>Views</h4>

On this app, there is only one view.
It is a simple page with just a sidebar to choose which dashboard to displays on an iframe.
Besides the simplicity, all the animations around the sidebar buttons are handled by CSS with some JS that adds and removes classes to HTML elements, as events (hover and click) happen.
To facilitate the development process of CSS, [SCSS](https://sass-lang.com/) was used to build styling of the view.
It prevents duplication with the addition of variables and adds the possibility to express parent classes by nesting their declaration.

In cases where there are a lot of buttons on the sidebar, some buttons might get impossible to reach since they are out of the field of view.
To avoid this we make use of [SimpleBar](https://github.com/Grsmto/simplebar), which makes the sidebar scrollable, displaying a scroll bar on the right side of the sidebar whenever there are elements outside of the field of view.

<h4>API</h4>

There is one endpoint, `[BASE_URL]/api/`, where a JSON object of tabs and groups of tabs and their sub-tabs are returned.

<h4>Models</h4>

![](images/code-documentation/tabs-models.png)

<h3>Uploader</h3>

all possible error messages for uploads

<h4>Models</h4>

![](images/code-documentation/uploader-models.png)

### External Node Packages {-}

### Docker {-}

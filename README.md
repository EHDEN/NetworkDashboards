# Network Dashboards
The dashboards to represent the OMOP CDM databases in the EHDEN network

## Installation

Refer to the docker directory

## Demo

1. Reconfigure the database on Superset (`localhost:8088`) to upload csvs.
- Go to "Sources"-> "Databases" and edit the existing
database (Second icon on the left).
- Check the checkbox on "Expose in SQL Lab" and "Allow
Csv Upload ".

2. Upload the *CSV file* on the `demo/` folder:
- Go to "Sources" -> "Upload a CSV"
- Set the name of the table equal to the name of the file uploading without the extension
- Select the csv file
- Choose the database configured on the previous step

3. Upload the exported dashboard file
- Go to "Manage" -> "Import Dashboards"
- Select the `sources_by_age_dashboard_exported.json` file,
present on the `demo/` folder.
- Click "Upload"

4. Add a new tab to the dashboard viewer app.
- Go to the Django's admin app (`localhost:8000/admin`)
- On the `DASHBOARD_VIEWER` section and on `Tabs`
row, add a new Tab.
- Fill form's fields
```
Title:    Sources by Age
Icon:     birthday-cake
Url:      See the next point
Position: 1
Visible:  ✓
```
- To get the url field
    - Go back to superset (`localhost:8088`)
    - Go to "Dashboards"
    - Right click on the dashboard "Sources by age" and copy the link address
    - Go back to the dashboard viewer app
    - Paste de link and append to it `?standalone=true`
    - Save
    
5. Update the public permissions to see the dashboards
- In Superset go to "Security" -> "List Roles"
- Select the "Edit record" button from the public role.
- In the Permissions field, add the following categories:
    - can explore JSON on Superset
    - can dashboard on Superset
    - all datasource access on all_datasource_access
    - can csrf token on Superset
    - can list on CssTemplateAsyncModelView

6. Now you can go back to the root url (`localhost:8000`) to see the final result

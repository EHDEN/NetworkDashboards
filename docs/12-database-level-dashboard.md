---
output: html_document
---



## Database-Level Dashboard

<!-- Discuss the goal of this dashboard... TO DO -->

This dashboard is an exact copy of the [Network Dashboard](#PerDatabaseDashboard) dashboard but several legends and fields
displayed on the original are hidden either through CSS or by changing some chart settings.
On the following sections we will only present the things to change on the original charts.

### Label Colors  {-}

In order to obtain the colors blue and rose in the chart representing the gender distribution,
add the following JSON entry to the JSON object of the `JSON Metadata` field on the edit dashboard page:

```json
"label_colors": {
    "Male": "#3366FF",
    "Female": "#FF3399"
}
```

### CSS {-}

To hide the dashboard header insert the following css code to the `CSS` field on the edit page:

```css
/* hides the filter badges on right side of charts */
.dashboard-filter-indicators-container {
    display: none;
}
/* hides the acronym filter */
.grid-content > .dragdroppable.dragdroppable-row > .with-popover-menu {
    display: none;
}
/*
WARNING panel 1 id hardcoded
Hides the X Axis Label of the heatmap on the Data Domains tab
*/
#TABS-nlIU6H5mcT-pane-1 g.x.axis > g.tick text {
    display: none;
}
/*
WARNING panel 2 id hardcoded
Hides the X Axis Labels of the bar charts on the Data Provenance tab
*/
#TABS-nlIU6H5mcT-pane-2 g.nv-x.nv-axis.nvd3-svg > g.nvd3.nv-wrap.nv-axis > g > g.tick.zero > text {
    display: none;
}
```

With this every time you want to edit the dashboard layout you have to either comment the CSS inserted
or remove it so the "Edit Dashboard" button can show again.

### Data Source Filter - hidden {-}

\begin{figure}
\includegraphics[width=1\linewidth]{images/12-acronym_filter} \caption{Settings for creating the Data Source filter chart}(\#fig:dataSourceFilter)
\end{figure}

**For the filter to work the name of the fields to filter should match in all tables used on the charts of this dashboard.**

#### SQL query {-}

No SQL query, use the sql table `data_source` of the `achilles` database.

#### Chart settings {-}

- Data Tab
  - Datasource & Chart Type
    - Visualization Type: Filter Box
  - Time
    - Time range: No filter
  - Filters Configuration
    - Filters:
      - acronym
    - Date Filter: off
    - Instant Filtering: on

### Demographics Tab {-}

#### Number of Patients {-}

No changes

#### Gender Table {-}

No changes

#### Gender Pie {-}

No changes

#### Age at first observation - Table {-}

Remove the `name` field from the columns to display.
  
- Data Tab
  - Query
    - Columns: 0-10, 10-20, 20-30, 30-40, 40-50, 50-60, 60-70, 70-80, 80-90, 90+

#### Age at first observation - Bars {-}

Remove legend.

- Customize Tab
  - Chart Options
    - Legend: off

#### Year of Birth {-}

Remove legend.

- Customize Tab
  - Chart Options
    - Legend: off

### Data Domains Tab {-}

No changes

### Data Provenance Tab {-}

No changes

### Observation Period Tab {-}

#### Number of Patitents in Observation Period {-}

Remove legend.

- Customize Tab
  - Chart Options
    - Legend: off

#### Cumulative Observation Period {-}

Remove legend.

- Customize Tab
  - Chart Options
    - Legend: off

### Visit Tab {-}

#### Visit Type Graph {-}

Remove legend.

- Customize Tab
  - Chart Options
    - Legend: off

#### Visit Type Table {-}

Remove the `name` field from the columns to display.

- Data Tab
  - Query
    - Columns: visit_type, num_persons, percent_persons with label persons (%), records_per_person

### Concept Browser Tab {-}

#### Concept Browser Table {-}

Remove the `source_name` field from the columns to display.

- Data Tab
  - Query
    - Columns: concept_id, concept_name, domain_id, magnitude_persons, magnitude_occurrences

### Meta Data Tab {-}

#### Meta Data Table {-}

Remove the `name` field from the columns to display.

- Data Tab
  - Query
    - Columns: source_release_date, cdm_release_date, cdm_version, vocabulary_version

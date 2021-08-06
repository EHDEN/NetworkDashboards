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
 * WARNING panel 1 id hardcoded
 * Hides the X Axis Label of the heatmap on the Data Domains tab
 */
#TABS-nlIU6H5mcT-pane-1 g.x.axis > g.tick text {
    display: none;
}

/*
 * WARNING panel 2 id hardcoded
 * Hides the X Axis Labels of the bar charts on the Data Provenance tab
 */
#TABS-nlIU6H5mcT-pane-2 g.nv-x.nv-axis.nvd3-svg > g.nvd3.nv-wrap.nv-axis > g > g.tick.zero > text {
    display: none;
}
```

With this every time you want to edit the dashboard layout you have to either comment the CSS inserted
or remove it so the "Edit Dashboard" button can show again.

### Data Source Filter - hidden {-}

Dataset: `data_source` table of the `achilles` database.

**For the filter to work the name of the fields to filter should match in all tables used on the charts of this dashboard.**

![](images/12-database-level/01-acronym-filter.png)

### Demographics Tab {-}

#### Number of Patients {-}

No changes

#### Gender Table {-}

No changes

#### Gender Pie {-}

No changes

#### Age at first observation - Bars {-}

Remove legend.

- Customize Tab
  - Chart Options
    - Legend: off

#### Distribution of age at first observation period {-}

No changes

#### Year of Birth {-}

Remove legend.

- Customize Tab
  - Chart Options
    - Legend: off

### Data Domains Tab {-}

#### Average number of records per person {-}

No changes

#### Total number of records {-}

No changes

#### Data Density Plot {-}

Dataset: Materialized View [data_density](materialized-views-1.html#data_density)

![](images/12-database-level/03-data-domains/03-data-density.png)

#### Records per person {-}

Dataset: Materialized View [records_per_person](materialized-views-1.html#records_per_person)

![](images/12-database-level/03-data-domains/04-records-per-person.png)

#### Concepts per person {-}

Dataset: Materialized View [number_of_distinct_per_person](materialized-views-1.html#number_of_distinct_per_person)

![](images/12-database-level/03-data-domains/05-concepts-pperson.png)

### Data Provenance Tab {-}

#### Type Concepts {-}

Dataset: Materialized View [data_provenance](materialized-views-1.html#data_provenance)

![](images/12-database-level/04-type-concepts.png)

### Observation Period Tab {-}

#### Number of Patitents in Observation Period {-}

Remove legend.

- Customize Tab
  - Chart Options
    - Legend: off

#### Length of observation (days) of first observation period {-}

No changes

#### Cumulative Observation Period {-}

Remove legend.

- Customize Tab
  - Chart Options
    - Legend: off

#### Number of Observation Periods {-}

No changes

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

#### Visit Age Distribution {-}

Dataset: Materialized View [visit_age_distribution](materialized-views-1.html#visit_age_distribution)

![](images/12-database-level/05-visit-age-distribution.png)

### Concept Browser Tab {-}

#### Domain Filter {-}

No changes

#### Concept Browser {-}

Dataset: Materialized View [concept_browser_table2](materialized-views-1.html#concept_browser_table2)

![](images/12-database-level/06-concept-browser.png)

### Meta Data Tab {-}

#### Meta Data {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/12-database-level/07-metadata.png)

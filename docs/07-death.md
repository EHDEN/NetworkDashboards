---
output: html_document
---



## Death

<!-- Discuss the goal of this dashboard... TO DO -->

### CSS {-}

To hide the dashboard header insert the following css code to the `CSS` field on the edit page:

```css
.dashboard > div:not(.dashboard-content) {  /* dashboard header */
  display: none;
}
```

With this every time you want to edit the dashboard layout you have to either comment the CSS inserted
or remove it so the "Edit Dashboard" button can show again.

### Data Source Filter {-}

<div class="figure">
<img src="images/shared/data_source_filter.png" alt="Settings for creating the Data Source filter chart" width="100%" />
<p class="caption">(\#fig:dataSourceFilter)Settings for creating the Data Source filter chart</p>
</div>

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
      - name
    - Date Filter: off
    - Instant Filtering: on

### Number of Records {-}

<div class="figure">
<img src="images/07-death/02-number_of_records.png" alt="Settings for creating the Number of Records chart" width="100%" />
<p class="caption">(\#fig:numberOfRecords)Settings for creating the Number of Records chart</p>
</div>

#### SQL query {-}

```sql
SELECT source.name,
    count_value,
    source.acronym
FROM public.achilles_results AS achilles
INNER JOIN public.data_source AS source ON achilles.data_source_id=source.id
WHERE analysis_id = 501
```

#### Chart settings {-}

- Data Tab
  - Datasource & Chart Type
    - Visualization Type: Bar Chart
  - Time
    - Time range: No filter
  - Query
    - Metrics: MAX(count_value) with label Count
    - Series: name
- Customize Tab
  - Chart Options
    - Y Axis Label: Number of Patients
  - X Axis
    - X Axis Label: Databases
    - Reduce X ticks: on

### Death By Year per Thousand People {-}

<div class="figure">
<img src="images/07-death/03-deaths_by_year_per_thousand_people.png" alt="Settings for creating the Death by Year per Thousand People chart" width="100%" />
<p class="caption">(\#fig:deathByYearPerThousandPeople)Settings for creating the Death by Year per Thousand People chart</p>
</div>

#### SQL query {-}

```sql
SELECT source.name,
    source.acronym,
    EXTRACT(year FROM TO_DATE(stratum_1, 'YYYYMM')) AS Date,
    count_value
FROM public.achilles_results as achilles
INNER JOIN public.data_source as source ON achilles.data_source_id=source.id
WHERE analysis_id = 502
```

#### Chart settings {-}

- Data Tab
  - Datasource & Chart Type
    - Visualization Type: Bar Chart
  - Time
    - Time range: No filter
  - Query
    - Metrics: MAX(count_value) with label Count
    - Series: date
    - Breakdowns: name
- Customize Tab
  - Chart Options
    - Stacked Bars: on
    - Sort Bars: on
    - Y Axis Label:Number of Patients (in thousands)
  - X Axis
    - X Axis Label: Years
    - Reduce X ticks: on

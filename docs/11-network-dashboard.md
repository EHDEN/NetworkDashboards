---
output: html_document
---



# Dashboards

## Network Dashboard {#PerDatabaseDashboard}

<!-- Discuss the goal of this dashboard... TODO -->

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
.dashboard > div:not(.dashboard-content) {  /* dashboard header */
  display: none;
}
```

With this every time you want to edit the dashboard layout you have to either comment the CSS inserted
or remove it so the "Edit Dashboard" button can show again.

### Filters {-}

#### Country Filter {-}

Materialized View: [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/01-filters/01-country.png)

#### Database Type Filter {-}

Materialized View: [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/01-filters/02-database-type.png)

#### Data Source Filter {-}

Materialized View: [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/01-filters/03-datasource.png)

### Overview Tab {-}

#### Countries {-}

Materialized View: [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/01-countries.png)

#### Data Sources {-}

Materialized View: [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/02-datasource.png)

#### Datasource Types {-}

Materialized View: [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/03-datasource-type.png)

#### Patients {-}

Materialized View: [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/04-patients.png)

#### Patients {-}

Materialized View: [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/04-patients.png)

#### Patients by Country {-}

Materialized View: [meta_data_table](materialized-views-1.html#patients_per_country_and_database_type)

![](images/11-network-dashboard/02-overview/05-patients-by-country.png)

#### Database Types per Country {-}

Materialized View: [meta_data_table](materialized-views-1.html#patients_per_country_and_database_type)

![](images/11-network-dashboard/02-overview/06-database-types-by-country.png)

#### Meta Data {-}

Materialized View: [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/07-metadata.png)

### Demographics Tab {-}

#### Number of Patients {-}

Materialized View: [number_of_patients](materialized-views-1.html#number_of_patients)

![](images/11-network-dashboard/03-demographics/01-number-of-patients.png)

#### Gender Table {-}

Materialized View: [gender](materialized-views-1.html#gender)

![](images/11-network-dashboard/03-demographics/02-gender-table.png)

#### Gender Pie {-}

Materialized View: [gender](materialized-views-1.html#gender)

![](images/11-network-dashboard/03-demographics/03-gender-pie.png)

#### Age at first observation Table {-}

Materialized View: [age1observation_table](materialized-views-1.html#age1observation_table)

![](images/11-network-dashboard/03-demographics/04-age-at-first-observation-table.png)

#### Age at first observation Bar Chart {-}

Materialized View: [age1observation_bar_chart](materialized-views-1.html#age1observation_bar_chart)

![](images/11-network-dashboard/03-demographics/05-age-at-first-observation-bar-chart.png)

#### Distribution of age at first observation period {-}

Materialized View: [distribution_of_age_at_first_observation_period](materialized-views-1.html#distribution_of_age_at_first_observation_period)

![](images/11-network-dashboard/03-demographics/06-dist-age-at-fist-obs-period.png)

#### Year of Birth {-}

Materialized View: [year_of_birth](materialized-views-1.html#year_of_birth)

![](images/11-network-dashboard/03-demographics/07-year-of-birth.png)

### Data Domains Tab {-}

#### Average Number of Records per Person {-}

Same chart as the one used on the [Data Domains](#avgRecordsPerPerson) dashboard.

#### Total Number of Records {-}

##### SQL query {-}

```sql
SELECT
data_source.name,
data_source.acronym,
    CASE 
    WHEN analysis_id = 201 THEN 'Visit'
    WHEN analysis_id = 401 THEN 'Condition'
    WHEN analysis_id = 501 THEN 'Death'
    WHEN analysis_id = 601 THEN 'Procedure'
    WHEN analysis_id = 701 THEN 'Drug Exposure'
    WHEN analysis_id = 801 THEN 'Observation'
    WHEN analysis_id = 1801 THEN 'Measurement'
    WHEN analysis_id = 2101 THEN 'Device'
    WHEN analysis_id = 2201 THEN 'Note'
    END AS Data_Domain,
    SUM(count_value) AS "count"
FROM achilles_results
JOIN data_source ON achilles_results.data_source_id=data_source.id
GROUP BY name, acronym, analysis_id
HAVING analysis_id IN (201, 401, 501, 601, 701, 801, 1801, 2101, 2201)
```

##### Chart settings {-}

- Data Tab
  - Datasource & Chart Type
    - Visualization Type: Pie Chart
  - Time
    - Time range: No filter
  - Query
    - Metric: MAX(count)
    - Group by: data_domain
    - Row limit: None

### Data Provenance Tab {-}

Same six charts used on the [Provenance](#dataProvenanceCharts) dashboard.

### Observation Period Tab {-}

#### Number of Patitents in Observation Period {-}

Same chart used on the [Observation Period](#numInObservationPeriod) dashboard.

#### Cumulative Observation Period {-}

The cumulative observation time plot shows the percentage of patients that have more that X days of observation time.

##### SQL Query {-}

```sql
SELECT
  name,
  acronym,
  xLengthOfObservation,
  round(cumulative_sum / total, 5) as yPercentPersons
FROM (
  SELECT data_source_id, CAST(stratum_1 AS INTEGER) * 30 AS xLengthOfObservation, SUM(count_value) OVER (PARTITION BY data_source_id ORDER BY CAST(stratum_1 AS INTEGER) DESC) as cumulative_sum
  FROM achilles_results
  WHERE analysis_id = 108
) AS cumulative_sums
JOIN (
  SELECT data_source_id, count_value as total
  FROM achilles_results
  WHERE analysis_id = 1
) AS totals
ON cumulative_sums.data_source_id = totals.data_source_id
JOIN data_source ON cumulative_sums.data_source_id = data_source.id
ORDER BY name, xLengthOfObservation
```

##### Chart settings {-}

- Data Tab
  - Datasource & Chart Type
    - Visualization Type: Bar Chart
  - Time
    - Time range: No filter
  - Query
    - Metrics: SUM(ypercentpersons)
    - Series: xlengthofobservation
    - Breakdowns: name
    - Row limit: None
- Customize Tab
  - Chart Options
    - Sort Bars: on
    - Y Axis Fomat: ,.1% (12345.432 => 1,234,543.2%)
    - Y Axis Label: Number of Patients
  - X Axis
    - X Axis Label: Days
    - Reduce X ticks: on

### Visit Tab {-}

#### Visit Type Graph {-}

##### SQL Query {-}

```sql
SELECT
  data_source.name,
  data_source.acronym,
  concept.concept_name,
  achilles_results.count_value AS num_persons
FROM (SELECT * FROM achilles_results WHERE analysis_id = 200) AS achilles_results
JOIN data_source ON achilles_results.data_source_id = data_source.id
JOIN concept ON CAST(achilles_results.stratum_1 AS BIGINT) = concept.concept_id
```

##### Chart settings {-}

- Data Tab
  - Datasource & Chart Type
    - Visualization Type: Bar Chart
  - Time
    - Time range: No filter
  - Query
    - Metrics: SUM(num_persons)
    - Series: concept_name
    - Breakdowns: name
    - Row limit: None

#### Visit Type Table {-}

##### SQL Query {-}

```sql
SELECT
  name,
  acronym,
  concept.concept_name,
  ar1.count_value AS num_persons,
  round(100.0 * ar1.count_value / denom.count_value, 2) AS percent_persons,
  round(1.0 * ar2.count_value / ar1.count_value, 2) AS records_per_person
FROM (
  SELECT *
  FROM achilles_results WHERE analysis_id = 200) AS ar1
  JOIN (
    SELECT *
    FROM achilles_results WHERE analysis_id = 201) AS ar2
    ON ar1.stratum_1 = ar2.stratum_1 AND ar1.data_source_id = ar2.data_source_id
  JOIN (
    SELECT *
    FROM achilles_results WHERE analysis_id = 1) AS denom
    ON ar1.data_source_id = denom.data_source_id
  JOIN data_source ON data_source.id = ar1.data_source_id
  JOIN concept ON CAST(ar1.stratum_1 AS INTEGER) = concept_id
ORDER BY ar1.data_source_id, ar1.count_value DESC
```

##### Chart Settings {-}

- Data Tab
  - Datasource & Chart Type
    - Visualization Type: Table
  - Time
    - Time range: No filter
  - Query
    - Query Mode: Raw Records
    - Columns: name, visit_type, num_persons, percent_persons with label persons (%), records_per_person
    - Row limit: None
- Customize Tab
  - Options
    - Show Cell Bars: off

### Concept Browser Tab {-}

#### Concept Browser Table {-}

Same chart used on the [Concept Browser](#conceptBrowserTable) dashboard.

### Meta Data Tab {-}

#### Meta Data Table {-}

Same chart used on the [General](#metaDataTable) dashboard.

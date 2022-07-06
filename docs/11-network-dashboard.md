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

Whenever a user types some texts on superset's filters the avaiable options on it are filtered.
Whenever no option matches the text inserted a 'Create option "[inserted text]"'.
Since Superset filters do exact match, this option will for sure return no results.
Because of that, this option is being hidden with the following CSS:

```css
.css-0.Select__option {
  display: none;
}
```

With this every time you want to edit the dashboard layout you have to either comment the CSS inserted
or remove it so the "Edit Dashboard" button can show again.

### Filters {-}

#### Mappings {-}

This defines which charts specific filters will affect.
This can be edited by entering in edit mode, click the three dots near the "Save" and then go to "Set filter mappings".
To apply a mapping you have to select a set of filters on the left, choose on the right which charts it affects and finally hit save.
You have to do this procedure for the different sets of filters that have different mappings.

This is done mainly to not confuse the user.
Let's say you choose "Portugal" on the country filter and that databases from Portugal only have records of the Dug domain.
After this, if the user clicks on the domain filter dropdown, only the Drug domain option will appear.
With this, the user might get the idea that the system only has records of the Drug domain.
If all options appear on the domain filter, the charts will show "No results" and with this, the users should conclude that for the set of filters defined there is no data.

Global filters: note that it does not affect the other filters mentioned below.  
![](images/11-network-dashboard/01-filters/filter-mappings/global-filters.png)

Domain Filter  
![](images/11-network-dashboard/01-filters/filter-mappings/domain-filter.png)

Concept Filter: Note that it does not affect the Domain filter  
![](images/11-network-dashboard/01-filters/filter-mappings/domain-filter.png)

Number of patitents in observation period time range  
![](images/11-network-dashboard/01-filters/filter-mappings/number-of-patients-in-obs-period-time-range.png)

#### Country Filter {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/01-filters/01-country.png)

#### Database Type Filter {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/01-filters/02-database-type.png)

#### Data Source Filter {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/01-filters/03-datasource.png)

### Overview Tab {-}

#### Countries {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/01-countries.png)

#### Data Sources {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/02-datasource.png)

#### Datasource Types {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/03-datasource-type.png)

#### Patients {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/04-patients.png)

#### Patients {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/04-patients.png)

#### Patients by Country {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#patients_per_country_and_database_type)

![](images/11-network-dashboard/02-overview/05-patients-by-country.png)

#### Database Types per Country {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#patients_per_country_and_database_type)

![](images/11-network-dashboard/02-overview/06-database-types-by-country.png)

#### Meta Data {-}

Dataset: Materialized View [meta_data_table](materialized-views-1.html#meta_data_table)

![](images/11-network-dashboard/02-overview/07-metadata.png)

### Demographics Tab {-}

#### Number of Patients {-}

Dataset: Materialized View [number_of_patients](materialized-views-1.html#number_of_patients)

![](images/11-network-dashboard/03-demographics/01-number-of-patients.png)

#### Gender Table {-}

Dataset: Materialized View [gender](materialized-views-1.html#gender)

![](images/11-network-dashboard/03-demographics/02-gender-table.png)

#### Gender Pie {-}

Dataset: Materialized View [gender](materialized-views-1.html#gender)

![](images/11-network-dashboard/03-demographics/03-gender-pie.png)

#### Age at first observation Table {-}

Dataset: Materialized View [age1observation_table](materialized-views-1.html#age1observation_table)

![](images/11-network-dashboard/03-demographics/04-age-at-first-observation-table.png)

#### Age at first observation Bar Chart {-}

Dataset: Materialized View [age1observation_bar_chart](materialized-views-1.html#age1observation_bar_chart)

![](images/11-network-dashboard/03-demographics/05-age-at-first-observation-bar-chart.png)

#### Distribution of age at first observation period {-}

Dataset: Materialized View [distribution_of_age_at_first_observation_period](materialized-views-1.html#distribution_of_age_at_first_observation_period)

![](images/11-network-dashboard/03-demographics/06-dist-age-at-fist-obs-period.png)

#### Year of Birth {-}

Dataset: Materialized View [year_of_birth](materialized-views-1.html#year_of_birth)

![](images/11-network-dashboard/03-demographics/07-year-of-birth.png)

### Data Domains Tab {-}

#### Average number of records per person {-}

Dataset: Materialized View [avg_num_of_records_per_person](materialized-views-1.html#avg_num_of_records_per_person)

![](images/11-network-dashboard/04-data-domains/01-avg-num-recs-per-person.png)

#### Total number of records {-}

Dataset: Materialized View [data_domain_total_num_of_records](materialized-views-1.html#data_domain_total_num_of_records)

![](images/11-network-dashboard/04-data-domains/02-total-num-of-rec.png)

#### Number of distinct visit occurrence concepts per person {-}

Dataset: Materialized View [number_of_distinct_per_person](materialized-views-1.html#number_of_distinct_per_person)

![](images/11-network-dashboard/04-data-domains/03-num-distinct-visit-occurr-concepts-pperson.png)

#### Number of distinct condition occurrence concepts per person {-}

Dataset: Materialized View [number_of_distinct_per_person](materialized-views-1.html#number_of_distinct_per_person)

![](images/11-network-dashboard/04-data-domains/04-num-distinct-cond-occur-concepts-pperson.png)

#### Number of distinct procedure occurrence concepts per person {-}

Dataset: Materialized View [number_of_distinct_per_person](materialized-views-1.html#number_of_distinct_per_person)

![](images/11-network-dashboard/04-data-domains/05-num-distinct-proced-occur-concepts-pperson.png)

#### Number of distinct drug exposure concepts per person {-}

Dataset: Materialized View [number_of_distinct_per_person](materialized-views-1.html#number_of_distinct_per_person)

![](images/11-network-dashboard/04-data-domains/06-num-distinct-drug-occur-concepts-pperson.png)

#### Number of distinct observation occurrence concepts per person {-}

Dataset: Materialized View [number_of_distinct_per_person](materialized-views-1.html#number_of_distinct_per_person)

![](images/11-network-dashboard/04-data-domains/07-num-distinct-observ-occur-concepts-pperson.png)

#### Number of distinct mesurement occurrence concepts per person {-}

Dataset: Materialized View [number_of_distinct_per_person](materialized-views-1.html#number_of_distinct_per_person)

![](images/11-network-dashboard/04-data-domains/08-num-distinct-mesur-occur-concepts-pperson.png)

### Data Provenance Tab {-}

Dataset: Materialized View [data_provenance](materialized-views-1.html#data_provenance)

![](images/11-network-dashboard/05-visit-type-pivot.png)

### Observation Period Tab {-}

#### Number of Patitents in Observation Period {-}

Dataset: Materialized View [num_of_patients_in_observation_period](materialized-views-1.html#num_of_patients_in_observation_period)

![](images/11-network-dashboard/06-observation-period/01-num-patients-in-ober-period.png)

#### Cumulative Observation Period {-}

Dataset: Materialized View [cumulative_observation_time](materialized-views-1.html#cumulative_observation_time)

![](images/11-network-dashboard/06-observation-period/02-cumulative-oberv-time.png)

#### Number of Observation Periods {-}

Dataset: Materialized View [number_of_observation_periods](materialized-views-1.html#number_of_observation_periods)

![](images/11-network-dashboard/06-observation-period/03-num-observ-periods.png)

#### Length of observation (days) of first observation period {-}

Dataset: Materialized View [length_of_observation_of_first_observation_period](materialized-views-1.html#length_of_observation_of_first_observation_period)

![](images/11-network-dashboard/06-observation-period/04-len-observ-days-first-observ-period.png)

### Visit Tab {-}

#### Visit Type Graph {-}

Dataset: Materialized View [visit_type_bar_chart](materialized-views-1.html#visit_type_bar_chart)

![](images/11-network-dashboard/07-visit/01-visit-type-graph.png)

#### Visit Type {-}

Dataset: Materialized View [visit_type_table](materialized-views-1.html#visit_type_table)

![](images/11-network-dashboard/07-visit/02-visit-type.png)

### Concept Browser Tab {-}

#### Domain Filter {-}

Dataset: Materialized View [domain_filter](materialized-views-1.html#domain_filter)

![](images/11-network-dashboard/08-concept-browser/01-domain-filter.png)

#### Concept Browser {-}

Dataset: Materialized View [concept_browser_table3](materialized-views-1.html#concept_browser_table3)

![](images/11-network-dashboard/08-concept-browser/02-concept-browser.png)

#### Concept Network Coverage {-}

Dataset: Materialized View [concept_coverage2](materialized-views-1.html#concept_coverage2)

![](images/11-network-dashboard/08-concept-browser/03-concept-network-coverage.png)

### About Tab {-}

Markdown dashboard components

![](images/11-network-dashboard/09-about.png)

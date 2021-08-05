## Materialized views

### meta_data_table {-}
```sql
SELECT data_source.acronym,
   data_source.name,
   data_source.database_type,
   country.country,
   p.count_value AS number_of_patients,
   a.stratum_2 AS source_release_date,
   a.stratum_3 AS cdm_release_date,
   a.stratum_4 AS cdm_version,
   a.stratum_5 AS vocabulary_version,
   p.stratum_3 AS execution_date,
   p.stratum_2 AS package_version
  FROM (((achilles_results a
    JOIN data_source ON ((a.data_source_id = data_source.id)))
    JOIN country ON ((data_source.country_id = country.id)))
    JOIN ( SELECT achilles_results.count_value,
           achilles_results.data_source_id,
           achilles_results.stratum_2,
           achilles_results.stratum_3
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 0)) p ON ((p.data_source_id = data_source.id)))
 WHERE (a.analysis_id = 5000);
```

### patients_per_country_and_database_type {-}

```sql
SELECT country.country,
   source.database_type,
   achilles.count_value
  FROM ((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country country ON ((source.country_id = country.id)))
 WHERE (achilles.analysis_id = 1);
```

### number_of_patients {-}

```sql
SELECT achilles_results.count_value,
   data_source.name,
   data_source.acronym,
   data_source.database_type,
   country.country
  FROM ((achilles_results
    JOIN data_source ON ((achilles_results.data_source_id = data_source.id)))
    JOIN country ON ((data_source.country_id = country.id)))
 WHERE (achilles_results.analysis_id = 1);
```

### gender {-}

```sql
SELECT source.name,
   source.acronym,
   source.database_type,
   country.country,
   concept.concept_name AS gender,
   achilles.count_value
  FROM (((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((country.id = source.country_id)))
    JOIN concept ON ((achilles.stratum_1 = (concept.concept_id)::text)))
 WHERE (achilles.analysis_id = 2);
```

### age1observation_table {-}

```sql
SELECT source.name,
   source.acronym,
   source.database_type,
   country.country,
   sum(
       CASE
           WHEN ((achilles.stratum_2)::integer < 10) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "0-10",
   sum(
       CASE
           WHEN (((achilles.stratum_2)::integer >= 10) AND ((achilles.stratum_2)::integer < 20)) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "10-20",
   sum(
       CASE
           WHEN (((achilles.stratum_2)::integer >= 20) AND ((achilles.stratum_2)::integer < 30)) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "20-30",
   sum(
       CASE
           WHEN (((achilles.stratum_2)::integer >= 30) AND ((achilles.stratum_2)::integer < 40)) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "30-40",
   sum(
       CASE
           WHEN (((achilles.stratum_2)::integer >= 40) AND ((achilles.stratum_2)::integer < 50)) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "40-50",
   sum(
       CASE
           WHEN (((achilles.stratum_2)::integer >= 50) AND ((achilles.stratum_2)::integer < 60)) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "50-60",
   sum(
       CASE
           WHEN (((achilles.stratum_2)::integer >= 60) AND ((achilles.stratum_2)::integer < 70)) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "60-70",
   sum(
       CASE
           WHEN (((achilles.stratum_2)::integer >= 70) AND ((achilles.stratum_2)::integer < 80)) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "70-80",
   sum(
       CASE
           WHEN (((achilles.stratum_2)::integer >= 80) AND ((achilles.stratum_2)::integer < 90)) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "80-90",
   sum(
       CASE
           WHEN ((achilles.stratum_2)::integer >= 90) THEN achilles.count_value
           ELSE NULL::bigint
       END) AS "90+"
  FROM (((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((country.id = source.country_id)))
    JOIN concept ON ((achilles.stratum_1 = (concept.concept_id)::text)))
 WHERE (achilles.analysis_id = 102)
 GROUP BY source.name, source.acronym, source.database_type, country.country;
```

### age1observation_bar_chart {-}

```sql
SELECT source.name,
   (achilles.stratum_1)::integer AS age,
   achilles.count_value AS count,
   source.acronym,
   source.database_type,
   country.country
  FROM ((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((country.id = source.country_id)))
 WHERE (achilles.analysis_id = 101);
```

### distribution_of_age_at_first_observation_period {-}

```sql
SELECT source.name,
   source.acronym,
   country.country,
   achilles.count_value,
   achilles.p10_value AS p10,
   achilles.p25_value AS p25,
   achilles.median_value AS median,
   achilles.p75_value AS p75,
   achilles.p90_value AS p90,
   achilles.max_value,
   achilles.min_value
  FROM ((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((source.country_id = country.id)))
 WHERE (achilles.analysis_id = 103)
 ORDER BY source.name;
```

### year_of_birth {-}

```sql
SELECT source.name,
   source.acronym,
   source.database_type,
   country.country,
   achilles.stratum_1 AS "Birth_year",
   achilles.count_value AS count
  FROM ((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((country.id = source.country_id)))
 WHERE (achilles.analysis_id = 3);
```


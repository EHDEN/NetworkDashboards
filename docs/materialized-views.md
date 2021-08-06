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

### avg_num_of_records_per_person {-}

```sql
SELECT source.name,
   source.acronym,
   source.database_type,
   country.country,
       CASE
           WHEN (achilles.analysis_id = 201) THEN 'Visit'::text
           WHEN (achilles.analysis_id = 401) THEN 'Condition'::text
           WHEN (achilles.analysis_id = 501) THEN 'Death'::text
           WHEN (achilles.analysis_id = 601) THEN 'Procedure'::text
           WHEN (achilles.analysis_id = 701) THEN 'Drug Exposure'::text
           WHEN (achilles.analysis_id = 801) THEN 'Observation'::text
           WHEN (achilles.analysis_id = 1801) THEN 'Measurement'::text
           WHEN (achilles.analysis_id = 2101) THEN 'Device'::text
           WHEN (achilles.analysis_id = 2201) THEN 'Note'::text
           ELSE NULL::text
       END AS data_domain,
   (sum(achilles.count_value) / avg(counts.num_persons)) AS records_per_person
  FROM (((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((country.id = source.country_id)))
    JOIN ( SELECT achilles_results.data_source_id,
           achilles_results.count_value AS num_persons
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 1)) counts ON ((achilles.data_source_id = counts.data_source_id)))
 GROUP BY achilles.analysis_id, source.name, source.acronym, source.database_type, country.country
HAVING (achilles.analysis_id = ANY (ARRAY[(201)::bigint, (401)::bigint, (501)::bigint, (601)::bigint, (701)::bigint, (801)::bigint, (1801)::bigint, (2101)::bigint, (2201)::bigint]));
```

### data_domain_total_num_of_records {-}

```sql
SELECT data_source.name,
   data_source.acronym,
   data_source.database_type,
   country.country,
       CASE
           WHEN (achilles_results.analysis_id = 201) THEN 'Visit'::text
           WHEN (achilles_results.analysis_id = 401) THEN 'Condition'::text
           WHEN (achilles_results.analysis_id = 501) THEN 'Death'::text
           WHEN (achilles_results.analysis_id = 601) THEN 'Procedure'::text
           WHEN (achilles_results.analysis_id = 701) THEN 'Drug Exposure'::text
           WHEN (achilles_results.analysis_id = 801) THEN 'Observation'::text
           WHEN (achilles_results.analysis_id = 1801) THEN 'Measurement'::text
           WHEN (achilles_results.analysis_id = 2101) THEN 'Device'::text
           WHEN (achilles_results.analysis_id = 2201) THEN 'Note'::text
           ELSE NULL::text
       END AS data_domain,
   sum(achilles_results.count_value) AS count
  FROM ((achilles_results
    JOIN data_source ON ((achilles_results.data_source_id = data_source.id)))
    JOIN country ON ((country.id = data_source.country_id)))
 GROUP BY data_source.name, data_source.acronym, data_source.database_type, country.country, achilles_results.analysis_id
HAVING (achilles_results.analysis_id = ANY (ARRAY[(201)::bigint, (401)::bigint, (501)::bigint, (601)::bigint, (701)::bigint, (801)::bigint, (1801)::bigint, (2101)::bigint, (2201)::bigint]));
```

### number_of_distinct_per_person {-}

```sql
SELECT source.name,
   source.acronym,
   country.country,
   achilles.analysis_id,
       CASE
           WHEN (achilles.analysis_id = 203) THEN 'Visit'::text
           WHEN (achilles.analysis_id = 403) THEN 'Condition'::text
           WHEN (achilles.analysis_id = 603) THEN 'Procedure'::text
           WHEN (achilles.analysis_id = 703) THEN 'Drug Exposure'::text
           WHEN (achilles.analysis_id = 803) THEN 'Observation'::text
           WHEN (achilles.analysis_id = 1803) THEN 'Measurement'::text
           ELSE NULL::text
       END AS data_domain,
   achilles.count_value,
   achilles.min_value,
   achilles.p10_value AS p10,
   achilles.p25_value AS p25,
   achilles.median_value AS median,
   achilles.p75_value AS p75,
   achilles.p90_value AS p90,
   achilles.max_value
  FROM ((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((source.country_id = country.id)))
 WHERE (achilles.analysis_id = ANY (ARRAY[(203)::bigint, (403)::bigint, (603)::bigint, (703)::bigint, (803)::bigint, (183)::bigint]))
 ORDER BY source.name;
```

### data_provenance {-}

```sql
SELECT source.name,
   source.acronym,
   source.database_type,
   country.country,
       CASE
           WHEN (achilles.analysis_id = 405) THEN 'Condition'::text
           WHEN (achilles.analysis_id = 605) THEN 'Procedure'::text
           WHEN (achilles.analysis_id = 705) THEN 'Drug'::text
           WHEN (achilles.analysis_id = 805) THEN 'Observation'::text
           WHEN (achilles.analysis_id = 1805) THEN 'Measurement'::text
           WHEN (achilles.analysis_id = 2105) THEN 'Device'::text
           ELSE 'Other'::text
       END AS domain_name,
   c1.concept_name,
   sum(achilles.count_value) AS num_records
  FROM (((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((country.id = source.country_id)))
    JOIN concept c1 ON ((achilles.stratum_2 = (c1.concept_id)::text)))
 WHERE (achilles.analysis_id = ANY (ARRAY[(405)::bigint, (605)::bigint, (705)::bigint, (805)::bigint, (1805)::bigint, (2105)::bigint]))
 GROUP BY source.name, source.acronym, source.database_type, country.country, c1.concept_name,
       CASE
           WHEN (achilles.analysis_id = 405) THEN 'Condition'::text
           WHEN (achilles.analysis_id = 605) THEN 'Procedure'::text
           WHEN (achilles.analysis_id = 705) THEN 'Drug'::text
           WHEN (achilles.analysis_id = 805) THEN 'Observation'::text
           WHEN (achilles.analysis_id = 1805) THEN 'Measurement'::text
           WHEN (achilles.analysis_id = 2105) THEN 'Device'::text
           ELSE 'Other'::text
       END;
```

### num_of_patients_in_observation_period {-}

```sql
SELECT source.name,
   source.acronym,
   source.database_type,
   country.country,
   to_date(achilles.stratum_1, 'YYYYMM'::text) AS date,
   achilles.count_value AS "Nr_patients"
  FROM ((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((country.id = source.country_id)))
 WHERE (achilles.analysis_id = 110);
```

### cumulative_observation_time {-}

```sql
SELECT data_source.name,
   data_source.acronym,
   data_source.database_type,
   country.country,
   cumulative_sums.xlengthofobservation,
   round((cumulative_sums.cumulative_sum / (totals.total)::numeric), 5) AS ypercentpersons
  FROM (((( SELECT achilles_results.data_source_id,
           ((achilles_results.stratum_1)::integer * 30) AS xlengthofobservation,
           sum(achilles_results.count_value) OVER (PARTITION BY achilles_results.data_source_id ORDER BY (achilles_results.stratum_1)::integer DESC) AS cumulative_sum
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 108)) cumulative_sums
    JOIN ( SELECT achilles_results.data_source_id,
           achilles_results.count_value AS total
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 1)) totals ON ((cumulative_sums.data_source_id = totals.data_source_id)))
    JOIN data_source ON ((cumulative_sums.data_source_id = data_source.id)))
    JOIN country ON ((country.id = data_source.country_id)))
 ORDER BY data_source.name, cumulative_sums.xlengthofobservation;
```

### number_of_observation_periods {-}

```sql
SELECT ar.data_source_id AS id,
   ds.acronym,
   ds.name,
   country.country,
   ar.stratum_1,
   ar.count_value,
   pa.nrpatients AS patients,
   round((((100)::numeric * (ar.count_value)::numeric) / (pa.nrpatients)::numeric), 2) AS percentage
  FROM (((achilles_results ar
    JOIN data_source ds ON ((ds.id = ar.data_source_id)))
    JOIN country ON ((ds.country_id = country.id)))
    JOIN ( SELECT achilles_results.count_value AS nrpatients,
           achilles_results.data_source_id
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 0)) pa ON ((pa.data_source_id = ds.id)))
 WHERE (ar.analysis_id = 113);
```

### length_of_observation_of_first_observation_period {-}

```sql
SELECT source.name,
   source.acronym,
   country.country,
   achilles.count_value,
   achilles.min_value,
   achilles.p10_value AS p10,
   achilles.p25_value AS p25,
   achilles.median_value AS median,
   achilles.p75_value AS p75,
   achilles.p90_value AS p90,
   achilles.max_value
  FROM ((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN country ON ((source.country_id = country.id)))
 WHERE (achilles.analysis_id = 105)
 ORDER BY source.name;
```

### visit_type_bar_chart {-}

```sql
SELECT data_source.name,
   data_source.acronym,
   data_source.database_type,
   country.country,
   concept.concept_name,
   achilles_results.count_value AS num_persons
  FROM (((( SELECT achilles_results_1.id,
           achilles_results_1.analysis_id,
           achilles_results_1.stratum_1,
           achilles_results_1.stratum_2,
           achilles_results_1.stratum_3,
           achilles_results_1.stratum_4,
           achilles_results_1.stratum_5,
           achilles_results_1.count_value,
           achilles_results_1.data_source_id,
           achilles_results_1.avg_value,
           achilles_results_1.max_value,
           achilles_results_1.median_value,
           achilles_results_1.min_value,
           achilles_results_1.p10_value,
           achilles_results_1.p25_value,
           achilles_results_1.p75_value,
           achilles_results_1.p90_value,
           achilles_results_1.stdev_value
          FROM achilles_results achilles_results_1
         WHERE (achilles_results_1.analysis_id = 200)) achilles_results
    JOIN data_source ON ((achilles_results.data_source_id = data_source.id)))
    JOIN country ON ((country.id = data_source.country_id)))
    JOIN concept ON (((achilles_results.stratum_1)::integer = concept.concept_id)));
```

### visit_type_table {-}

```sql
SELECT data_source.name,
   data_source.acronym,
   data_source.database_type,
   country.country,
   concept.concept_name,
   ar1.count_value AS num_persons,
   round(((100.0 * (ar1.count_value)::numeric) / (denom.count_value)::numeric), 2) AS percent_persons,
   round(((1.0 * (ar2.count_value)::numeric) / (ar1.count_value)::numeric), 2) AS records_per_person
  FROM (((((( SELECT achilles_results.id,
           achilles_results.analysis_id,
           achilles_results.stratum_1,
           achilles_results.stratum_2,
           achilles_results.stratum_3,
           achilles_results.stratum_4,
           achilles_results.stratum_5,
           achilles_results.count_value,
           achilles_results.data_source_id,
           achilles_results.avg_value,
           achilles_results.max_value,
           achilles_results.median_value,
           achilles_results.min_value,
           achilles_results.p10_value,
           achilles_results.p25_value,
           achilles_results.p75_value,
           achilles_results.p90_value,
           achilles_results.stdev_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 200)) ar1
    JOIN ( SELECT achilles_results.id,
           achilles_results.analysis_id,
           achilles_results.stratum_1,
           achilles_results.stratum_2,
           achilles_results.stratum_3,
           achilles_results.stratum_4,
           achilles_results.stratum_5,
           achilles_results.count_value,
           achilles_results.data_source_id,
           achilles_results.avg_value,
           achilles_results.max_value,
           achilles_results.median_value,
           achilles_results.min_value,
           achilles_results.p10_value,
           achilles_results.p25_value,
           achilles_results.p75_value,
           achilles_results.p90_value,
           achilles_results.stdev_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 201)) ar2 ON (((ar1.stratum_1 = ar2.stratum_1) AND (ar1.data_source_id = ar2.data_source_id))))
    JOIN ( SELECT achilles_results.id,
           achilles_results.analysis_id,
           achilles_results.stratum_1,
           achilles_results.stratum_2,
           achilles_results.stratum_3,
           achilles_results.stratum_4,
           achilles_results.stratum_5,
           achilles_results.count_value,
           achilles_results.data_source_id,
           achilles_results.avg_value,
           achilles_results.max_value,
           achilles_results.median_value,
           achilles_results.min_value,
           achilles_results.p10_value,
           achilles_results.p25_value,
           achilles_results.p75_value,
           achilles_results.p90_value,
           achilles_results.stdev_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 1)) denom ON ((ar1.data_source_id = denom.data_source_id)))
    JOIN data_source ON ((data_source.id = ar1.data_source_id)))
    JOIN country ON ((country.id = data_source.country_id)))
    JOIN concept ON (((ar1.stratum_1)::integer = concept.concept_id)))
 ORDER BY ar1.data_source_id, ar1.count_value DESC;
```

### domain_filter {-}

```sql
SELECT concept.concept_name,
   concept.domain_id,
   source.name,
   source.acronym,
   source.database_type,
   country.country
  FROM (((achilles_results
    JOIN concept ON (((achilles_results.stratum_1)::bigint = concept.concept_id)))
    JOIN data_source source ON ((achilles_results.data_source_id = source.id)))
    JOIN country ON ((country.id = source.country_id)))
 WHERE (achilles_results.analysis_id = ANY (ARRAY[(201)::bigint, (401)::bigint, (601)::bigint, (701)::bigint, (801)::bigint, (901)::bigint, (1001)::bigint, (1801)::bigint, (200)::bigint, (400)::bigint, (600)::bigint, (700)::bigint, (800)::bigint, (1800)::bigint]));
```

### concept_browser_table3 {-}

```sql
SELECT source.name,
   source.acronym,
   source.database_type,
   country.country,
   (((('<a href="https://athena.ohdsi.org/search-terms/terms/'::text || ar1.concept_id) || '"target="_blank">'::text) || ar1.concept_id) || '</a>'::text) AS concept_id,
   concept.concept_name,
   concept.domain_id,
   (ar1.rc)::integer AS rc,
   (ar2.drc)::integer AS drc
  FROM ((((( SELECT achilles_results.data_source_id,
           achilles_results.analysis_id,
           achilles_results.stratum_1 AS concept_id,
           achilles_results.count_value AS rc
          FROM achilles_results
         WHERE (achilles_results.analysis_id = ANY (ARRAY[(401)::bigint, (601)::bigint, (701)::bigint, (801)::bigint, (1801)::bigint, (2101)::bigint]))) ar1
    JOIN ( SELECT ar.data_source_id,
           ar.analysis_id,
           ar.stratum_1 AS concept_id,
           ar.count_value AS drc
          FROM achilles_results ar
         WHERE (ar.analysis_id = ANY (ARRAY[(430)::bigint, (630)::bigint, (730)::bigint, (830)::bigint, (1830)::bigint, (2130)::bigint]))) ar2 ON (((ar1.concept_id = ar2.concept_id) AND (ar1.data_source_id = ar2.data_source_id))))
    JOIN data_source source ON ((ar1.data_source_id = source.id)))
    JOIN country ON ((source.country_id = country.id)))
    JOIN concept concept ON ((ar1.concept_id = (concept.concept_id)::text)))
 ORDER BY ((ar2.drc)::integer) DESC;
```

### concept_coverage2 {-}

```sql
SELECT source.name AS source_name,
   source.database_type,
   country.country,
   (((('<a href="https://athena.ohdsi.org/search-terms/terms/'::text || concept.concept_id) || '" target="_blank">'::text) || concept.concept_id) || '</a>'::text) AS concept_id,
   concept.concept_name,
   concept.domain_id,
   sum((ar1.rc)::integer) AS rc,
   sum((ar2.drc)::integer) AS drc
  FROM ((((( SELECT achilles_results.data_source_id,
           achilles_results.analysis_id,
           achilles_results.stratum_1 AS concept_id,
           achilles_results.count_value AS rc
          FROM achilles_results
         WHERE (achilles_results.analysis_id = ANY (ARRAY[(401)::bigint, (601)::bigint, (701)::bigint, (801)::bigint, (1801)::bigint, (2101)::bigint]))) ar1
    JOIN ( SELECT ar.data_source_id,
           ar.analysis_id,
           ar.stratum_1 AS concept_id,
           ar.count_value AS drc
          FROM achilles_results ar
         WHERE (ar.analysis_id = ANY (ARRAY[(430)::bigint, (630)::bigint, (730)::bigint, (830)::bigint, (1830)::bigint, (2130)::bigint]))) ar2 ON (((ar1.concept_id = ar2.concept_id) AND (ar1.data_source_id = ar2.data_source_id))))
    JOIN data_source source ON ((ar1.data_source_id = source.id)))
    JOIN country ON ((country.id = source.country_id)))
    JOIN concept concept ON ((ar1.concept_id = (concept.concept_id)::text)))
 GROUP BY source.name, source.database_type, country.country, concept.domain_id, concept.concept_id, concept.concept_name;
```

### data_density {-}

```sql
SELECT source.acronym,
   t1.table_name AS series_name,
   to_date(t1.stratum_1, 'YYYYMM'::text) AS x_calendar_month,
   t1.count_value AS y_record_count
  FROM (( SELECT achilles_results.data_source_id AS id,
           'Visit occurrence'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 220)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Condition occurrence'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 420)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Death'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 502)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Procedure occurrence'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 620)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Drug exposure'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 720)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Observation'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 820)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Drug era'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 920)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Device Exposure'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 2120)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Condition era'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 1020)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Observation period'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 111)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Measurement'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 1820)) t1
    JOIN data_source source ON ((source.id = t1.id)))
 ORDER BY t1.table_name, (
       CASE
           WHEN (t1.stratum_1 ~ '^\d+\.?\d+$'::text) THEN t1.stratum_1
           ELSE NULL::text
       END)::integer;
```

### records_per_person {-}

```sql
SELECT source.acronym,
   t1.table_name AS series_name,
   to_date(t1.stratum_1, 'YYYYMM'::text) AS x_calendar_month,
   round(((1.0 * (t1.count_value)::numeric) / (denom.count_value)::numeric), 5) AS y_record_count
  FROM ((( SELECT achilles_results.data_source_id AS id,
           'Visit occurrence'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 220)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Condition occurrence'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 420)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Death'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 502)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Procedure occurrence'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 620)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Drug exposure'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 720)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Observation'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 820)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Device exposure'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 2120)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Drug era'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 920)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Condition era'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 1020)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Observation period'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 111)
       UNION ALL
        SELECT achilles_results.data_source_id AS id,
           'Measurement'::text AS table_name,
           achilles_results.stratum_1,
           achilles_results.count_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 1820)) t1
    JOIN ( SELECT achilles_results.id,
           achilles_results.analysis_id,
           achilles_results.stratum_1,
           achilles_results.stratum_2,
           achilles_results.stratum_3,
           achilles_results.stratum_4,
           achilles_results.stratum_5,
           achilles_results.count_value,
           achilles_results.data_source_id,
           achilles_results.avg_value,
           achilles_results.max_value,
           achilles_results.median_value,
           achilles_results.min_value,
           achilles_results.p10_value,
           achilles_results.p25_value,
           achilles_results.p75_value,
           achilles_results.p90_value,
           achilles_results.stdev_value
          FROM achilles_results
         WHERE (achilles_results.analysis_id = 117)) denom ON (((t1.stratum_1 = denom.stratum_1) AND (t1.id = denom.data_source_id))))
    JOIN data_source source ON ((source.id = t1.id)))
 ORDER BY t1.table_name, (
       CASE
           WHEN (t1.stratum_1 ~ '^\d+\.?\d+$'::text) THEN t1.stratum_1
           ELSE NULL::text
       END)::integer;
```

### visit_age_distribution {-}

```sql
SELECT source.name,
   source.acronym,
   c1.concept_name,
   c2.concept_name AS gender,
   achilles.count_value,
   achilles.p10_value AS p10,
   achilles.p25_value AS p25,
   achilles.median_value AS median,
   achilles.p75_value AS p75,
   achilles.p90_value AS p90
  FROM (((achilles_results achilles
    JOIN data_source source ON ((achilles.data_source_id = source.id)))
    JOIN concept c1 ON ((achilles.stratum_1 = (c1.concept_id)::text)))
    JOIN concept c2 ON ((achilles.stratum_2 = (c2.concept_id)::text)))
 WHERE (achilles.analysis_id = 206)
 ORDER BY source.name, c1.concept_name, c2.concept_name;
```

### concept_browser_table2 {-}

```sql
SELECT
   source.acronym,
   (((('<a href="https://athena.ohdsi.org/search-terms/terms/'::text || ar1.concept_id) || '"target="_blank">'::text) || ar1.concept_id) || '</a>'::text) AS concept_id,
   concept.concept_name,
   concept.domain_id,
   (ar1.rc)::integer AS rc,
   (ar2.drc)::integer AS drc
  FROM (((( SELECT achilles_results.data_source_id,
           achilles_results.analysis_id,
           achilles_results.stratum_1 AS concept_id,
           achilles_results.count_value AS rc
          FROM achilles_results
         WHERE (achilles_results.analysis_id = ANY (ARRAY[(401)::bigint, (601)::bigint, (701)::bigint, (801)::bigint, (1801)::bigint, (2101)::bigint]))) ar1
    JOIN ( SELECT ar.data_source_id,
           ar.analysis_id,
           ar.stratum_1 AS concept_id,
           ar.count_value AS drc
          FROM achilles_results ar
         WHERE (ar.analysis_id = ANY (ARRAY[(430)::bigint, (630)::bigint, (730)::bigint, (830)::bigint, (1830)::bigint, (2130)::bigint]))) ar2 ON (((ar1.concept_id = ar2.concept_id) AND (ar1.data_source_id = ar2.data_source_id))))
    JOIN data_source source ON ((ar1.data_source_id = source.id)))
    JOIN concept concept ON ((ar1.concept_id = (concept.concept_id)::text)))
 ORDER BY ((ar2.drc)::integer) DESC;
```

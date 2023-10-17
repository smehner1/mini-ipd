-- count number of distinct AS Numbers per timestep
SELECT
    t AS timestep,
    count(DISTINCT prefix_asn) AS num_as
FROM
    -- max.parameter_study_max
    DB_TABLE
WHERE
    parameter_study_name == 'PARAMTERIZATION'
    AND parameter_study_type == 'STUDY'
    AND ip_version == 4
GROUP BY
    t
ORDER BY
    t;
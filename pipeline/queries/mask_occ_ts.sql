-- count number of distinct addresses per mask per date
SELECT
    t AS timestep,
    mask AS mask,
    count(DISTINCT netid_string) AS count
FROM
    -- max.parameter_study_max
    DB_TABLE
WHERE
    parameter_study_name == 'PARAMTERIZATION'
    AND parameter_study_type == 'STUDY'
    AND ip_version == 4
GROUP BY
    t,
    mask
ORDER BY
    t,
    mask;
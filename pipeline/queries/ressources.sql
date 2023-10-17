SELECT
    t AS timestep,
    ipd_ranges_count,
    ipd_cpu_runtime,
    iteration_cpu_runtime,
    ram_usage
FROM
    DB_TABLE
WHERE
    parameter_study_name == 'PARAMTERIZATION'
    AND parameter_study_type == 'STUDY'
    AND ip_version == 4
ORDER BY
    t;
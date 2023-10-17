SELECT
    t,
    SUM(num_ips_t) AS num_ips_top_as,
    round(SUM(num_ips_t)/intExp2(32), 8)*100 AS share
FROM (
    SELECT
        t,
        num_ips*mask_size AS num_ips_t,
        num_ips,
        mask,
        mask_size
    FROM (
        SELECT
            t,
            COUNT(DISTINCT ip) AS num_ips,
            mask,
            intExp2(32-mask) AS mask_size
        FROM (
            SELECT
                t,
                substring(netid_string, 8) AS ip,
                mask,
                prefix_asn AS asn
            FROM
                DB_TABLE
            WHERE
                parameter_study_name == 'PARAMTERIZATION'
                AND parameter_study_type == 'STUDY'
                AND ip_version == 4
        )
        WHERE
            asn IN ['15169', '2906', '20940', '6805', '32934', '16509', '202818', '46489', '65050', '22822', '65013', '15133', '6185', '24940', '54113', '20446', '60068', '16276', '13335', '5483', '32590']
        GROUP BY
            t, mask
        ORDER BY
            t
    )
)
GROUP BY
    t
ORDER BY
    t;
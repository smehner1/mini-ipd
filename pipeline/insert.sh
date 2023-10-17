
PARAMETRIZATION=$1

q=$2
c4=$3
c6=$4
cidr4=$5
cidr6=$6
t=$7
e=$8
decay=$9

ssh max@mittelerde "zcat /home/max/WORK/masterthesis/pipeline/data/ranges/range_${PARAMETRIZATION}.csv.gz" | clickhouse-client \
    --query "
        INSERT INTO max.mini_internet_parameter_study
            SELECT
                t,
                ip_version,
                confidence,
                ingress_router,
                counter_samples,
                counter_samples_needed,
                netid_string,
                mask,
                prefix_asn,
                '-',
                pni,
                ipd_ranges_count,
                ipd_cpu_runtime,
                iteration_cpu_runtime,
                ram_usage,
                ${q},
                ${c4},
                ${c6},
                ${cidr4},
                ${cidr6},
                ${t},
                ${e},
                '${decay}',
                '${PARAMETRIZATION}',
                'mini_internet'
            FROM input('
                t DateTime,
                ip_version UInt8,
                confidence Float32,
                ingress_router String,
                parameter_q Float32,
                parameter_c4 Float32,
                parameter_c6 Float32,
                parameter_cidr_max4 UInt16,
                parameter_cidr_max6 UInt16,
                parameter_t UInt16,
                parameter_e UInt16,
                parameter_decay String,
                parameter_study_name String,
                prefix_asn UInt8,
                netid_string String,
                mask UInt8,
                counter_samples UInt32,
                counter_samples_needed UInt32,
                pni UInt8,
                ipd_ranges_count UInt32,
                ipd_cpu_runtime Float32,
                iteration_cpu_runtime Float32,
                ram_usage UInt32
            ')
            FORMAT CSV"
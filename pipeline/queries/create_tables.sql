-- DROP TABLE IF EXISTS max.mini_internet_parameter_study;
CREATE TABLE IF NOT EXISTS max.mini_internet_parameter_study
(
    `t` DateTime,
    `ip_version` UInt8,
    `confidence` Float32,
    `ingress_router` String CODEC(LZ4),
    `counter_samples` UInt32,
    `counter_samples_needed` UInt32,
    `netid_string` String CODEC(LZ4),
    `mask` UInt8,
    `prefix_asn` String,
    `ingress_asn` String,
    `pni` UInt8,
    `ipd_ranges_count` UInt32,
    `ipd_cpu_runtime` Float32,
    `iteration_cpu_runtime` Float32,
    `ram_usage` UInt32,
    `parameter_q` Float32,
    `parameter_c4` Float32,
    `parameter_c6` Float32,
    `parameter_cidr_max4` UInt16,
    `parameter_cidr_max6` UInt16,
    `parameter_t` UInt16,
    `parameter_e` UInt16,
    `parameter_decay` String CODEC(LZ4),
    `parameter_study_name` String CODEC(LZ4),
    `parameter_study_type` String CODEC(LZ4)
)
ENGINE = MergeTree
ORDER BY (t, netid_string, ingress_router)
SETTINGS index_granularity = 8192;

-- DROP TABLE IF EXISTS max.range__subnet_mini_internet;
CREATE TABLE IF NOT EXISTS max.range__subnet_mini_internet
(
    `t` DateTime,
    `ip_version` UInt8,
    `confidence` Float32,
    `counter_samples` UInt32,
    `counter_samples_needed` UInt32,
    `netid_string` String,
    `mask` UInt8,
    `pni` UInt8,
    `ingress_router` String,
    `parameter_study_type` String,
    `parameter_study_name` String
)
ENGINE = MergeTree
ORDER BY (t, ingress_router)
SETTINGS index_granularity = 8192;

-- DROP TABLE IF EXISTS max.aggregate_netid_ingress__mv_bundles_mini_internet;
CREATE TABLE IF NOT EXISTS max.aggregate_netid_ingress__mv_bundles_mini_internet
(
    `pni` UInt8 CODEC(T64, LZ4),
    `netid_string` String CODEC(LZ4),
    `mask` UInt8 CODEC(T64, LZ4),
    `t` DateTime CODEC(Delta(4), LZ4),
    `ingress_router` LowCardinality(String) CODEC(LZ4),
    `confidence` Float32 CODEC(Gorilla, LZ4),
    `counter_samples` UInt32 CODEC(T64, LZ4),
    `counter_samples_needed` UInt32 CODEC(T64, LZ4),
    `length_seconds` UInt64 CODEC(T64, LZ4),
    `parameter_study_type` String CODEC(LZ4),
    `parameter_study_name` String CODEC(LZ4)
)
ENGINE = MergeTree
ORDER BY (t, netid_string, mask, ingress_router)
SETTINGS index_granularity = 8192;

-- DROP TABLE IF EXISTS max.netstability_mini_internet;
CREATE TABLE IF NOT EXISTS max.netstability_mini_internet
(
    `netid_string` String CODEC(LZ4),
    `t` DateTime CODEC(LZ4),
    `pni` UInt8 CODEC(T64, LZ4),
    `mask` UInt8 CODEC(T64, LZ4),
    `ingress_router` String CODEC(LZ4HC(0)),
    `ipd_events_num` Int64 CODEC(T64, LZ4),
    `ipd_events_lengths_seconds` Int64 CODEC(T64, LZ4),
    `ipd_events_confidence_avg` Float32 CODEC(Gorilla, LZ4),
    `ipd_events_confidence_std` Float32 CODEC(Gorilla, LZ4),
    `ipd_events_condifence_samples_avg` Float32 CODEC(Gorilla, LZ4),
    `ipd_events_confidence_samples_std` Float32 CODEC(Gorilla, LZ4),
    `ipd_events_confidence_samples_needed_avg` Float32 CODEC(Gorilla, LZ4),
    `ipd_events_confidence_samples_needed_std` Float32 CODEC(Gorilla, LZ4),
    `no_data_events_num` Int64 CODEC(T64, LZ4),
    `no_data_events_length_seconds` Int64 CODEC(T64, LZ4),
    `no_data_events_length_seconds_avg` Float32 CODEC(Gorilla, LZ4),
    `no_data_events_length_seconds_std` Float32 CODEC(Gorilla, LZ4),
    `no_data_events_length_seconds_max` Int64 CODEC(T64, LZ4),
    `end_of_sequence_len_seconds` Int64 CODEC(T64, LZ4),
    `network_stable_timed` Int64 CODEC(T64, LZ4),
    `parameter_study_type` String CODEC(LZ4),
    `parameter_study_name` String CODEC(LZ4)
)
ENGINE = MergeTree
PARTITION BY pni
ORDER BY (netid_string, t, parameter_study_name, parameter_study_type)
SETTINGS index_granularity = 8192;

-- DROP TABLE IF EXISTS max.netstability_2_mini_internet;
CREATE TABLE IF NOT EXISTS max.netstability_2_mini_internet
(
    `netid_string`  String CODEC(LZ4),
    `t`  DateTime CODEC(Delta(4), LZ4),
    `pni`  Int8 CODEC(T64, LZ4),
    `mask`  UInt8 CODEC(T64, LZ4),
    `ingress_router`  String CODEC(LZ4),
    `t__lengths`  UInt64 CODEC(T64, LZ4),
    `sequence_ipd_events_num`  UInt32 CODEC(T64, LZ4),
    `sequence_ipd_events_lengths_seconds__sum`  UInt32 CODEC(T64, LZ4),
    `sequence_ipd_events_confidence__avg`  Float32 CODEC(Gorilla, LZ4),
    `sequence_ipd_events_confidence__std`  Float32 CODEC(Gorilla, LZ4),
    `sequence_ipd_events_confidence_samples__avg`  Float32 CODEC(Gorilla, LZ4),
    `sequence_ipd_events_confidence_samples__std`  Float32 CODEC(Gorilla, LZ4),
    `sequence_ipd_events_confidence_samples_needed__avg`  Float32 CODEC(Gorilla, LZ4),
    `sequence_ipd_events_confidence_samples_needed__std`  Float32 CODEC(Gorilla, LZ4),
    `no_data_events_num` Int64 CODEC(T64, LZ4),
    `no_data_events_length_seconds` Int64 CODEC(T64, LZ4),
    `no_data_events_length_seconds_avg` Float32 CODEC(Gorilla, LZ4),
    `no_data_events_length_seconds_std` Float32 CODEC(Gorilla, LZ4),
    `no_data_events_length_seconds_max` Int64 CODEC(T64, LZ4),
    `end_of_sequence_len_seconds` Int64 CODEC(T64, LZ4),
    `network_stable_timed`  UInt64 CODEC(T64, LZ4),
    `parameter_study_type` String CODEC(LZ4),
    `parameter_study_name` String CODEC(LZ4)
)
ENGINE = MergeTree
PARTITION BY tuple(pni)
ORDER BY (t, netid_string, mask, ingress_router, parameter_study_name, parameter_study_type)
SETTINGS index_granularity = 8192;

-- DROP TABLE IF EXISTS max.metrics_mini_internet;
CREATE TABLE IF NOT EXISTS max.metrics_mini_internet
(
    `t` DateTime,

    `conv_as` Float64,
    `conv_ips` Float64,
    `granularity` Float64,
    `ipd_ranges_count` UInt32,
    `ipd_cpu_runtime` Float32,
    `iteration_cpu_runtime` Float32,
    `ram_usage` UInt32,

    `parameter_q` Float64,
    `parameter_c4` Float64,
    `parameter_c6` Float64,
    `parameter_cidr_max4` UInt16,
    `parameter_cidr_max6` UInt16,
    `parameter_t` UInt16,
    `parameter_e` UInt16,
    `parameter_decay` String CODEC(LZ4),

    `parameter_study_name` String CODEC(LZ4),
    `parameter_study_type` String CODEC(LZ4)
)
ENGINE = MergeTree
ORDER BY (t, parameter_study_name, parameter_study_type)
SETTINGS index_granularity = 8192;

-- DROP TABLE IF EXISTS max.metrics_mini_internet
CREATE TABLE IF NOT EXISTS max.metrics_stability_mini_internet
(
    `1200` Float64, `1500` Float64, `1800` Float64, `2100` Float64, `2400` Float64, `2700` Float64, `3000` Float64, `3300` Float64, `3600` Float64, `3900` Float64, `4200` Float64, `4500` Float64, `4800` Float64, `5100` Float64, `5400` Float64, `5700` Float64, `6000` Float64, `6300` Float64, `6600` Float64, `6900` Float64, `7200` Float64, `7500` Float64, `7800` Float64, `8100` Float64, `8400` Float64, `8700` Float64, `9000` Float64, `9300` Float64, `9600` Float64, `9900` Float64, `10200` Float64, `10500` Float64, `10800` Float64, `11100` Float64, `11400` Float64, `11700` Float64, `12000` Float64, `12300` Float64, `12600` Float64, `12900` Float64, `13200` Float64, `13500` Float64, `13800` Float64, `14100` Float64, `14400` Float64, `14700` Float64, `15000` Float64, `15300` Float64, `15600` Float64, `15900` Float64, `16200` Float64, `16500` Float64, `16800` Float64, `17100` Float64, `17400` Float64, `17700` Float64, `18000` Float64, `18300` Float64, `18600` Float64, `18900` Float64, `19200` Float64, `19500` Float64, `19800` Float64, `20100` Float64, `20400` Float64, `20700` Float64, `21000` Float64, `21300` Float64, `21600` Float64, `21900` Float64, `22200` Float64, `22500` Float64, `22800` Float64, `23100` Float64, `23400` Float64, `23700` Float64, `24000` Float64, `24300` Float64, `24600` Float64, `24900` Float64, `25200` Float64, `25500` Float64, `25800` Float64, `26100` Float64, `26400` Float64, `26700` Float64, `27000` Float64, `27300` Float64, `27600` Float64, `27900` Float64, `28200` Float64, `28500` Float64, `28800` Float64, `29100` Float64, `29400` Float64, `29700` Float64, `30000` Float64, `30300` Float64, `30600` Float64, `30900` Float64, `31200` Float64, `31500` Float64, `31800` Float64, `32100` Float64, `32400` Float64, `32700` Float64, `33000` Float64, `33300` Float64, `33600` Float64, `33900` Float64, `34200` Float64, `34500` Float64, `34800` Float64, `35100` Float64, `35400` Float64, `35700` Float64, `36000` Float64, `36300` Float64, `36600` Float64, `36900` Float64, `37200` Float64, `37500` Float64, `37800` Float64, `38100` Float64, `38400` Float64, `38700` Float64, `39000` Float64, `39300` Float64, `39600` Float64, `39900` Float64, `40200` Float64, `40500` Float64, `40800` Float64, `41100` Float64, `41400` Float64, `41700` Float64, `42000` Float64, `42300` Float64, `42600` Float64, `42900` Float64, `43200` Float64, `43500` Float64, `43800` Float64, `44100` Float64, `44400` Float64, `44700` Float64, `45000` Float64, `45300` Float64, `45600` Float64, `45900` Float64, `46200` Float64, `46500` Float64, `46800` Float64, `47100` Float64, `47400` Float64, `47700` Float64, `48000` Float64, `48300` Float64, `48600` Float64, `48900` Float64, `49200` Float64, `49500` Float64, `49800` Float64, `50100` Float64, `50400` Float64, `50700` Float64, `51000` Float64, `51300` Float64, `51600` Float64, `51900` Float64, `52200` Float64, `52500` Float64, `52800` Float64, `53100` Float64, `53400` Float64, `53700` Float64, `54000` Float64, `54300` Float64, `54600` Float64, `54900` Float64, `55200` Float64, `55500` Float64, `55800` Float64, `56100` Float64, `56400` Float64, `56700` Float64, `57000` Float64, `57300` Float64, `57600` Float64, `57900` Float64, `58200` Float64, `58500` Float64, `58800` Float64, `59100` Float64, `59400` Float64, `59700` Float64, `60000` Float64, `60300` Float64, `60600` Float64, `60900` Float64, `61200` Float64, `61500` Float64, `61800` Float64, `62100` Float64, `62400` Float64, `62700` Float64, `63000` Float64, `63300` Float64, `63600` Float64, `63900` Float64, `64200` Float64, `64500` Float64, `64800` Float64, `65100` Float64, `65400` Float64, `65700` Float64, `66000` Float64, `66300` Float64, `66600` Float64, `66900` Float64, `67200` Float64, `67500` Float64, `67800` Float64, `68100` Float64, `68400` Float64, `68700` Float64, `69000` Float64, `69300` Float64, `69600` Float64, `69900` Float64, `70200` Float64, `70500` Float64, `70800` Float64, `71100` Float64, `71400` Float64, `71700` Float64, `72000` Float64, `72300` Float64, `72600` Float64, `72900` Float64, `73200` Float64, `73500` Float64, `73800` Float64, `74100` Float64, `74400` Float64, `74700` Float64, `75000` Float64, `75300` Float64, `75600` Float64, `75900` Float64, `76200` Float64, `76500` Float64, `76800` Float64, `77100` Float64, `77400` Float64, `77700` Float64, `78000` Float64, `78300` Float64, `78600` Float64, `78900` Float64, `79200` Float64, `79500` Float64, `79800` Float64, `80100` Float64, `80400` Float64, `80700` Float64, `81000` Float64, `81300` Float64, `81600` Float64, `81900` Float64, `82200` Float64, `82500` Float64, `82800` Float64, `83100` Float64, `83400` Float64, `83700` Float64, `84000` Float64, `84300` Float64, `84600` Float64, `84900` Float64, `85200` Float64, `85500` Float64, `85800` Float64, `86100` Float64, `86400` Float64,

    `parameter_q` Float64,
    `parameter_c4` Float64,
    `parameter_c6` Float64,
    `parameter_cidr_max4` UInt16,
    `parameter_cidr_max6` UInt16,
    `parameter_t` UInt16,
    `parameter_e` UInt16,
    `parameter_decay` String CODEC(LZ4),
    `definition` String CODEC(LZ4),
    `parameter_study_name` String CODEC(LZ4),
    `parameter_study_type` String CODEC(LZ4)
)
ENGINE = MergeTree
ORDER BY (parameter_study_name, parameter_study_type)
SETTINGS index_granularity = 8192;

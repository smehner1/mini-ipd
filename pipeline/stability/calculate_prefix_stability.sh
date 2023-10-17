# !/bin/bash

PARAMETRIZATION=$1
STUDY_TYPE=$2

# echo $PARAMETRIZATION

SUCCESS=0

while [ $SUCCESS -ne 1 ]
do
    # 0) create needed tables if the do not exist yet &
    #    remove entries of paramterstudies with the same name from 3 used tables
    # echo ----- REMOVE ENTRIES FROM DBs OF THIS PARAMETRIZATION -----
    # echo
    # cat queries/create_tables.sql | clickhouse-client -mn

    python3 stability/clear_para_tables.py $PARAMETRIZATION $STUDY_TYPE

    # 2) Insert CSV File to Range Tabelle or get from parameter_study table
    # echo ----- INSERT DATA INTO RANGE TABLE -----
    # echo
    clickhouse-client \
        --query "
            INSERT INTO max.range__subnet_mini_internet
            SELECT
                t,
                ip_version,
                confidence,
                counter_samples,
                counter_samples_needed,
                netid_string,
                mask,
                pni,
                ingress_router,
                parameter_study_type,
                parameter_study_name
            FROM max.mini_internet_parameter_study
            WHERE parameter_study_name == '${PARAMETRIZATION}' and parameter_study_type == '${STUDY_TYPE}'
        "

    # 3) aggregate Content of aggregate Table
    # echo ----- AGGREGATE THE DATA FROM RANGE TABLE TO AGGREGATE TABLE -----
    # echo
    python3 stability/create_aggregate_ingress.py $PARAMETRIZATION $STUDY_TYPE

    # 4) calculate netstability
    # echo
    # echo ----- EVALUATE THE NETSTABILITY AND ADD TO TABLE -----
    # echo
    python3 stability/create_mv_netstab.py $PARAMETRIZATION $STUDY_TYPE
    SUCCESS=$?
    # echo $SUCCESS
    # echo
done

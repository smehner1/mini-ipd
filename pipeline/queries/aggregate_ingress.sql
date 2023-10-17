INSERT INTO TABLE max.aggregate_netid_ingress__mv_bundles_mini_internet
    select
    events_pni,
    netid_string,
    events_mask,
    events_t,
    events_ingress_router,

    confidence,
    counter_samples,
    counter_samples_needed,

    length_seconds,
    parameter_study_type,
    parameter_study_name
from (
    select
        netid_string,
        -- Create router hashes for calculating arrayDifferences
        arrayMap(x -> metroHash64(x), arr__ingress_router_with_nonevents_sorted) as arr__ingress_router_with_nonevents_sorted_hash,
        -- Get sequential router differences aka changes
        arrayPushFront(
            arrayPopFront(
                arrayDifference(arr__ingress_router_with_nonevents_sorted_hash)                    
            ),
            1
        ) as arr__ingress_router_with_nonevents_sorted_pushed_differences_fixed,
        -- We now can filter according to the found differences...
        arrayFilter((x, y) -> y <> 0, arr__t_with_nonevents_sorted,                      arr__ingress_router_with_nonevents_sorted_pushed_differences_fixed) as arr__events_t,
        arrayFilter((x, y) -> y <> 0, arr__ingress_router_with_nonevents_sorted,         arr__ingress_router_with_nonevents_sorted_pushed_differences_fixed) as arr__events_ingress_router,
        arrayFilter((x, y) -> y <> 0, arr__pni_with_nonevents_sorted,                    arr__ingress_router_with_nonevents_sorted_pushed_differences_fixed) as arr__events_pni,
        arrayFilter((x, y) -> y <> 0, arr__mask_with_nonevents_sorted,                   arr__ingress_router_with_nonevents_sorted_pushed_differences_fixed) as arr__events_mask,

        arrayFilter((x, y) -> y <> 0, arr__confidence_with_nonevents_sorted,             arr__ingress_router_with_nonevents_sorted_pushed_differences_fixed) as arr__events_confidence,
        arrayFilter((x, y) -> y <> 0, arr__counter_samples_with_nonevents_sorted,        arr__ingress_router_with_nonevents_sorted_pushed_differences_fixed) as arr__events_counter_samples,
        arrayFilter((x, y) -> y <> 0, arr__counter_samples_needed_with_nonevents_sorted, arr__ingress_router_with_nonevents_sorted_pushed_differences_fixed) as arr__events_counter_samples_needed,

        --finally, we would like to also store the length of each ipd state in the sequence.
        arrayPopFront(
            arrayDifference(
                arrayMap(
                    x -> toUnixTimestamp(x),
                    --add sentinal to end of observation.
                    arrayPushBack(
                        arr__events_t,
                        cast( --the select may technically be null. cast to NON-nullable.
                            (
                                select max(t)
                                from max.range__subnet_mini_internet
                                where parameter_study_name == 'REPLACEMENT2'
                            ) as DateTime
                        )
                    )
                )
            )
        ) as arr__state_time_period_length,
        parameter_study_type,
        parameter_study_name,
        1
    from (
        -- This subselect does the heavy lifting for each found netid.
        select
            netid_string,
            parameter_study_type,
            parameter_study_name,
            -- prepare array: sort by time + add sentinel element at end of observation
            date_add(minute, 5, arrayReduce('max', groupArray(t))),
            arrayPushBack(
                arraySort(groupArray(t)),
                arrayReduce('max', groupArray(t))
            ) as arr__t,
            -- smehner added splitByChar('(', ingress_router)[1]
            arrayPushBack(arraySort((x, y) -> y, groupArray(splitByChar('(', ingress_router)[1]),         groupArray(t)), 'NO_DATA') as arr__ingress_router,
            arrayPushBack(arraySort((x, y) -> y, groupArray(pni),                    groupArray(t)), -1)        as arr__pni,
            arrayPushBack(arraySort((x, y) -> y, groupArray(mask),                   groupArray(t)), 0)         as arr__mask,

            arrayPushBack(arraySort((x, y) -> y, groupArray(confidence),             groupArray(t)), 1)        as arr__confidence,
            arrayPushBack(arraySort((x, y) -> y, groupArray(counter_samples),        groupArray(t)), 0)        as arr__counter_samples,
            arrayPushBack(arraySort((x, y) -> y, groupArray(counter_samples_needed), groupArray(t)), 0)        as arr__counter_samples_needed,
        
            -- FIRST, we need to check for holes within the sequences to detect where netids fall out of ipd state
            arrayMap(
                x -> date_add(minute, 5, x),
                arrayFilter(
                    -- choose threshold for nonevent - we expect ipd intervals of 5min
                    (x, y) -> y > 7.5*60,
                    arr__t,
                    -- collect timestamp differences and circle shift array by one elemnent - we want the timestamp right before the change
                    arrayPushBack(
                        arrayPopFront(
                            arrayDifference(
                                arrayMap(
                                    x -> toUnixTimestamp(x),
                                    arr__t
                                )
                            )
                        ),
                        0
                    )
                )
            ) as arr__t_nonevents,
            -- append default data to arrays for each nonevents
            arrayConcat(arr__t,                      arr__t_nonevents)                                              as arr__t_with_nonevents, 
            arrayConcat(arr__ingress_router,         arrayResize(['NO_DATA'], length(arr__t_nonevents), 'NO_DATA')) as arr__ingress_router_with_nonevents,
            arrayConcat(arr__pni,                    arrayResize([-1],        length(arr__t_nonevents), -1))        as arr__pni_with_nonevents,
            arrayConcat(arr__mask,                   arrayResize([0],         length(arr__t_nonevents),  0))        as arr__mask_with_nonevents,

            arrayConcat(arr__confidence,             arrayResize([1],         length(arr__t_nonevents),  1))        as arr__confidence_with_nonevents,
            arrayConcat(arr__counter_samples,        arrayResize([0],         length(arr__t_nonevents),  0))        as arr__counter_samples_with_nonevents,
            arrayConcat(arr__counter_samples_needed, arrayResize([0],         length(arr__t_nonevents),  0))        as arr__counter_samples_needed_with_nonevents,

            -- Re-sort new arrays (place nonevents into time sequence)
            arraySort(arr__t_with_nonevents)                                                          as arr__t_with_nonevents_sorted,
            arraySort((x, y) -> y, arr__ingress_router_with_nonevents,         arr__t_with_nonevents) as arr__ingress_router_with_nonevents_sorted,
            arraySort((x, y) -> y, arr__pni_with_nonevents,                    arr__t_with_nonevents) as arr__pni_with_nonevents_sorted,
            arraySort((x, y) -> y, arr__mask_with_nonevents,                   arr__t_with_nonevents) as arr__mask_with_nonevents_sorted,

            arraySort((x, y) -> y, arr__confidence_with_nonevents,             arr__t_with_nonevents) as arr__confidence_with_nonevents_sorted,
            arraySort((x, y) -> y, arr__counter_samples_with_nonevents,        arr__t_with_nonevents) as arr__counter_samples_with_nonevents_sorted,
            arraySort((x, y) -> y, arr__counter_samples_needed_with_nonevents, arr__t_with_nonevents) as arr__counter_samples_needed_with_nonevents_sorted,

            1
        from
            -- ipd.range__subnet_time_ingress__mv__pni
        -- from (
        -- select * from 
            (select
                *
            from
                max.range__subnet_mini_internet
            where
                parameter_study_type == 'REPLACEMENT3' and
                parameter_study_name == 'REPLACEMENT2'
            ) -- where netid_string = '::ffff:212.51.0.0')
        --     ipd.range__subnet_time_ingress__mv__pni
        --     order by t
        -- ) as X1
        where
            1
            and metroHash64(netid_string) % 8 == REPLACEMENT
        group by
            netid_string,
            parameter_study_type,
            parameter_study_name,
            1
        order by
            netid_string,
            1
    )
) as X2
array join
    arr__events_t as events_t,
    arr__events_ingress_router as events_ingress_router,
    arr__events_pni as events_pni,
    arr__events_mask as events_mask,

    arr__events_confidence as confidence,
    arr__events_counter_samples as counter_samples,
    arr__events_counter_samples_needed as counter_samples_needed,

    arr__state_time_period_length  as length_seconds
where
    events_t < (
        select max(t)
        from max.range__subnet_mini_internet
        where parameter_study_name == 'REPLACEMENT2' and parameter_study_type == 'REPLACEMENT3'
    );

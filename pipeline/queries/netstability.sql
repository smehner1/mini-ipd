INSERT INTO TABLE max.netstability_2_mini_internet
select
    netid_string,
    t__sorted__filtered,
    pni__sorted__filtered,
    mask__sorted__filtered,
    ingress_router__sorted__filtered,
    t__sorted__filtered__lengths,

    sequence_ipd_events_num,
    sequence_ipd_events_lengths_seconds__sum,
    sequence_ipd_events_confidence__avg,
    sequence_ipd_events_confidence__std,
    sequence_ipd_events_confidence_samples__avg,
    sequence_ipd_events_confidence_samples__std,
    sequence_ipd_events_confidence_samples_needed__avg,
    sequence_ipd_events_confidence_samples_needed__std,

    no_data_events_num,
    no_data_events_length_seconds,
    no_data_events_length_seconds_avg,
    no_data_events_length_seconds_std,
    no_data_events_length_seconds_max,

    end_of_sequence_len_seconds,

    t__sorted__filtered__lengths - end_of_sequence_len_seconds as network_stable_timed,
    parameter_study_type,
    parameter_study_name
from (
    select
        -- fixed "stable" sequence data - one row per netid; temporal data within arrays
        netid_string,                           --netid PK
        parameter_study_type,
        parameter_study_name,
        arr__t__sorted__filtered,               --sequence timestamps
        arr__pni__sorted__filtered,             --pni
        arr__mask__sorted__filtered,            --netmask
        arr__ingress_router__sorted__filtered,  --ingress
        -- all data items
        arr__confidence__sorted,                --confidence values per subsequence
        arr__t__sorted__filtered__lengths,      --sequence lengths
        arr__confidnece_samples__sorted,        --samples
        arr__confidnece_samples_needed__sorted, --samples_needed

        -- do aggregation over stable period timeframes
        -- in practice we shoul have rather a O(n) version calculating aggregation ranges instead of n times each
        -- filtering.
        -- idea: use arr__ingress_change_mask to determine starting time + calculate amount of subsequrnt items within
        --       given timeframe to slice.
        -- TOY:
        -- select
        --     [1,0,0,0,1,1,0,0] as arr__ingress_change_mask,

        ----do cumsum creating ids for all items in sequence
        --arrayCumSum(arr__ingress_change_mask) as arr__ingress_change_mask_ids,
        ----leverage these ids to sumMap these ids
        --sumMap(
        --    arr__ingress_change_mask_ids, --by ids
        --    arrayResize([1], length(arr__ingress_change_mask), 1) --simply count.
        --) as arr__ingress_change_mask_item_lengths,
        ---- ┌─arr__ingress_change_mask─┬─arr__ingress_change_mask_ids─┬─sumMap(arrayCumSum([1, 0, 0, 0, 1, 1, 0, 0]),
        ----arrayResize([1], length([1, 0, 0, 0, 1, 1, 0, 0]), 1))─┐
        ---- │ [1,0,0,0,1,1,0,0]        │ [1,1,1,1,2,3,3,3]            │ ([1,2,3],[4,1,3])
        ----                                                       │
        ---- └──────────────────────────┴──────────────────────────────┴───────────────────────────────────────────────
        ----───────────────────────────────────────────────────────┘

        arrayFilter(
            (x, y) -> y == 1,
            arrayCumSum( --create array index via cumsum
                arrayResize([1], length(arr__ingress_change_mask), 1)
            ),
            arr__ingress_change_mask --filter for start indexes
        ) as cumsum_id_start_index,

        -- count amount of values for defining aggregation ranges
        sumMap(
            arrayCumSum(arr__ingress_change_mask), --by ids created by cumsum, whoop whoop; should NOT(!) contain ID 0.
            arrayResize([1], length(arr__ingress_change_mask), 1) --simply count.
        ) as arr__ingress_change_mask_item_lengths,
        -- arraySlice(arr__ingress_change_mask_item_lengths.2, 2) as arr__sequence_ipd_events_num, --1 = DO NOT; 2 = cut
        --   first element --> arraydifference may start with 0 & therefore cumsum id 0, however, inner select marks
        --   first occurrence as diff.
        arr__ingress_change_mask_item_lengths.2 as arr__sequence_ipd_events_num,

        -- assemble aggregation ranges
        arrayMap(
            (y, z) -> tuple(z, y), --index + len(!)
            arr__ingress_change_mask_item_lengths.2, --count of values within sequence / seq len
            cumsum_id_start_index --use index to define range start / seq offset
        ) as arr__ingress_change_mask_item_lengths__ranges,

        --do aggregation on sequences
        arrayReduceInRanges(
            'sum',
            arr__ingress_change_mask_item_lengths__ranges,
            arr__length_seconds__sorted --arr__t__sorted__filtered__lengths
        ) as arr__sequence_ipd_events_lengths_seconds__sum,
        arrayReduceInRanges(
            'avg',
            arr__ingress_change_mask_item_lengths__ranges,
            arr__confidence__sorted
        ) as arr__sequence_ipd_events_confidence__avg,
        arrayReduceInRanges(
            'stddevPop',
            arr__ingress_change_mask_item_lengths__ranges,
            arr__confidence__sorted
        ) as arr__sequence_ipd_events_confidence__std,
        arrayReduceInRanges(
            'avg',
            arr__ingress_change_mask_item_lengths__ranges,
            arr__confidnece_samples__sorted
        ) as arr__sequence_ipd_events_confidence_samples__avg,
        arrayReduceInRanges(
            'stddevPop',
            arr__ingress_change_mask_item_lengths__ranges,
            arr__confidnece_samples__sorted
        ) as arr__sequence_ipd_events_confidence_samples__std,
        arrayReduceInRanges(
            'avg',
            arr__ingress_change_mask_item_lengths__ranges,
            arr__confidnece_samples_needed__sorted
        ) as arr__sequence_ipd_events_confidence_samples_needed__avg,
        arrayReduceInRanges(
            'stddevPop',
            arr__ingress_change_mask_item_lengths__ranges,
            arr__confidnece_samples_needed__sorted
        ) as arr__sequence_ipd_events_confidence_samples_needed__std,

        -- NO DATA EVENTS
        --merge timestamp for ipd events & no-data events + create mask for ipd events (anchor elements**).
        arraySort(
            (x, y) -> y,
            --first, we concatenate dummy-0 elements for each no-data events WITH the change events mask
            arrayConcat(
                arrayResize([0], length(arr__t__noevents__sorted), 0),
                arrayResize([1], length(arr__t__sorted__filtered), 1)
            ),
            --and put them into a sorted list by timestamp --> arrayCumSum again will later deliver ids for each stable
            --ipd sequence
            arrayConcat(arr__t__noevents__sorted, arr__t__sorted__filtered)
        ) as no_data_events_mask,

        arrayFilter( --gather mask indices for ranges
            (x, y) -> y == 1,
            arrayCumSum( --create array index via cumsum
                arrayResize([1], length(no_data_events_mask), 1)
            ),
            no_data_events_mask --filter for start indexes
        ) as cumsum_noevent_id_start_index,

        sumMap( --count no-data event array items per sequence
            arrayCumSum(no_data_events_mask), --by ids created by cumsum, whoop whoop
            arrayResize([1], length(no_data_events_mask), 1) --simply count.
        ) as no_data_events_mask_item_lengths,
        arrayMap(
            x -> x - 1, --remove anchor element(**) from counts
            no_data_events_mask_item_lengths.2
        ) as arr__no_data_events_num,

        -- assemble aggregation ranges
        arrayMap(
            --index + len. offset+1 & #items-1 due to ipd event items within mask array.
            (num_items, offset) -> tuple(toUInt64(offset + 1), toUInt64(num_items - 1)),
            no_data_events_mask_item_lengths.2, --count of values within sequence / seq len
            cumsum_noevent_id_start_index --use index to define range start / seq offset
        ) as no_data_events_mask_ranges,

        -- do aggregation on sequences
        arraySort(
            (x, y) -> y,
            arrayConcat(
                arr__length_seconds__noevents__sorted,
                arrayResize([0], length(arr__t__sorted__filtered), 0)
            ),
            arrayConcat(
                arr__t__noevents__sorted,
                arr__t__sorted__filtered
            )
        ) as length_total_values_to_noevent_mask,
        -- no_data_events_mask_ranges,
        -- length_total_values_to_noevent_mask,
        -- length(length_total_values_to_noevent_mask),
        arrayReduceInRanges(
            'sum',
            no_data_events_mask_ranges,
            length_total_values_to_noevent_mask
        ) as arr__length_seconds__noevents_sum,
        arrayMap(
            x -> coalesce(x, 0),
            arrayReduceInRanges(
                'avgOrNull',
                no_data_events_mask_ranges,
                length_total_values_to_noevent_mask
            )
        ) as arr__length_seconds__noevents_avg,
        arrayMap(
            x -> coalesce(x, 0),
            arrayReduceInRanges(
                'stddevPopOrNull',
                no_data_events_mask_ranges,
                length_total_values_to_noevent_mask
            )
        ) as arr__length_seconds__noevents_std,
        arrayReduceInRanges(
            'max',
            no_data_events_mask_ranges,
            length_total_values_to_noevent_mask
        ) as arr__length_seconds__noevents_max,


        -- specific request: "undefined time" - time from last seen observation of netid at router X to changing ingress
        --                                      to router Y
        --                                      ie sequences' last item timespan - use no-data events as proxy.
        arrayPopFront(
            arrayPushBack(
                no_data_events_mask,
                1
            )
        ) as arr__end_of_sequence_mask,
        arrayFilter(
            (x, y) -> y == 1,
            --lengths of undefined period = length of last nodata event or ipd sampling delay (<=7.5min as defined in
            --raw-MV)
            arraySort(
                (x, y) -> y,
                --first, we gather lengts of nodata & ipd events=0
                arrayConcat(
                    arr__length_seconds__noevents__sorted,
                    arrayResize( --default may also be set to threshold 7.5min as defined upper bound.
                        [0],
                        length(arr__t__sorted__filtered),
                        0
                    )
                ),
                --and sort them by timestamp
                arrayConcat(arr__t__noevents__sorted, arr__t__sorted__filtered)
            ),
            -- these will be filtered by end of sequence mask
            arr__end_of_sequence_mask
        ) as arr__end_of_sequence_len_seconds,
        1
    from (
        select
            -- DO SORTING, mentioned in some old issue, clickhouse bright break order between blocks vs arraying.
            netid_string,
            parameter_study_type,
            parameter_study_name,

            arraySort(arr__t) as arr__t__sorted,
            arraySort((x, y) -> y, arr__pni,                    arr__t) as arr__pni__sorted,
            arraySort((x, y) -> y, arr__mask,                   arr__t) as arr__mask__sorted,
            arraySort((x, y) -> y, arr__t_ingress_router,       arr__t) as arr__ingress_router__sorted,
            arraySort((x, y) -> y, arr__confidence,             arr__t) as arr__confidence__sorted,
            arraySort((x, y) -> y, arr__counter_samples,        arr__t) as arr__confidnece_samples__sorted,
            arraySort((x, y) -> y, arr__counter_samples_needed, arr__t) as arr__confidnece_samples_needed__sorted,
            arraySort((x, y) -> y, arr__length_seconds,         arr__t) as arr__length_seconds__sorted,

            arraySort(arr__t__noevents) as arr__t__noevents__sorted,
            arraySort(
                (x, y) -> y, arr__length_seconds__noevents, arr__t__noevents) as arr__length_seconds__noevents__sorted,

            -- do stability recalculation
            arrayMap(
                x -> x <> 0,
                arrayPushFront(
                    arrayPopFront(
                        arrayDifference(
                            arrayMap(
                                x -> metroHash64(x),
                                arr__ingress_router__sorted
                            )
                        )
                    ),
                    1 --mark first occurrence as change(!)
                )
            ) as arr__ingress_change_mask,

            -- filter data according to change events, fixed values first
            arrayFilter(
                (x, y) -> y <> 0,
                arr__t__sorted,
                arr__ingress_change_mask) as arr__t__sorted__filtered,
            arrayFilter(
                (x, y) -> y <> 0,
                arr__pni__sorted,
                arr__ingress_change_mask) as arr__pni__sorted__filtered,
            arrayFilter(
                (x, y) -> y <> 0,
                arr__mask__sorted,
                arr__ingress_change_mask) as arr__mask__sorted__filtered,
            arrayFilter(
                (x, y) -> y <> 0,
                arr__ingress_router__sorted,
                arr__ingress_change_mask) as arr__ingress_router__sorted__filtered,

            -- stability period TIME length to the above key (also used to filter aggregations)
            arrayPopFront(
                arrayDifference(
                    arrayMap(
                        x -> toUnixTimestamp(x),
                        --add sentinal to end of observation for this netid.
                        arrayPushBack(
                            arrayFilter(--get all change events
                                (x, y) -> y <> 0,
                                arr__t__sorted,
                                arr__ingress_change_mask
                            ),
                            arrayReduce( --take last observation from raw data (note: this is _no_ non-event)
                                'max',
                                arr__t__sorted
                            )
                        )
                    )
                )
            ) as arr__t__sorted__filtered__lengths,
            -- filter possibly changing data
            --O(n^2) version; quite slow. -----> moved into better version, but seems needing another aggregation layer.
            -- arrayMap( --iterate through change events
            --     thetimestamp, thelength ->
            --         arrayFilter( --and filter all matching timestamps from rawdata for later aggregation
            --             (_, join_series) -> thetimestamp <= join_series and join_series < thetimestamp + thelength,
            --             arr__confidence__sorted, --field to be aggregated
            --             arr__t__sorted --from all raw-data timestamps (no non-events)
            --         ),
            --     arr__t__sorted__filtered,
            --     arr__t__sorted__filtered__lengths
            -- ) as arr_confience_values,

            1
        from (
            select
                --GATHER DATA per netid
                -- aggregate definition
                netid_string,
                parameter_study_type,
                parameter_study_name,

                -- distinction between events & noevents.
                groupArray(pni) as arr__pni_all,

                --actual data. cast(-1 as UInt8)=255
                arrayFilter(y -> y <> 255, arr__pni_all) as arr__pni,
                arrayFilter(x, y -> y <> 255, groupArray(t), arr__pni_all) as arr__t,
                arrayFilter(x, y -> y <> 255, groupArray(mask), arr__pni_all) as arr__mask,
                arrayFilter(
                    x, y -> y <> 255,
                    groupArray(splitByChar('(', ingress_router)[1]), arr__pni_all) as arr__t_ingress_router,
                arrayFilter(x, y -> y <> 255, groupArray(confidence), arr__pni_all) as arr__confidence,
                arrayFilter(x, y -> y <> 255, groupArray(counter_samples), arr__pni_all) as arr__counter_samples,
                arrayFilter(
                    x, y -> y <> 255,
                    groupArray(counter_samples_needed), arr__pni_all) as arr__counter_samples_needed,
                arrayFilter(x, y -> y <> 255, groupArray(length_seconds), arr__pni_all) as arr__length_seconds,
                --no-events
                arrayFilter(x, y -> y == 255, groupArray(t), arr__pni_all) as arr__t__noevents,
                arrayFilter(
                    x, y -> y == 255, groupArray(length_seconds), arr__pni_all) as arr__length_seconds__noevents,
                1
            from (
                select
                    *
                from
                    max.aggregate_netid_ingress__mv_bundles_mini_internet
                where
                    1
                    -- and netid_string = '::ffff:80.249.160.0'
                    and metroHash64(netid_string) % REPLACE1 == REPLACE2
                    and t > toDateTime('1970-01-01 01:00:00') --remove spurious entries. cnt=2
                    and parameter_study_name == 'REPLACE3' and parameter_study_type == 'REPLACE4'
                order by t
                -- limit 49
            )
            group by
                netid_string, parameter_study_name, parameter_study_type
            having --remove single events (1x ipd + 1x nodata) causing trouble.
                count() > 2 --caused trouble within non-event aggregation range foo
            -- we might order by time here as well, however, we simply do it in the outer aggregation.
        )
    )
    group by
        netid_string,
        parameter_study_type,
        parameter_study_name,
        arr__t__sorted__filtered,
        arr__pni__sorted__filtered,
        arr__ingress_router__sorted__filtered,
        arr__t__sorted__filtered__lengths,
        arr__mask__sorted__filtered,
        arr__confidence__sorted,
        arr__confidnece_samples__sorted,
        arr__confidnece_samples_needed__sorted,
        arr__t__noevents__sorted,
        arr__length_seconds__noevents__sorted,
        arr__ingress_change_mask,
        arr__t__sorted,
        arr__length_seconds__sorted,
        1
    having
        1

)
array join
    arr__t__sorted__filtered as t__sorted__filtered,
    arr__pni__sorted__filtered as pni__sorted__filtered,
    arr__mask__sorted__filtered as mask__sorted__filtered,
    arr__ingress_router__sorted__filtered as ingress_router__sorted__filtered,
    arr__t__sorted__filtered__lengths as t__sorted__filtered__lengths,

    arr__sequence_ipd_events_num as sequence_ipd_events_num,
    arr__sequence_ipd_events_lengths_seconds__sum as sequence_ipd_events_lengths_seconds__sum,
    arr__sequence_ipd_events_confidence__avg as sequence_ipd_events_confidence__avg,
    arr__sequence_ipd_events_confidence__std as sequence_ipd_events_confidence__std,
    arr__sequence_ipd_events_confidence_samples__avg as sequence_ipd_events_confidence_samples__avg,
    arr__sequence_ipd_events_confidence_samples__std as sequence_ipd_events_confidence_samples__std,
    arr__sequence_ipd_events_confidence_samples_needed__avg as sequence_ipd_events_confidence_samples_needed__avg,
    arr__sequence_ipd_events_confidence_samples_needed__std as sequence_ipd_events_confidence_samples_needed__std,

    arr__no_data_events_num as no_data_events_num,
    arr__length_seconds__noevents_sum as no_data_events_length_seconds,
    arr__length_seconds__noevents_avg as no_data_events_length_seconds_avg,
    arr__length_seconds__noevents_std as no_data_events_length_seconds_std,
    arr__length_seconds__noevents_max as no_data_events_length_seconds_max,

    arr__end_of_sequence_len_seconds as end_of_sequence_len_seconds
order by
    netid_string,
    parameter_study_type,
    parameter_study_name,
    t__sorted__filtered;
#!/bin/bash

basis=$(pwd)
VERBOSE=0

# read possible flags, otherwise use default values
while getopts "v" OPTION; do
    case "$OPTION" in
        v)
            VERBOSE=1
            ;;
        ?)
            echo "script usage: $(basename \$0) [-v]" >&2
            exit 1
            ;;
    esac
done
shift "$(($OPTIND -1))"

# dir="/home/max/WORK/masterthesis/traffic_generator/test_netflow"
# dir="/home/max/Documents/workspace/playground/garbage/netflow"
dir="/home/netflow"
cd $dir

# will include the folders for all ports on one router
readarray -t folders <<< $(ls -d -- */)

DAY=$(date +%D)
DAY=${DAY//"/"/" "}
DAY_ARR=($DAY)

MONTH=${DAY_ARR[0]}
MONTH=$(sed 's/^0*//'<<< $MONTH)  # remove leading zero
DAY=${DAY_ARR[1]}
DAY=$(sed 's/^0*//'<<< $DAY)  # remove leading zero
YEAR="20"${DAY_ARR[2]}

# echo $MONTH

# YEAR=2023
# MONTH=1
# DAY=10

# go 2 days back
CUT_DAY=$((DAY-1))

# adjust the CUT_DATES if 2 days back was another month and/or year
if [ $CUT_DAY -lt 1 ]; then
    CUT_MONTH=$((MONTH-1))
    if [ $CUT_MONTH -lt 1 ]; then
        CUT_YEAR=$((YEAR-1))
        CUT_MONTH=12
    else
        CUT_YEAR=$YEAR
    fi

    if [ $CUT_MONTH -eq 2 ]; then
        CUT_DAY=$((CUT_DAY+28))
    fi
    if [ $CUT_MONTH -eq 1 ] || [ $CUT_MONTH -eq 3 ] || [ $CUT_MONTH -eq 5 ] || [ $CUT_MONTH -eq 7 ] || [ $CUT_MONTH -eq 8 ] || [ $CUT_MONTH -eq 10 ] || [ $CUT_MONTH -eq 12 ] ; then
        CUT_DAY=$((CUT_DAY+31))
    else
        CUT_DAY=$((CUT_DAY+30))
    fi
else
    CUT_MONTH=$MONTH
    CUT_YEAR=$YEAR
fi

if [ $VERBOSE -eq 1 ]; then
    # add possible leading zeros for output
    if [ ${DAY} -lt 10 ]; then
        DAY=0${DAY}
    fi
    if [ ${CUT_DAY} -lt 10 ]; then
        CUT_DAY=0${CUT_DAY}
    fi
    if [ ${MONTH} -lt 10 ]; then
        MONTH=0${MONTH}
    fi
    if [ ${CUT_MONTH} -lt 10 ]; then
        CUT_MONTH=0${CUT_MONTH}
    fi
    echo
    echo "|------------------------|"
    echo "| TODAY DATE: $DAY/$MONTH/$YEAR |"
    echo "| CUT DATE:   $CUT_DAY/$CUT_MONTH/$CUT_YEAR |"
    echo "|------------------------|"
    echo
    # remove leading zeros for calculations
    DAY=$(sed 's/^0*//'<<< $DAY)
    MONTH=$(sed 's/^0*//'<<< $MONTH)
    CUT_DAY=$(sed 's/^0*//'<<< $CUT_DAY)
    CUT_MONTH=$(sed 's/^0*//'<<< $CUT_MONTH)
fi

for folder in "${folders[@]}"; do
    folder_array=(${folder})

    # /home/netflow/port-1/YEAR/MONTH/DAY/*.nfcapd

    if [ $folder_array != $dir ]; then

        port_folder=${dir}/${folder_array}
        cd $port_folder

        # ############### YEAR #################
        if [ $VERBOSE -eq 1 ]; then
            echo "|------------------------------------------------"
            echo "|----------- START WITH ${folder_array}"
            echo "|------------------------------------------------"

            echo "| DIRECTORY: $(pwd)"
            echo "|"
        fi

        readarray -t year_folders <<< $(ls -d -- */)
        years=()
        
        if [ $VERBOSE -eq 1 ]; then
            echo "|--> Check if going back gives another Year"
        fi
        if [ $CUT_YEAR -eq $YEAR ]; then
            if [ $VERBOSE -eq 1 ]; then
                echo "|----> No change for Year --> Have a Look at available Years"
                echo "|"
            fi
            for year_folder in "${year_folders[@]}"; do
                year_folder_array=(${year_folder})
                year_folder_array=${year_folder_array::-1}
                year_folder_array=$(sed 's/^0*//'<<< $year_folder_array)  # remove leading zero
                if [ $VERBOSE -eq 1 ]; then
                    echo "|--------> $year_folder_array --> earlier than $CUT_YEAR?"
                fi
                # echo $year_folder_array
                if [ $((year_folder_array)) -lt $YEAR ]; then
                    if [ $VERBOSE -eq 1 ]; then
                        echo "|------------> Yes --> Remove this Year-Directory"
                        echo "|------------> ${port_folder}${year_folder_array}"
                        echo "|"
                    fi
                    rm -r ${port_folder}${year_folder_array}
                else
                    years+=($year_folder_array)
                    if [ $VERBOSE -eq 1 ]; then
                        echo "|------------> NO  --> Look into this Year-Directory"
                        echo "|------------> Open Directories: ${years[@]}"
                        echo "|"
                    fi
                fi
            done
        else
            if [ $VERBOSE -eq 1 ]; then
                echo "|----> Year has changed --> only remove directories lower than $CUT_YEAR"
                echo "|"
            fi
            for year_folder in "${year_folders[@]}"; do
                year_folder_array=(${year_folder})
                year_folder_array=${year_folder_array::-1}
                year_folder_array=$(sed 's/^0*//'<<< $year_folder_array)  # remove leading zero
                if [ $VERBOSE -eq 1 ]; then
                    echo "|--------> $year_folder_array --> earlier than $CUT_YEAR?"
                fi
                # echo $year_folder_array
                if [ $((year_folder_array)) -lt $CUT_YEAR ]; then
                    if [ $VERBOSE -eq 1 ]; then
                        echo "|------------> Yes --> Remove this Year-Directory"
                        echo "|------------> ${port_folder}${year_folder_array}"
                        echo "|"
                    fi
                    rm -r ${port_folder}${year_folder_array}
                else
                    years+=($year_folder_array)
                    if [ $VERBOSE -eq 1 ]; then
                        echo "|------------> NO  --> Look into this Year-Directory"
                        echo "|--------------------> Open Directories: ${years[@]}"
                        echo "|"
                    fi
                fi
            done
        fi

        if [ $VERBOSE -eq 1 ]; then
            echo "|--> Look into Years: ${years[@]}"
            echo "|------------------------------------------"
        fi

        # LOOK INTO MONTHS

        years_counter=0
        years_length=${#years[@]}

        for year in "${years[@]}"; do
            act_year=(${year})

            months=()

            year_folder=${dir}/${folder_array}$year
            cd $year_folder
            if [ $VERBOSE -eq 1 ]; then
                echo "  |---> Look into year $act_year"
                echo "  |-----> Directory:"
                echo "  |      $year_folder"
            fi

            if [ $act_year -le $CUT_YEAR ]; then
                if [ $VERBOSE -eq 1 ]; then
                    echo "  |"
                    echo "  |-----> Check if going back gives another Month"
                fi

                readarray -t month_folders <<< $(ls -d -- */)

                if [ $CUT_MONTH -eq $MONTH ]; then
                    if [ $VERBOSE -eq 1 ]; then
                        echo "  |------> No change for Month --> Have a Look at available Months in $act_year"
                        echo "  |"
                    fi
                    for month_folder in "${month_folders[@]}"; do
                        month_folder_array=(${month_folder})
                        month_folder_array=${month_folder_array::-1}
                        month_folder_array=$(sed 's/^0*//'<<< $month_folder_array)  # remove leading zero
                        if [ $VERBOSE -eq 1 ]; then
                            echo "  |----------> $month_folder_array --> earlier than $MONTH?"
                        fi
                        if [ $((month_folder_array)) -lt $MONTH ]; then
                            if [ $VERBOSE -eq 1 ]; then
                                echo "  |------------> Yes --> Remove this Month-Directory"
                                if [ ${month_folder_array} -lt 10 ]; then
                                    echo "  |------------> ${port_folder}${act_year}/0${month_folder_array}"
                                else
                                    echo "  |------------> ${port_folder}${act_year}/${month_folder_array}"
                                fi
                                echo "  |"
                            fi
                            if [ ${month_folder_array} -lt 10 ]; then
                                rm -r ${port_folder}${act_year}/0${month_folder_array}
                            else
                                rm -r ${port_folder}${act_year}/${month_folder_array}
                            fi
                        else
                            months+=($month_folder_array)
                            if [ $VERBOSE -eq 1 ]; then
                                echo "  |------------> NO  --> Look into this Year-Directory"
                                echo "  |--------------------> Open Directories: ${months[@]}"
                                echo "  |"
                            fi
                        fi
                    done
                else
                    if [ $VERBOSE -eq 1 ]; then
                        echo "  |-------> Month has changed --> only remove directories lower than $CUT_MONTH"
                        echo "  |"
                    fi
                    for month_folder in "${month_folders[@]}"; do
                        month_folder_array=(${month_folder})
                        month_folder_array=${month_folder_array::-1}
                        month_folder_array=$(sed 's/^0*//'<<< $month_folder_array)  # remove leading zero
                        if [ $VERBOSE -eq 1 ]; then
                            echo "  |-----------> $month_folder_array --> earlier than $CUT_MONTH?"
                        fi
                        if [ $((month_folder_array)) -lt $CUT_MONTH ]; then
                            if [ $VERBOSE -eq 1 ]; then
                                echo "  |-------------> Yes --> Remove this Month-Directory"
                                if [ ${month_folder_array} -lt 10 ]; then
                                    echo "  |------------> ${port_folder}${act_year}/0${month_folder_array}"
                                else
                                    echo "  |------------> ${port_folder}${act_year}/${month_folder_array}"
                                fi
                                echo "  |"
                            fi
                            if [ ${month_folder_array} -lt 10 ]; then
                                rm -r ${port_folder}${act_year}/0${month_folder_array}
                            else
                                rm -r ${port_folder}${act_year}/${month_folder_array}
                            fi
                        else
                            months+=($month_folder_array)
                            if [ $VERBOSE -eq 1 ]; then
                                echo "  |-------------> NO  --> Look into this Year-Directory"
                                echo "  |---------------------> Open Directories: ${months[@]}"
                                echo "  |"
                            fi
                        fi
                    done
                fi

                months_length=${#months[@]}
                month_counter=0

                if [ $VERBOSE -eq 1 ]; then
                    echo "  |---> Look into Months ${months[@]} in Year ${year}"
                    echo "  |----------------------------------------------"
                fi

                # LOOK INTO DAYS

                for month in "${months[@]}"; do
                    act_month=(${month})

                    if [ ${month} -lt 10 ]; then
                        month_folder=${dir}/${folder_array}${year}/0${month}
                    else
                        month_folder=${dir}/${folder_array}${year}/${month}
                    fi
                    cd $month_folder

                    if [ $VERBOSE -eq 1 ]; then
                        echo "    |---> Look into month $act_month"
                        echo "    |-----> Directory:"
                        echo "    |      $month_folder"
                    fi

                    if [ $act_month -le $CUT_MONTH ] && [ $act_year -ge $CUT_YEAR ]; then
                        if [ $VERBOSE -eq 1 ]; then
                            echo "    |"
                            echo "    |-----> Check if going back gives another Day"
                        fi

                        readarray -t day_folders <<< $(ls -d -- */)

                        if [ $CUT_DAY -eq $DAY ]; then
                            if [ $VERBOSE -eq 1 ]; then
                                echo "    |-------> No change for Day --> Have a Look at available Days in $act_month"
                                echo "    |"
                            fi
                            for day_folder in "${day_folders[@]}"; do
                                day_folder_array=(${day_folder})
                                day_folder_array=${day_folder_array::-1}
                                day_folder_array=$(sed 's/^0*//'<<< $day_folder_array)  # remove leading zero
                                if [ $VERBOSE -eq 1 ]; then
                                    echo "    |-----------> $day_folder_array --> earlier than $DAY?"
                                fi
                                if [ $((day_folder_array)) -le $DAY ]; then
                                    if [ $VERBOSE -eq 1 ]; then
                                        echo "    |-------------> Yes --> Remove this Day-Directory"
                                        if [ ${month} -lt 10 ]; then
                                            echo "    |-------------> ${month_folder}/0${day_folder_array}"
                                        else
                                            echo "    |-------------> ${month_folder}/${day_folder_array}"
                                        fi
                                        echo "    |"
                                    fi
                                    if [ ${day_folder_array} -lt 10 ]; then
                                        rm -r ${month_folder}/0${day_folder_array}
                                    else
                                        rm -r ${month_folder}/${day_folder_array}
                                    fi
                                else
                                    if [ $VERBOSE -eq 1 ]; then
                                        echo "    |-------------> NO  --> Don't remove this Day-Directory!"
                                        echo "    |"
                                    fi
                                fi
                            done
                        else
                            if [ $VERBOSE -eq 1 ]; then
                                echo "    |-------> Day has changed --> only remove directories lower than $CUT_DAY"
                                echo "    |"
                            fi
                            for day_folder in "${day_folders[@]}"; do
                                day_folder_array=(${day_folder})
                                day_folder_array=${day_folder_array::-1}
                                day_folder_array=$(sed 's/^0*//'<<< $day_folder_array)  # remove leading zero
                                if [ $VERBOSE -eq 1 ]; then
                                    echo "    |-----------> $day_folder_array --> earlier than $CUT_DAY?"
                                fi
                                if [ $((day_folder_array)) -le $CUT_DAY ]; then
                                    if [ $VERBOSE -eq 1 ]; then
                                        echo "    |-------------> Yes --> Remove this Day-Directory"
                                        if [ ${month} -lt 10 ]; then
                                            echo "    |-------------> ${month_folder}/0${day_folder_array}"
                                        else
                                            echo "    |-------------> ${month_folder}/${day_folder_array}"
                                        fi
                                        echo "    |"
                                    fi
                                    if [ ${day_folder_array} -lt 10 ]; then
                                        rm -r ${month_folder}/0${day_folder_array}
                                    else
                                        rm -r ${month_folder}/${day_folder_array}
                                    fi
                                else
                                    if [ $VERBOSE -eq 1 ]; then
                                        echo "    |-------------> NO  --> Don't remove this Directory!"
                                        echo "    |"
                                    fi
                                fi
                            done
                        fi

                        if [ $VERBOSE -eq 1 ]; then
                            echo "    |---> Finished this Month"
                            echo "    |"
                        fi
                    else
                        if [ $VERBOSE -eq 1 ]; then
                            echo "    |"
                            echo "    |---> This month can be skipped"
                            echo "    |"
                        fi
                    fi

                    month_counter=$((month_counter+1))
                    if [ $month_counter -lt $months_length ]; then
                        if [ $VERBOSE -eq 1 ]; then
                            echo "    |--------------------------------------------"
                        fi
                    else
                        if [ $years_counter -lt $((years_length-1)) ]; then
                            if [ $VERBOSE -eq 1 ]; then
                                echo "  |----------------------------------------------"
                            fi
                        else
                            if [ $VERBOSE -eq 1 ]; then
                                echo "|------------------------------------------------"
                            fi
                        fi
                    fi
                done

            else
                    if [ $VERBOSE -eq 1 ]; then
                        echo "  |"
                        echo "  |---> This year can be skipped"
                    fi

                    if [ $years_counter -lt $((years_length-1)) ]; then
                        if [ $VERBOSE -eq 1 ]; then
                            echo "  |"
                        fi
                    else
                        if [ $VERBOSE -eq 1 ]; then
                            echo "|------------------------------------------------"
                        fi
                    fi
            fi

            years_counter=$((years_counter+1))
            
        done

        cd ${dir}
        if [ $VERBOSE -eq 1 ]; then
            echo "|----------- FINSIHED WITH ${folder_array}"
            echo "|------------------------------------------------"
        fi
    fi

    if [ $VERBOSE -eq 1 ]; then
        echo
    fi
done

cd $basis

#!/bin/bash
cd /home/amocrm/amo_crm_api_reader
python_script="main.py"
output_file1="$(dirname "$(readlink -f "$PWD")")/leads_csv/msc.csv"
output_file2="$(dirname "$(readlink -f "$PWD")")/leads_csv/spb.csv"

is_file_created_today() {
    local file_path="$1"
    if [ -f "$file_path" ]; then
        local file_date=$(stat --format='%y' "$file_path" | cut -d' ' -f1)
        local today=$(date +%Y-%m-%d)
        [ "$file_date" == "$today" ] && return 0 || return 1
    else
        return 1
    fi
}

run_and_check() {
    local script="$1"
    local output_file="$2"
    local city="$3"

    while true; do
        echo "Запуск: $script $city"
        python3 "$script" "$city" &
        wait $!

        if is_file_created_today "$output_file"; then
            echo "Файл $output_file успешно создан или обновлён сегодня"
            break
        else
            echo "Файл $output_file не создан. Повторный запуск $script"
            find "$(dirname "$(readlink -f "$PWD")")/amo_crm_api_reader" -type f -name "$city_cache.sqlite" -exec rm -f {} \;
        fi
    done
}

source venv/bin/activate
run_and_check "$python_script" "$output_file1" "msc" &
pid1=$!

run_and_check "$python_script" "$output_file2" "spb" &
pid2=$!

wait $pid1
wait $pid2

echo "Оба скрипта отработали успешно, оба файла созданы"

find "$(dirname "$(readlink -f "$PWD")")/amo_crm_api_reader" -type f -name "*.sqlite" -exec rm -f {} \;
echo "Все .sqlite файлы удалены"

echo "Начали создание таблиц в clickhouse"
python3 upload_csv_in_clickhouse.py
echo "Закончили создание таблиц в clickhouse"

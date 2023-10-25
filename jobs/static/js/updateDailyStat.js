async function updateDailyStat() {
    daily_stat = JSON.parse($.ajax({
        'url': `${getCookie('daily_stat_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    let daily_stat_message = "";
    for (let i = 0; i < daily_stat.length; i++){
        daily_stat_message += `\n\nETL Parsed at ${daily_stat[i].date_added} - ${daily_stat[i].number_of_new_jobs} New Jobs\n`;
    }
    document.getElementById("daily_stat").innerText = daily_stat_message;
}
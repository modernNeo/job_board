async function updateAppliedStat() {
    daily_stat = JSON.parse($.ajax({
        'url': `${getCookie('applied_stats_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    let daily_stat_message = "";
    for(const [date, date_stats] of Object.entries(daily_stat)){
        daily_stat_message += `${date}\n - Easy Applied : ${date_stats.easy_apply}\n - Company Website Applied : ${date_stats.company_website_apply}\n`;
    }
    document.getElementById("applied_stats").innerText = daily_stat_message;
}
function setCookie(name, value) {
    document.cookie = `${name}=${value}`;
}
function getCookie(name, value) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies_str = document.cookie;
        if (value !== undefined) {
            // as close to atomic as I can get with trying to read the value of a cookie and update it in one action
            setCookie(name, value)
        }
        const cookies = cookies_str.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                if (!isNaN(cookieValue)){
                    cookieValue = Number(cookieValue);
                }
                if (cookieValue === "null"){
                    cookieValue = null;
                }
                break;
            }
        }
    }
    return cookieValue;
}

async function browserReady() {
    clearCookies();
    if (getCookie("logged_in_user") === "jace") {
        setCookie("pageNumber", 1);
        await updateDailyStat();
        const allLists = JSON.parse($.ajax({
            'url': `${getCookie('list_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
        await refreshDeleteListDropDown(allLists)
        await showListButton(allLists)
        const searchDetected = extractSearchParams();
        if (searchDetected) {
            const allLists = JSON.parse($.ajax({
                'url': `${getCookie('list_endpoint')}`,
                'type': 'GET',
                'cache': false,
                headers: {'X-CSRFToken': getCookie('csrftoken')},
                contentType: 'application/json; charset=utf-8',
                async: false
            }).responseText)
            setCookie("previously_selected_job_index", getCookie("currently_selected_job_index"));
            await refreshAfterJobOrListUpdate(allLists);
        } else {
            await showInbox(allLists)
        }
    }
}
function deleteCookies() {
    var allCookies = document.cookie.split(';');

    // The "expire" attribute of every cookie is
    // Set to "Thu, 01 Jan 1970 00:00:00 GMT"
    for (var i = 0; i < allCookies.length; i++) {
        const key = allCookies[i].split("=")[0].trim();
        const clearable_cookie = (
            key !== "applied_stats_endpoint" && key !== "daily_stat_endpoint" && key !== "job_location_item_endpoint" &&
            key !== "job_item_endpoint" && key !== "job_location_endpoint" && key !== "list_endpoint" &&
            key !== "list_of_jobs_endpoint" && key !== "logged_in_user" && key !== "note_endpoint" &&
            key !== "note_endpoint" && key !== "csrftoken"
        )
        if (clearable_cookie) {
            console.log(`clearing cookie [${key}]`);
            document.cookie = allCookies[i] + "=;expires=" + new Date(0).toUTCString();
        }else{
            console.log(`not clearing cookie [${key}]`);
        }
    }
}
function clearCookies() {
    deleteCookies();
    setCookie("view","inbox")
}
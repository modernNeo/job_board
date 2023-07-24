async function showAllJobs() {
    const all_lists = JSON.parse($.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    setCookie("view", "all_jobs")
    await goToPage(all_lists, 0);
}
async function showInbox(all_lists) {
    if (all_lists === undefined) {
        all_lists = JSON.parse($.ajax({
            'url': `${getCookie('lists_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
        setCookie("view", "all_jobs")
    }
    setCookie("view", "inbox")
    await goToPage(all_lists, 0);
}
async function showArchived(all_lists) {
    if (all_lists === undefined) {
        all_lists = JSON.parse($.ajax({
            'url': `${getCookie('lists_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
        setCookie("view", "all_jobs")
    }
    setCookie("view", "archived")
    await goToPage(all_lists, 0);
}
async function showList(list_obj_id, all_lists) {
    setCookie("page_number", 1)
    setCookie("view", `list_index_${list_obj_id}`);
    if (all_lists === undefined) {
        all_lists = JSON.parse($.ajax({
            'url': `${getCookie('lists_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
    }
    await goToPage(all_lists, 0, list_obj_id);
}
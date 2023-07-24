async function showAllJobs() {
    const allLists = JSON.parse($.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    setCookie("view", "all_jobs")
    await goToPage(allLists, 0);
}
async function showInbox(allLists) {
    if (allLists === undefined) {
        allLists = JSON.parse($.ajax({
            'url': `${getCookie('list_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
        setCookie("view", "all_jobs")
    }
    setCookie("view", "inbox")
    await goToPage(allLists, 0);
}
async function showArchived(allLists) {
    if (allLists === undefined) {
        allLists = JSON.parse($.ajax({
            'url': `${getCookie('list_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
        setCookie("view", "all_jobs")
    }
    setCookie("view", "archived")
    await goToPage(allLists, 0);
}
async function showList(listObjectId, allLists) {
    setCookie("pageNumber", 1)
    setCookie("view", `list_index_${listObjectId}`);
    if (allLists === undefined) {
        allLists = JSON.parse($.ajax({
            'url': `${getCookie('list_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
    }
    await goToPage(allLists, 0, listObjectId);
}
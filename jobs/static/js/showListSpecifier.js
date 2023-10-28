async function showAllJobs() {
    const searchParams = new URLSearchParams(window.location.search.slice(1));
    if (searchParams.get("view") !== "all_jobs") {
        const urlParamsSetter = new URLSearchParams(window.location.search);
        urlParamsSetter.set("view", "all_jobs")
        window.location.search = urlParamsSetter;
    }
    setCookie("view", "all_jobs")
    const allLists = JSON.parse($.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    await goToPage(allLists, 0);
}
async function showAppliedJobs(allLists) {
    const searchParams = new URLSearchParams(window.location.search.slice(1));
    if (searchParams.get("view") !== "applied_jobs") {
        const urlParamsSetter = new URLSearchParams(window.location.search);
        urlParamsSetter.set("view", "applied_jobs")
        window.location.search = urlParamsSetter;
    }
    setCookie("view", "applied_jobs")
    await goToPage(allLists, 0);
}

async function showInbox(allLists) {
    const searchParams = new URLSearchParams(window.location.search.slice(1));
    if (searchParams.get("view") !== "inbox") {
        const urlParamsSetter = new URLSearchParams(window.location.search);
        urlParamsSetter.set("view", "inbox")
        window.location.search = urlParamsSetter;
    }
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
    const searchParams = new URLSearchParams(window.location.search.slice(1));
    if (searchParams.get("view") !== "archived") {
        const urlParamsSetter = new URLSearchParams(window.location.search);
        urlParamsSetter.set("view", "archived")
        window.location.search = urlParamsSetter;
    }
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
    const searchParams = new URLSearchParams(window.location.search.slice(1));
    if (searchParams.get("view") !== `list_index_${listObjectId}`) {
        const urlParamsSetter = new URLSearchParams(window.location.search);
        urlParamsSetter.set("view", `list_index_${listObjectId}`)
        window.location.search = urlParamsSetter;
    }
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
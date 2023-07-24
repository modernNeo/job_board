async function goToPreviousPage() {
    const allLists = $.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    const view = getCookie("view");
    const listObjectId = view.match(/^list_index_\d*$/) ? Number(view.slice(11)) : view;
    await goToPage(allLists,  - 1, listObjectId);
}
async function goToNextPage() {
    const allLists = $.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    const view = getCookie("view");
    const listObjectId = view.match(/^list_index_\d*$/) ? Number(view.slice(11)) : view;
    await goToPage(allLists, 1, listObjectId);
}


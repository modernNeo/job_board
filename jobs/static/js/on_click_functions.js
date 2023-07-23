

async function goToPreviousPage() {
    const all_lists = $.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    const view = getCookie("view");
    const list_obj_id = view.match(/^list_index_\d*$/) ? Number(view.slice(11)) : view;
    await goToPage(all_lists,  - 1, list_obj_id);
}
async function goToNextPage() {
    const all_lists = $.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    const view = getCookie("view");
    const list_obj_id = view.match(/^list_index_\d*$/) ? Number(view.slice(11)) : view;
    await goToPage(all_lists, 1, list_obj_id);
}


async function goToPreviousPage() {await goToSpecifiedPage(-1);}

async function goToNextPage() {await goToSpecifiedPage(1);}

async function goToSpecifiedPage(newPageDifference) {
    const allLists = JSON.parse($.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    const view = getCookie("view");
    const listObjectId = view.match(/^list_index_\d*$/) ? Number(view.slice(11)) : view;
    await goToPage(allLists, newPageDifference, listObjectId);
}
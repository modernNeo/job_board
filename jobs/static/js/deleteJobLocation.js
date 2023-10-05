async function deleteJobLocation(job_location_id) {
    $.ajax({
        'url': `${getCookie('job_location_endpoint')}${job_location_id}`,
        'type': 'DELETE',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    });
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
}
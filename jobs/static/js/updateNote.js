async function saveNote(jobObjectId) {
    setCookie("currently_selected_job_id", jobObjectId);
    if ((document.getElementById("note").value).trim().length === 0) {
        await $.ajax({
            'url': `${getCookie('note_endpoint')}${jobObjectId}`,
            'type': 'DELETE',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        })
    } else {
        let data = {
            "job": jobObjectId,
            "note": document.getElementById("note").value
        }
        await $.ajax({
            'url': getCookie('note_endpoint'),
            'type': 'POST',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            data: JSON.stringify(data),
            contentType: 'application/json; charset=utf-8',
            async: false
        })
    }

    const allLists = $.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    await refreshAfterJobOrListUpdate(allLists);
}
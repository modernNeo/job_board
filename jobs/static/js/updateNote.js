async function saveNote(jobObjectId, note_exists) {
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
        const data = {
            "job": jobObjectId,
            "note": document.getElementById("note").value
        }
        const url = note_exists ? `${getCookie('note_endpoint')}/${jobObjectId}` : getCookie('note_endpoint');
        const requestType = note_exists ? `PUT` : `POST`;
        try {
            await $.ajax({
                'url': url,
                'type': requestType,
                'cache': false,
                headers: {'X-CSRFToken': getCookie('csrftoken')},
                data: JSON.stringify(data),
                contentType: 'application/json; charset=utf-8',
                async: false
            })
        } catch (e) {
            console.log(JSON.parse(e.responseText)['job'][0]);
        }
    }

    const allLists = JSON.parse($.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    await refreshAfterJobOrListUpdate(allLists);
}
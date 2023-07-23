async function hideJob(job_obj_id) {
    setCookie("previously_selected_job_index", getCookie("currently_selected_job_index"))
    let data = {
        "id": job_obj_id,
        "hide": true
    }
    await updating_job_and_view(job_obj_id, data);
}
async function showJob(job_obj_id) {
    setCookie("previously_selected_job_index", getCookie("currently_selected_job_index"))
    let data = {
        "id": job_obj_id,
        "hide": false
    }
    await updating_job_and_view(job_obj_id, data);
}
async function toggle_applied(job_applied, job_obj_id) {
    setCookie("previously_selected_job_index", getCookie("currently_selected_job_index"))
    let data = {
        "id": job_obj_id,
        "applied": !job_applied
    }
    await updating_job_and_view(job_obj_id, data);
}

async function save_note(job_obj_id) {
    setCookie("currently_selected_job_id", job_obj_id);
    let data = {
        "id": job_obj_id,
        "note": document.getElementById("note").value
    }
    await updating_job_and_view(job_obj_id, data);
}
async function updating_job_and_view(job_obj_id, data){
        await $.ajax({
        'url': getCookie('update_user_job_settings').replace("user_job_info_id/", job_obj_id + "/"),
        'type': 'POST',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    const all_lists = $.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    await refreshJobView(all_lists);
}


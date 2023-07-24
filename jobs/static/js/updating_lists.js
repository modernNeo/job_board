
function refreshDeleteListDropDown(all_lists) {
    let delete_list = document.getElementById("delete_list");
    let list_delete_drop_down = document.createElement("select");
    for (let i = 0; i < all_lists.length; i++) {
        let option = document.createElement("option")
        option.value = all_lists[i].id;
        option.innerText = all_lists[i].name;
        list_delete_drop_down.appendChild(option);
    }
    list_delete_drop_down.id = 'delete_list_select_tag';
    delete_list.replaceChildren();
    if (all_lists.length > 0) {
        let delete_label = document.createElement("label");
        delete_label.textContent = "List to delete: ";
        delete_list.appendChild(delete_label);
        delete_list.appendChild(list_delete_drop_down);

        let delete_list_button = document.createElement("button");
        delete_list_button.textContent = "Delete";
        delete_list_button.setAttribute("onclick", "deleteList()");
        delete_list.appendChild(delete_list_button);
    }
    delete_list.append(document.createElement("br"), document.createElement("br"))
}


async function showListButton(all_lists) {
    document.getElementById('lists_buttons').replaceChildren();
    let job_button = document.createElement("button");
    job_button.setAttribute("onclick", "showAllJobs()");
    job_button.textContent = "All Jobs";
    document.getElementById('lists_buttons').appendChild(job_button);
    job_button = document.createElement("button");
    job_button.setAttribute("onclick", "showInbox()");
    job_button.textContent = "Inbox";
    document.getElementById('lists_buttons').appendChild(job_button);
    job_button = document.createElement("button");
    job_button.setAttribute("onclick", "showArchived()");
    job_button.textContent = "Archived";
    document.getElementById('lists_buttons').appendChild(job_button);
    for (let i = 0; i < all_lists.length; i++) {
        let job_button = document.createElement("button");
        job_button.setAttribute("onclick", "showList(" + all_lists[i].id + ")");
        job_button.textContent = all_lists[i].name;
        document.getElementById('lists_buttons').appendChild(job_button);
    }
}


async function createNewList(url) {
    let data = {
        "name": document.getElementById("new_list_name").value
    }
    document.getElementById("new_list_name").value = '';
    $.ajax({
        "url": url,
        "type": 'POST',
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
    await refreshDeleteListDropDown(all_lists);
    await refresh_after_job_or_list_update(all_lists);
}

async function deleteList() {
    const item_to_delete_index = document.getElementById("delete_list_select_tag").value
    $.ajax({
        "url": `${getCookie('lists_endpoint')}${item_to_delete_index}`,
        "type": 'DELETE',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
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
    await refreshDeleteListDropDown(all_lists);
    await refresh_after_job_or_list_update(all_lists);
}
// async function addJobToList(job_id, list_id) {
//     $.ajax({
//             'url': `${getCookie('item_endpoint')}?job_id=${job_id}&list_id=${list_id}`,
//             'type': 'POST',
//             'cache': false,
//             headers: {'X-CSRFToken': getCookie('csrftoken')},
//             contentType: 'application/json; charset=utf-8',
//             async: false
//         }
//     )
//         const all_lists = $.ajax({
//         'url': `${getCookie('lists_endpoint')}`,
//         'type': 'GET',
//         'cache': false,
//         headers: {'X-CSRFToken': getCookie('csrftoken')},
//         contentType: 'application/json; charset=utf-8',
//         async: false
//     })
//     await refreshJobView(all_lists);
//     await refreshDeleteList(all_lists);
// }
// async function removeJobToList(item_id) {
//     $.ajax({
//             'url': `${getCookie('item_endpoint')}${item_id}`,
//             'type': 'DELETE',
//             'cache': false,
//             headers: {'X-CSRFToken': getCookie('csrftoken')},
//             contentType: 'application/json; charset=utf-8',
//             async: false
//         }
//     )
//     const all_lists = $.ajax({
//         'url': `${getCookie('lists_endpoint')}`,
//         'type': 'GET',
//         'cache': false,
//         headers: {'X-CSRFToken': getCookie('csrftoken')},
//         contentType: 'application/json; charset=utf-8',
//         async: false
//     })
//     await refreshJobView(all_lists);
//     await refreshDeleteList(all_lists);
// }
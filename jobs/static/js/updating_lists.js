
function refreshDeleteList(all_lists) {
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
    await refreshDeleteList(all_lists);
    await refreshJobView(all_lists);
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
    await refreshDeleteList(all_lists);
    await refreshJobView(all_lists);
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
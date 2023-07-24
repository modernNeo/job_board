
function refreshDeleteListDropDown(allLists) {
    let deleteListDiv = document.getElementById("delete_list");
    let listDeleteDropDown = document.createElement("select");
    for (let i = 0; i < allLists.length; i++) {
        let option = document.createElement("option")
        option.value = allLists[i].id;
        option.innerText = allLists[i].name;
        listDeleteDropDown.appendChild(option);
    }
    listDeleteDropDown.id = 'delete_list_select_tag';
    deleteListDiv.replaceChildren();
    if (allLists.length > 0) {
        let deleteLabel = document.createElement("label");
        deleteLabel.textContent = "List to delete: ";
        deleteListDiv.appendChild(deleteLabel);
        deleteListDiv.appendChild(listDeleteDropDown);

        let deleteListButton = document.createElement("button");
        deleteListButton.textContent = "Delete";
        deleteListButton.setAttribute("onclick", "deleteList()");
        deleteListDiv.appendChild(deleteListButton);
    }
    deleteListDiv.append(document.createElement("br"), document.createElement("br"))
}


async function showListButton(allLists) {
    document.getElementById('lists_buttons').replaceChildren();
    let jobButton = document.createElement("button");
    jobButton.setAttribute("onclick", "showAllJobs()");
    jobButton.textContent = "All Jobs";
    document.getElementById('lists_buttons').appendChild(jobButton);
    jobButton = document.createElement("button");
    jobButton.setAttribute("onclick", "showInbox()");
    jobButton.textContent = "Inbox";
    document.getElementById('lists_buttons').appendChild(jobButton);
    jobButton = document.createElement("button");
    jobButton.setAttribute("onclick", "showArchived()");
    jobButton.textContent = "Archived-Legacy";
    document.getElementById('lists_buttons').appendChild(jobButton);
    for (let i = 0; i < allLists.length; i++) {
        jobButton = document.createElement("button");
        jobButton.setAttribute("onclick", "showList(" + allLists[i].id + ")");
        jobButton.textContent = allLists[i].name;
        document.getElementById('lists_buttons').appendChild(jobButton);
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
    const allLists = $.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    await refreshDeleteListDropDown(allLists);
    await refreshAfterJobOrListUpdate(allLists);
}

async function deleteList() {
    const itemToDeleteIndex = document.getElementById("delete_list_select_tag").value
    $.ajax({
        "url": `${getCookie('list_endpoint')}${itemToDeleteIndex}`,
        "type": 'DELETE',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
        const allLists = $.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    await refreshDeleteListDropDown(allLists);
    await refreshAfterJobOrListUpdate(allLists);
}
async function addJobToList(jobId, listId) {
    $.ajax({
            'url': `${getCookie('item_endpoint')}?job_id=${jobId}&list_id=${listId}`,
            'type': 'POST',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }
    )
        const allLists = $.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    await refreshDeleteListDropDown(allLists);
    await refreshAfterJobOrListUpdate(allLists);
}
async function removeJobFromList(itemObjId) {
    $.ajax({
            'url': `${getCookie('item_endpoint')}${itemObjId}`,
            'type': 'DELETE',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }
    )
    const allLists = $.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    })
    await refreshDeleteListDropDown(allLists);
    await refreshAfterJobOrListUpdate(allLists);
}

async function toggle_applied(jobAppliedState, jobObjectId, listId, itemObjectId) {
    if (jobAppliedState){
        await removeJobFromList(itemObjectId);
    }else{
        await addJobToList(jobObjectId, listId);
    }
}

async function toggle_archived(jobArchivedState, jobObjectId, listId, itemObjectId) {
    if (jobArchivedState) {
        await removeJobFromList(itemObjectId);
    } else {
        await addJobToList(jobObjectId, listId);
    }
}

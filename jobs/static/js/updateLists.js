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
    jobButton.textContent = "Archived";
    document.getElementById('lists_buttons').appendChild(jobButton);
    for (let i = 0; i < allLists.length; i++) {
        if (allLists[i].name !== "Archived") {
            jobButton = document.createElement("button");
            jobButton.setAttribute("onclick", "showList(" + allLists[i].id + ")");
            jobButton.textContent = `${allLists[i].name}-${allLists[i].number_of_jobs}`;
            document.getElementById('lists_buttons').appendChild(jobButton);
        }
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
    const allLists = JSON.parse($.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    await refreshDeleteListDropDown(allLists);
    await showListButton(allLists)
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
    const allLists = JSON.parse($.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    await refreshDeleteListDropDown(allLists);
    await showListButton(allLists)
    await refreshAfterJobOrListUpdate(allLists);
}
async function addJobToList(jobLocationRequest, objId, listId, dateAppliedOrClosed){
    let params = jobLocationRequest ? `job_location_date_posted_id=${objId}&dateAppliedOrClosed=${dateAppliedOrClosed}` : `job_id=${objId}`;
    let endpoint = jobLocationRequest ? getCookie('job_location_item_endpoint') : getCookie('job_item_endpoint');
    $.ajax({
            'url': `${endpoint}?${params}&list_id=${listId}`,
            'type': 'POST',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }
    )
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
async function removeJobFromList(jobLocationRequest, itemObjId) {
    let endpoint = jobLocationRequest ? getCookie('job_location_item_endpoint') : getCookie('job_item_endpoint');
    $.ajax({
            'url': `${endpoint}${itemObjId}`,
            'type': 'DELETE',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }
    )
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

async function toggleJobLocationSpecificDatePostedListItem(jobAppliedState, jobObjectId, listId, itemObjectId, AppliedOrClosed) {
    if (jobAppliedState){
        await removeJobFromList(true, itemObjectId);
    }else{
        await addJobToList(true, jobObjectId, listId, AppliedOrClosed);
    }
}

async function toggleArchived(jobArchivedState, jobObjectId, listId, itemObjectId) {
    if (jobArchivedState) {
        await removeJobFromList(false, itemObjectId);
    } else {
        await addJobToList(false, jobObjectId, listId, false);
    }
}

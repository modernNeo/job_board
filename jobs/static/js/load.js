function setCookie(name, value) {
    document.cookie = `${name}=${value}`;
}
function getCookie(name, value) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies_str = document.cookie;
        if (value !== undefined) {
            // as close to atomic as I can get with trying to read the value of a cookie and update it in one action
            setCookie(name, value)
        }
        const cookies = cookies_str.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                if (!isNaN(cookieValue)){
                    cookieValue = Number(cookieValue);
                }
                if (cookieValue === "null"){
                    cookieValue = null;
                }
                break;
            }
        }
    }
    return cookieValue;
}

async function browserReady() {
    clearCookies();
    setCookie("pageNumber", 1);
    const allLists = JSON.parse($.ajax({
        'url': `${getCookie('list_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    await refreshDeleteListDropDown(allLists)
    await showListButton(allLists)
    await showInbox(allLists)
}

function clearCookies() {
    setCookie("previously_selected_job_index", null);
    setCookie("previously_selected_job_ids", null);
    setCookie("currently_selected_job_id", null);
    setCookie("currently_selected_job_index", null);
    setCookie("view","inbox")
}

async function showAppliedJobs(allLists) {
    setCookie("view", "applied_jobs")
    await goToPage(allLists, 0);
}

async function goToPage(allLists, newPageDifference, listObjectId) {
    let param = '';
    if (listObjectId !== undefined) {
        param += `list=${listObjectId}`;
    } else {
        param += `${await getListFuncOrParameterOrHeader(allLists, "parameter")}`;
    }
    let numPagesInfo = JSON.parse($.ajax({
        'url': `${getCookie('num_pages_endpoint')}?${param}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    const totalNumberOfPages = numPagesInfo['total_number_of_pages']
    setCookie("total_number_of_pages", totalNumberOfPages);
    setCookie("total_number_of_jobs", numPagesInfo['total_number_of_jobs']);
    const pageNumber = getCookie("pageNumber") + newPageDifference;
    if (pageNumber < 1) {
        setCookie("pageNumber", totalNumberOfPages);
    } else if (pageNumber > totalNumberOfPages) {
        setCookie("pageNumber", 1)
    } else {
        setCookie("pageNumber", pageNumber)
    }
    param += `&page=${getCookie("pageNumber")}`;
    let listOfJobs = JSON.parse($.ajax({
        'url': `${getCookie('list_of_jobs_endpoint')}?${param}`,
        'type': 'GET',
        'cache': false,
        async: false
    }).responseText)
    await updateJobList(listOfJobs, allLists);
}

async function getListFuncOrParameterOrHeader(allLists, returnType) {
    const view = getCookie("view")
    if (view === "all_jobs") {
        return (returnType === "func") ? showAllJobs : (returnType === "parameter") ? `list=all` : `All Jobs`;
    } else if (view === "inbox") {
        return (returnType === "func") ? showInbox : (returnType === "parameter") ? `list=inbox` : `Inbox`;
    }else if (view === "archived"){
        return (returnType === "func") ? showArchived : (returnType === "parameter") ? `list=archived` : `Archived`;
    } else if (view.match(/^list_index_\d*$/)) {
        const listIndex = Number(view.slice(11));
        for (let i = 0; i < allLists.length; i++) {
            if (listIndex === allLists[i].id) {
                return (returnType === "func") ? `showList_${allLists[i].id}` : (returnType === "parameter") ? `list_id=${allLists[i].id}` : allLists[i].name;
            }
        }
    } else {
        return (returnType === "func") ? showInbox : (returnType === "parameter") ? `list=inbox` : `Inbox`;
    }
}
async function updateJobList(listOfJobs, allLists) {
    let header = document.createElement("h3");
    header.textContent = await getListFuncOrParameterOrHeader(allLists, "header");
    document.getElementById("job_list_header").replaceChildren(header);

    let lastSelectedJobId = null;
    let previouslySelectedJobIndex = getCookie("previously_selected_job_index");
    if (previouslySelectedJobIndex !== null) {
        // if the last action was to hide or show a job or mark it as applied
        setCookie("previously_selected_job_index", null);
    } else {
        // otherwise, at least try to re-select the last item that was selected
        lastSelectedJobId = getCookie("currently_selected_job_id");
    }
    let currentlySelectedJobId = null;
    let currentlySelectedJobIndex = null;
    let jobList = document.getElementById("job_list");
    jobList.replaceChildren();
    for (let i = 0; i < listOfJobs.length; i++) {
        let jobItem = document.createElement("b");
        jobItem.setAttribute("id", listOfJobs[i].id + "_list_item");
        jobItem.setAttribute("onclick", "updateSelectedJobInList(" + i + ", " + listOfJobs[i].id + ")");
        jobItem.innerHTML = listOfJobs[i].job_title + " || " + listOfJobs[i].organisation_name;
        if (listOfJobs[i].note !== null) {
            jobItem.innerHTML += ` *`;
        }
        jobItem.innerHTML += listOfJobs[i].lists;
        if (listOfJobs[i].easy_apply) {
            jobItem.style = 'background-color: green;';
        }
        jobList.append(jobItem);
        jobItem.append(document.createElement("br"))

        // if the previously selected job was marked as applied or hidden so the code will try and jump to the nearest job so the user is not
        // moved back to the top and loses their place
        let adjacentJob = (previouslySelectedJobIndex !== null && i <= previouslySelectedJobIndex)
        // if the previously selected job is still in the current list
        let previouslySelectedJob = lastSelectedJobId === listOfJobs[i].id;
        // make sure the first element is selected at least if none of the above cases end up being true
        let selectFirstItem = currentlySelectedJobId === null;
        if (adjacentJob || previouslySelectedJob || selectFirstItem) {
            currentlySelectedJobId = listOfJobs[i].id;
            currentlySelectedJobIndex = i;
        }
    }
    // will comment it out since its a bit too jarring atm and I dont want to spend time working out the kinks since its not
    // a necessity
    // if (adjacent_job_id !== null) {
    //     job_list.scrollTop = document.getElementById(adjacent_job_id + "_list_item").offsetTop - job_list.offsetTop - 20;
    // }
    if (listOfJobs.length > 0) {
        await updateSelectedJobInList(currentlySelectedJobIndex, currentlySelectedJobId, listOfJobs, allLists);
    } else {
        setCookie("currently_selected_job_id", null);
        setCookie("currently_selected_job_index", null);
        setCookie("previously_selected_job_index", null);
        document.getElementById('company_info').replaceChildren();
        document.getElementById("number_of_jobs").innerText = `Page ${getCookie("pageNumber")}/${getCookie("total_number_of_pages")} | Job 0/0`;
    }
}



async function updateSelectedJobInList(currentlySelectedJobIndex, currentlySelectedJobId, listOfJobs, allLists) {
    setCookie("currently_selected_job_id", currentlySelectedJobId);
    setCookie("currently_selected_job_index", currentlySelectedJobIndex);
    item = document.getElementById(currentlySelectedJobId + "_list_item");
    item.style = 'color: blue';
    updateCompanyPane(allLists, listOfJobs, currentlySelectedJobId);
    document.getElementById("number_of_jobs").innerText = `Page ${getCookie("pageNumber")}/${getCookie("total_number_of_pages")} | Job ${((getCookie("pageNumber") - 1) * 25) + currentlySelectedJobIndex + 1}/${getCookie("total_number_of_jobs")}`;
}

function updateCompanyPane(allLists, listOfJobs, jobObjId) {
    let job;
    if (listOfJobs === undefined) {
        job = JSON.parse($.ajax({
            'url': `${getCookie('list_of_jobs_endpoint')}${jobObjId}`,
            'type': 'GET',
            'cache': false,
            async: false
        }).responseText)
    } else {
        listOfJobs = new Map(listOfJobs.map(job => [job.id, job]))
        job = listOfJobs.get(jobObjId);
    }
    if (allLists === undefined) {
        allLists = JSON.parse($.ajax({
            'url': `${getCookie('list_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
    }
    const allListMap = new Map(allLists.map(list => [list.name, list]))
    const appliedListId = allListMap.get("Applied").id;
    const archivedListId = allListMap.get("Archived").id;

    let userSpecificItems = JSON.parse($.ajax({
            'url': `${getCookie('item_endpoint')}?job_id=${job.id}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }
    ).responseText);
    userSpecificItems = new Map(userSpecificItems.map(job_list_for_user => [job_list_for_user.list, job_list_for_user]))
    const userSpecificAppliedItem = userSpecificItems.get(appliedListId)
    const userSpecificArchivedItem = userSpecificItems.get(archivedListId);

    let appliedFunctionCall = `toggle_applied(${userSpecificAppliedItem !== undefined}, ${job.id}, ${appliedListId}`;
    if (userSpecificAppliedItem !== undefined) {
        appliedFunctionCall += `, ${userSpecificAppliedItem.id}`;
    }
    appliedFunctionCall += `)`;


    let jobPostingInfo = document.getElementById('company_info');
    jobPostingInfo.replaceChildren();
    jobPostingInfo.appendChild(addButton(appliedFunctionCall, userSpecificAppliedItem === undefined ? "Mark as Applied" : 'Mark as Un-Applied'))
    if (userSpecificItems.size > 0) {
        let archivedFunctionCall = `toggle_archived(${userSpecificArchivedItem !== undefined}, ${job.id}, ${archivedListId}`;
        if (userSpecificArchivedItem !== undefined) {
            archivedFunctionCall += `, ${userSpecificArchivedItem.id}`;
        }
        archivedFunctionCall += `)`;
        jobPostingInfo.appendChild(addButton(archivedFunctionCall, userSpecificArchivedItem === undefined ? "Archive" : 'Un-Archive'))
    }
    jobPostingInfo.append(document.createElement("br"), document.createElement("br"));
    jobPostingInfo.append(createListSelectSection(allLists, userSpecificItems, job.id), document.createElement("br"));
    jobPostingInfo.appendChild(createCompanyInfoLine("Applied : ", "none", userSpecificItems.get(appliedListId) !== undefined))
    jobPostingInfo.appendChild(createCompanyNoteInfo(job.id, job['note'], job['note'] !== null && job['note'].trim().length > 0));
    jobPostingInfo.appendChild(createCompanyTitle(job.job_title))
    jobPostingInfo.append(createLink(job.linkedin_link), document.createElement("br"), document.createElement("br"));
    jobPostingInfo.appendChild(createCompanyInfoLine("Company : ", "company_label", job.organisation_name))
    jobPostingInfo.appendChild(createCompanyInfoLine("Location: ", "location_label", job.location))
    jobPostingInfo.appendChild(createCompanyInfoLine("Remote Work Allowed : ", "remote_work_allowed_label", job.remote_work_allowed))
    jobPostingInfo.appendChild(createCompanyInfoLine("Workplace Type : ", "workplace_type_label", job.workplace_type))
    jobPostingInfo.appendChild(createCompanyInfoLine("Date Posted : ", "date_posted_label", job.date_posted))
    jobPostingInfo.appendChild(createCompanyInfoLine("Source : ", "source_label", job.source_domain))
    jobPostingInfo.appendChild(createCompanyInfoLine("Link : ", "link_label", job.organisation_name))
    let previously_selected_job_id = getCookie("previously_selected_job_id", jobObjId);
    let previously_selected_job_id_green_highlighting = getCookie("previously_selected_job_id_green_highlighting", job.easy_apply);
    if (!(previously_selected_job_id === null || previously_selected_job_id === "" || Number(previously_selected_job_id) === Number(jobObjId))) {
        try {
            let previousItem = document.getElementById(`${previously_selected_job_id}_list_item`);
            previousItem.style = (previously_selected_job_id_green_highlighting === "true") ? 'background-color: green;'  : '';
        } catch (e) {
            console.log(`could not remove highlighting for ${previously_selected_job_id}_list_item a list item due to error\n${e}`);
        }

    }
}
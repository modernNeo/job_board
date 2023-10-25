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

    let locations = JSON.parse($.ajax({
            'url': `${getCookie('job_location_endpoint')}?job_id=${job.id}`,
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

    let appliedFunctionCall = `toggleApplied(${userSpecificAppliedItem !== undefined}, ${job.id}, ${appliedListId}`;
    if (userSpecificAppliedItem !== undefined) {
        appliedFunctionCall += `, ${userSpecificAppliedItem.id}`;
    }
    appliedFunctionCall += `)`;


    let jobPostingInfo = document.getElementById('company_info');
    jobPostingInfo.replaceChildren();
    jobPostingInfo.appendChild(addButton(appliedFunctionCall, userSpecificAppliedItem === undefined ? "Mark as Applied" : 'Mark as Un-Applied'))
    if (userSpecificItems.size > 0) {
        let archivedFunctionCall = `toggleArchived(${userSpecificArchivedItem !== undefined}, ${job.id}, ${archivedListId}`;
        if (userSpecificArchivedItem !== undefined) {
            archivedFunctionCall += `, ${userSpecificArchivedItem.id}`;
        }
        archivedFunctionCall += `)`;
        jobPostingInfo.appendChild(addButton(archivedFunctionCall, userSpecificArchivedItem === undefined ? "Archive" : 'Un-Archive'))
    }
    jobPostingInfo.append(document.createElement("br"), document.createElement("br"));
    jobPostingInfo.appendChild(createCompanyNoteInfo(job.id, job['note'], job['note'] !== null && job['note'].trim().length > 0));
    jobPostingInfo.appendChild(createCompanyTitle(job.job_title))
    jobPostingInfo.appendChild(createCompanyInfoLine("Company : ", "company_label", job.company_name))
    for (let i = 0; i < locations.length; i++) {
        let message = ``;
        if (locations[i].experience_level){
            message = `${locations[i].experience_level} - `;
        }
        if (locations.length > 1) {
            message += `Easy Apply: ${locations[i].easy_apply} - `;
        }
        jobPostingInfo.append(
            createLink(`${message}${locations[i].location} - ${locations[i].date_posted}`, locations[i].job_board_link),
            createJobLocationLinkedId(locations[i].job_board_id),
            createToggleEasyApplyButton(locations[i].id)
        );
        if (locations.length > 1){
            jobPostingInfo.append(createDeleteButton(locations[i].id))
        }
        jobPostingInfo.append(document.createElement("br"), document.createElement("br"))
    }
    jobPostingInfo.append(createListSelectSection(allLists, userSpecificItems, job.id), document.createElement("br"));
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
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
    const jobClosedListId = allListMap.get("Job Closed").id;
    const archivedListId = allListMap.get("Archived").id;

    let jobLocationItems = JSON.parse($.ajax({
            'url': `${getCookie('job_location_item_endpoint')}?job_id=${job.id}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }
    ).responseText);
    const jobItems = new Map(
        (
            JSON.parse($.ajax({
                'url': `${getCookie('job_item_endpoint')}?job_id=${job.id}`,
                'type': 'GET',
                'cache': false,
                headers: {'X-CSRFToken': getCookie('csrftoken')},
                contentType: 'application/json; charset=utf-8',
                async: false
            }).responseText)
        ).map(job_list_for_user => [job_list_for_user.list, job_list_for_user])
    );
    let locations = JSON.parse($.ajax({
            'url': `${getCookie('job_location_endpoint')}?job_id=${job.id}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }
    ).responseText);
    let jobPostingInfo = document.getElementById('company_info');
    jobPostingInfo.replaceChildren();

    // adds the button to archive a job to the posting
    const userSpecificArchivedItem = jobItems.get(archivedListId);
    if (jobLocationItems.length > 0 || jobItems.size > 0) {
        let archivedFunctionCall = `toggleArchived(${userSpecificArchivedItem !== undefined}, ${job.id}, ${archivedListId}`;
        if (userSpecificArchivedItem !== undefined) {
            archivedFunctionCall += `, ${userSpecificArchivedItem.id}`;
        }
        archivedFunctionCall += `)`;
        jobPostingInfo.appendChild(addButton(archivedFunctionCall, userSpecificArchivedItem === undefined ? "Archive" : 'Un-Archive'))
    }
    // adding the job posting info to the section
    jobPostingInfo.append(document.createElement("br"), document.createElement("br"));
    jobPostingInfo.appendChild(createCompanyNoteInfo(job.id, job['note'], job['note'] !== null && job['note'].trim().length > 0));
    jobPostingInfo.appendChild(createCompanyTitle(job.job_title))
    jobPostingInfo.appendChild(createCompanyInfoLine("Company : ", "company_label", job.company_name))

    // going over each job location and adding its info to the section
    for (let i = 0; i < locations.length; i++) {
        let message = ``;
        if (locations[i].experience_level) {
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
        const appliedToJobLocation = locations[i].applied_status;
        let jobLocationAppliedFunctionCall = (
            `toggleJobLocationSpecificDatePostedListItem(${appliedToJobLocation}, ${locations[i].latest_date_posted_obj_id}, ` +
            `${appliedListId}, ${locations[i].applied_item_id})`
        );

        jobPostingInfo.append(addButton(jobLocationAppliedFunctionCall, appliedToJobLocation ? 'Remove Applied Label' : "Mark Location as Applied"))


        const closedJobLocation = locations[i].closed_status;
        let jobLocationClosedFunctionCall = (
            `toggleJobLocationSpecificDatePostedListItem(${closedJobLocation}, ${locations[i].latest_date_posted_obj_id}, ` +
            `${jobClosedListId}, ${locations[i].closed_item_id})`
        );

        jobPostingInfo.append(addButton(jobLocationClosedFunctionCall, closedJobLocation ? 'Remove Closed Label' : "Mark Location as Closed"))


        if (locations.length > 1) {
            jobPostingInfo.append(createDeleteButton(locations[i].id))
        }
        jobPostingInfo.append(document.createElement("br"), document.createElement("br"))
    }
    jobPostingInfo.append(createListSelectSection(allLists, jobItems, job.id), document.createElement("br"));
    let previously_selected_job_id = getCookie("previously_selected_job_id", jobObjId);
    let previously_selected_job_id_green_highlighting = getCookie("previously_selected_job_id_green_highlighting", job.easy_apply);
    if (!(previously_selected_job_id === null || previously_selected_job_id === "" || Number(previously_selected_job_id) === Number(jobObjId))) {
        try {
            let previousItem = document.getElementById(`${previously_selected_job_id}_list_item`);
            previousItem.style = (previously_selected_job_id_green_highlighting === "true") ? 'background-color: green;' : '';
        } catch (e) {
            console.log(`could not remove highlighting for ${previously_selected_job_id}_list_item a list item due to error\n${e}`);
        }

    }
}
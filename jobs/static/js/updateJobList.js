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
        let message = (listOfJobs[i].easy_apply) ? `${listOfJobs[i].easy_apply_date_posted}` : `${listOfJobs[i].non_easy_apply_date_posted}`;
        message += ` ${listOfJobs[i].job_board}: `;
        if (listOfJobs[i].experience_level){
            message += listOfJobs[i].experience_level + " => ";
        }
        jobItem.innerHTML = message + listOfJobs[i].job_title + " || " + listOfJobs[i].company_name;
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
    document.getElementById("number_of_jobs").innerText = (
        `Page ${getCookie("pageNumber")}/${getCookie("total_number_of_pages")} | Job ${((getCookie("pageNumber") - 1) * 25) + currentlySelectedJobIndex + 1}/ 
        Less than or Equal To Associate: [${getCookie("number_of_easy_apply_below_mid_senior_job_postings")}/${getCookie("number_of_non_easy_apply_below_mid_senior_job_postings")} Easy/Non-Easy Apply Jobs]
        Greater Than Associate: [${getCookie("number_of_easy_apply_above_associate_job_postings")}/${getCookie("number_of_non_easy_apply_above_associate_job_postings")} Easy/Non-Easy Apply Jobs]`);
}


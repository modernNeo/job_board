async function goToPage(allLists, newPageDifference, listObjectId) {
    await updateAppliedStat();
    let param = '';
    if (listObjectId !== undefined) {
        param += `list=${listObjectId}`;
    } else {
        param += `${await getListFuncOrParameterOrHeader(allLists, "parameter")}`;
    }
    let pageNumber = getCookie("pageNumber") + newPageDifference;
    let totalNumberOfPages = getCookie['total_number_of_pages']
    if (pageNumber < 1){
        pageNumber = totalNumberOfPages;
    }else if (pageNumber > totalNumberOfPages){
        pageNumber = 1;
    }
    setCookie("pageNumber", pageNumber)
    param += `&page=${getCookie("pageNumber")}`;
    const search_title = getCookie("search_title");
    const search_id = getCookie("search_id");
    if (search_title !== null){
        param += `&search_title=${search_title}`;
    }
    if (search_id !== null){
        param += `&search_id=${search_id}`;
    }
    let listOfJobsResp = JSON.parse($.ajax({
        'url': `${getCookie('list_of_jobs_endpoint')}?${param}`,
        'type': 'GET',
        'cache': false,
        async: false
    }).responseText)

    setCookie("total_number_of_pages", listOfJobsResp.total_number_of_pages);
    setCookie(
        "number_of_easy_apply_below_mid_senior_job_postings",
        listOfJobsResp.number_of_job_postings.below_mid_senior_level.easy_apply
    );
    setCookie(
        "number_of_non_easy_apply_below_mid_senior_job_postings",
        listOfJobsResp.number_of_job_postings.below_mid_senior_level.non_easy_apply
    );
    setCookie(
        "number_of_easy_apply_above_associate_job_postings",
        listOfJobsResp.number_of_job_postings.above_associated_level.easy_apply
    );
    setCookie(
        "number_of_non_easy_apply_above_associate_job_postings",
        listOfJobsResp.number_of_job_postings.above_associated_level.non_easy_apply
    );

    await updateJobList(listOfJobsResp.results, allLists);
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
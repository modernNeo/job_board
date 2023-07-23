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

async function browser_ready() {
    clearCookies();
    setCookie("page_number", 1);
    const all_lists = JSON.parse($.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    await refreshDeleteList(all_lists)
    await showInbox(all_lists)
}

function clearCookies() {
    setCookie("previously_selected_job_index", null);
    setCookie("previously_selected_job_ids", null);
    setCookie("currently_selected_job_id", null);
    setCookie("currently_selected_job_index", null);
    setCookie("view","inbox")
}

async function showAllJobs() {
    const all_lists = JSON.parse($.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    setCookie("view", "all_jobs")
    await goToPage(all_lists, 0);
}
async function showInbox(all_lists) {
    if (all_lists === undefined) {
        all_lists = JSON.parse($.ajax({
            'url': `${getCookie('lists_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
        setCookie("view", "all_jobs")
    }
    setCookie("view", "inbox")
    await goToPage(all_lists, 0);
}
async function showAppliedJobs(all_lists) {
    setCookie("view", "applied_jobs")
    await goToPage(all_lists, 0);
}
async function showList(list_obj_id, all_lists) {
    setCookie("page_number", 1)
    setCookie("view", `list_index_${list_obj_id}`);
    await goToPage(all_lists, 0, list_obj_id);
}





async function goToPage(all_lists, new_page_difference, list_obj_id) {
    document.getElementById('lists_buttons').replaceChildren();
    let job_button = document.createElement("button");
    job_button.setAttribute("onclick", "showAllJobs()");
    job_button.textContent = "All Jobs";
    document.getElementById('lists_buttons').appendChild(job_button);
    job_button = document.createElement("button");
    job_button.setAttribute("onclick", "showInbox()");
    job_button.textContent = "Inbox";
    document.getElementById('lists_buttons').appendChild(job_button);
    console.log(all_lists);
    for (let i = 0; i < all_lists.length; i++) {
        let job_button = document.createElement("button");
        job_button.setAttribute("onclick", "showList(" + all_lists[i].id + ")");
        job_button.textContent = all_lists[i].name;
        document.getElementById('lists_buttons').appendChild(job_button);
    }

    let param = '';
    if (list_obj_id !== undefined) {
        param += `list=${list_obj_id}`;
    } else {
        param += `${await getListFuncOrParameterOrHeader(all_lists, "parameter")}`;
    }
    console.log(`list_of_jobs_param[${param}]`);
    let num_pages_info = JSON.parse($.ajax({
        'url': `${getCookie('num_pages_endpoint')}?${param}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        async: false
    }).responseText)
    const total_number_of_pages = num_pages_info['total_number_of_pages']
    setCookie("total_number_of_pages", total_number_of_pages);
    setCookie("total_number_of_jobs", num_pages_info['total_number_of_jobs']);
    const page_number = getCookie("page_number") + new_page_difference;
    if (page_number < 1) {
        setCookie("page_number", total_number_of_pages);
    } else if (page_number > total_number_of_pages) {
        setCookie("page_number", 1)
    } else {
        setCookie("page_number", page_number)
    }
    param += `&page=${getCookie("page_number")}`;
    let list_of_jobs = JSON.parse($.ajax({
        'url': `${getCookie('list_of_jobs')}?${param}`,
        'type': 'GET',
        'cache': false,
        async: false
    }).responseText)
    await updateJobList(list_of_jobs, all_lists);
}

async function getListFuncOrParameterOrHeader(all_lists, return_type) {
    const view = getCookie("view")
    if (view === "all_jobs") {
        return (return_type === "func") ? showAllJobs : (return_type === "parameter") ? `list=all` : `All Jobs`;
    } else if (view === "inbox") {
        return (return_type === "func") ? showInbox : (return_type === "parameter") ? `list=inbox` : `Inbox`;
    } else if (view.match(/^list_index_\d*$/)) {
        const list_index = Number(view.slice(11));
        for (let i = 0; i < all_lists.length; i++) {
            if (list_index === all_lists[i].id) {
                return (return_type === "func") ? `showList_${all_lists[i].id}` : (return_type === "parameter") ? `list_id=${all_lists[i].id}` : all_lists[i].name;
            }
        }
    } else {
        return (return_type === "func") ? showInbox : (return_type === "parameter") ? `list=inbox` : `Inbox`;
    }
}
async function updateJobList(list_of_jobs, all_lists) {
    let header = document.createElement("h3");
    header.textContent = await getListFuncOrParameterOrHeader(all_lists, "header");
    document.getElementById("job_list_header").replaceChildren(header);

    let last_selected_job_id = null;
    let previously_selected_job_index = getCookie("previously_selected_job_index");
    if (previously_selected_job_index !== null) {
        // if the last action was to hide or show a job or mark it as applied
        setCookie("previously_selected_job_index", null);
    } else {
        // otherwise, at least try to re-select the last item that was selected
        last_selected_job_id = getCookie("currently_selected_job_id");
    }
    let currently_selected_job_id = null;
    let currently_selected_job_index = null;
    let job_list = document.getElementById("job_list");
    job_list.replaceChildren();
    for (let i = 0; i < list_of_jobs.length; i++) {
        let job_item = document.createElement("b");
        job_item.setAttribute("id", list_of_jobs[i].id + "_list_item");
        job_item.setAttribute("onclick", "updateSelectedJobInList(" + i + ", " + list_of_jobs[i].id + ")");
        job_item.innerHTML = list_of_jobs[i].job_title + " || " + list_of_jobs[i].organisation_name;
        if (list_of_jobs[i].note !== null) {
            job_item.innerHTML += ` *`;
        }
        job_item.innerHTML += list_of_jobs[i].lists;
        job_list.append(job_item);
        job_item.append(document.createElement("br"))

        // if the previously selected job was marked as applied or hidden so the code will try and jump to the nearest job so the user is not
        // moved back to the top and loses their place
        let adjacent_job = (previously_selected_job_index !== null && i <= previously_selected_job_index)
        // if the previously selected job is still in the current list
        let previously_selected_job = last_selected_job_id === list_of_jobs[i].id;
        // make sure the first element is selected at least if none of the above cases end up being true
        let select_first_item = currently_selected_job_id === null;
        if (adjacent_job || previously_selected_job || select_first_item) {
            currently_selected_job_id = list_of_jobs[i].id;
            currently_selected_job_index = i;
        }
    }
    // will comment it out since its a bit too jarring atm and I dont want to spend time working out the kinks since its not
    // a necessity
    // if (adjacent_job_id !== null) {
    //     job_list.scrollTop = document.getElementById(adjacent_job_id + "_list_item").offsetTop - job_list.offsetTop - 20;
    // }
    if (list_of_jobs.length > 0) {
        await updateSelectedJobInList(currently_selected_job_index, currently_selected_job_id, list_of_jobs, all_lists);
    } else {
        setCookie("currently_selected_job_id", null);
        setCookie("currently_selected_job_index", null);
        setCookie("previously_selected_job_index", null);
        document.getElementById('company_info').replaceChildren();
        document.getElementById("number_of_jobs").innerText = `Page ${getCookie("page_number")}/${getCookie("total_number_of_pages")} | Job 0/0`;
    }
}



async function updateSelectedJobInList(currently_selected_job_index, currently_selected_job_id, list_of_jobs, all_lists) {
    setCookie("currently_selected_job_id", currently_selected_job_id);
    setCookie("currently_selected_job_index", currently_selected_job_index);
    item = document.getElementById(currently_selected_job_id + "_list_item");
    console.log(`adding highlighting to ${currently_selected_job_id}_list_item`);
    item.style = 'color: blue';
    updateCompanyPane(all_lists, list_of_jobs, currently_selected_job_id);
    document.getElementById("number_of_jobs").innerText = `Page ${getCookie("page_number")}/${getCookie("total_number_of_pages")} | Job ${((getCookie("page_number") - 1) * 25) + currently_selected_job_index + 1}/${getCookie("total_number_of_jobs")}`;
}

function updateCompanyPane(all_lists, list_of_jobs, job_obj_id) {
    let job = null;
    if (list_of_jobs === undefined) {
        job = JSON.parse($.ajax({
            'url': `${getCookie('list_of_jobs')}${job_obj_id}`,
            'type': 'GET',
            'cache': false,
            async: false
        }).responseText)
    } else {
        list_of_jobs = new Map(list_of_jobs.map(job => [job.id, job]))
        job = list_of_jobs.get(job_obj_id);
    }
    if (all_lists === undefined) {
        all_lists = JSON.parse($.ajax({
            'url': `${getCookie('lists_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            async: false
        }).responseText)
    }
    $.ajax({
        'url': getCookie('get_user_job_settings').replace("user_job_info_id/", job.id + "/"),
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        success: function (user_job_settings) {
            $.ajax({
                    'url': `${getCookie('item_endpoint')}?job_id=${job.id}`,
                    'type': 'GET',
                    'cache': false,
                    headers: {'X-CSRFToken': getCookie('csrftoken')},
                    contentType: 'application/json; charset=utf-8',
                    success: function (job_lists_for_user) {
                        try {
                            const visible_job = !user_job_settings['hide'];
                            let company_info = document.getElementById('company_info');
                            company_info.replaceChildren();
                            company_info.appendChild(addButton(visible_job ? "hideJob(" + job.id + ")" : "showJob(" + job.id + ")", visible_job ? 'Hide Job' : 'Show Job'))
                            company_info.appendChild(addButton("toggle_applied(" + user_job_settings['applied'] + ", " + job.id + ")", user_job_settings['applied'] ? 'Mark as Unapplied' : "Mark as Applied"))
                            company_info.append(document.createElement("br"), document.createElement("br"));
                            company_info.append(createListSelectSection(all_lists, job_lists_for_user, job.id), document.createElement("br"));
                            company_info.appendChild(createCompanyInfoLine("Applied : ", "none", user_job_settings['applied']))
                            company_info.appendChild(createCompanyNoteInfo(job.id, user_job_settings['note']));
                            company_info.appendChild(createCompanyTitle(job.job_title))
                            company_info.appendChild(createCompanyInfoLine("Company : ", "company_label", job.organisation_name))
                            company_info.appendChild(createCompanyInfoLine("Location: ", "location_label", job.location))
                            company_info.appendChild(createCompanyInfoLine("Remote Work Allowed : ", "remote_work_allowed_label", job.remote_work_allowed))
                            company_info.appendChild(createCompanyInfoLine("Workplace Type : ", "workplace_type_label", job.workplace_type))
                            company_info.appendChild(createCompanyInfoLine("Date Posted : ", "date_posted_label", job.date_posted))
                            company_info.appendChild(createCompanyInfoLine("Source : ", "source_label", job.source_domain))
                            company_info.appendChild(createCompanyInfoLine("Link : ", "link_label", job.organisation_name))
                            company_info.appendChild(createLink(job.linkedin_link));
                        } catch (e) {
                            console.log(e);
                        }
                        let previously_selected_job_id = getCookie("previously_selected_job_ids", job_obj_id);
                        if (!(previously_selected_job_id === null || previously_selected_job_id === "" || Number(previously_selected_job_id) === Number(job_obj_id))) {
                            try {
                                console.log(`removing highlighting for ${previously_selected_job_id}_list_item`);
                                let previous_item = document.getElementById(`${previously_selected_job_id}_list_item`);
                                previous_item.style = '';
                                console.log(`removed highlighting for ${previously_selected_job_id}_list_item`);
                            } catch (e) {
                                console.log(`could not remove highlighting for ${previously_selected_job_id}_list_item a list item due to error\n${e}`);
                            }

                        }
                    }
                }
            )
        }
    });
}


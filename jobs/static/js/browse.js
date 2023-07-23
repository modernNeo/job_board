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
function browser_ready() {
    clearCookies();
    setCookie("page_number", 1);
    showInbox()
    refreshDeleteList()
}

function viewParameterOrFunction(view, return_type) {
    if (view === "all_jobs") {
        return (return_type === "func") ? showAllJobs : (return_type === "parameter") ? `list=all` : `All Jobs`;
    } else if (view === "inbox") {
        return (return_type === "func") ? showInbox : (return_type === "parameter") ? `list=inbox` : `Inbox`;
    } else if (view.match(/^list_index_\d*$/)) {
        $.ajax({
            'url': `${getCookie('lists_endpoint')}`,
            'type': 'GET',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            success: function (all_lists) {
                const list_index = Number(view.slice(11));
                for (let i = 0; i < all_lists.length; i++) {
                    if (list_index === all_lists[i].id) {
                        if (return_type === "header") {
                            let header = document.createElement("h3");
                            header.textContent = all_lists[i].name;
                            document.getElementById("job_list_header").replaceChildren(header);
                        }
                        return (return_type === "func") ? `showList_${all_lists[i].id}` : (return_type === "parameter") ? `list_id=${all_lists[i].id}` : all_lists[i].name;
                    }
                }
            }
        })
    } else {
        return (return_type === "func") ? showInbox : (return_type === "parameter") ? `list=inbox` : `Inbox`;
    }
}
async function refreshJobView() {
    const view = getCookie("view")
    let func = await viewParameterOrFunction(view, "func");
    if (typeof func === "function") {
        func()
    } else {
        showList(Number(func.slice(9)));
    }
}
function getParameterForView() {
    const view = getCookie("view")
    return viewParameterOrFunction(view, "parameter");
}
function showAllJobs() {
    setCookie("view", "all_jobs")
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"));
}
function showInbox() {
    setCookie("view", "inbox")
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"));
}
function showAppliedJobs() {
    setCookie("view", "applied_jobs")
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"));
}
function showList(list_index) {
    setCookie("page_number", 1)
    setCookie("view",`list_index_${list_index}`);
    const list_of_jobs = getCookie('list_of_jobs');
    console.log(`list_index=${list_index}`);
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"), list_index);
}



function showVisibleJobs() {
    setCookie("view","inbox")
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"));
}

function showHiddenJobs() {
    setCookie("view","hidden_jobs")
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"));
}

function goToPage(list_of_jobs_url, params, page_number, list_id) {
    document.getElementById('lists_buttons').replaceChildren();
    $.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        success: function (response) {
            let job_button = document.createElement("button");
            job_button.setAttribute("onclick", "showAllJobs()");
            job_button.textContent = "All Jobs";
            document.getElementById('lists_buttons').appendChild(job_button);
            job_button = document.createElement("button");
            job_button.setAttribute("onclick", "showInbox()");
            job_button.textContent = "Inbox";
            document.getElementById('lists_buttons').appendChild(job_button);
            for (let i = 0; i < response.length; i++) {
                let job_button = document.createElement("button");
                job_button.setAttribute("onclick", "showList(" + response[i].id + ")");
                job_button.textContent = response[i].name;
                document.getElementById('lists_buttons').appendChild(job_button);
            }
        }
    })

    let list_of_jobs_param = '';
    let num_pages_param = '';
    if (list_id !== undefined) {
        list_of_jobs_param += `list=${list_id}`;
        num_pages_param += `list=${list_id}`;
    }else{
        list_of_jobs_param += `${params}`;
        num_pages_param += `${params}`;
    }
    console.log(`list_id[${list_id}]`);
    console.log(`params[${params}]`);
    console.log(`list_of_jobs_param[${list_of_jobs_param}]`);
    console.log(`num_pages_param[${num_pages_param}]`);
    $.ajax({
        'url': `${getCookie('num_pages_endpoint')}?${num_pages_param}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        success: function (response) {
            response = JSON.parse(response);
            const total_number_of_pages = response['total_number_of_pages']
            setCookie("total_number_of_pages", total_number_of_pages);
            setCookie("total_number_of_jobs", response['total_number_of_jobs']);
            if (page_number < 1) {
                setCookie("page_number", total_number_of_pages);
            } else if (page_number > total_number_of_pages) {
                setCookie("page_number", 1)
            } else {
                setCookie("page_number", page_number)
            }
            list_of_jobs_param += `&page=${getCookie("page_number")}`;
            $.ajax({
                'url': `${list_of_jobs_url}?${list_of_jobs_param}`,
                'type': 'GET',
                'cache': false,
                success: function (jobs) {
                    updateJobList(jobs);
                }
            });
        }
    });
}
function updateJobList(jobs) {
    let header = document.createElement("h3");
    const view = getCookie("view")
    let ret = viewParameterOrFunction(view, "header");
    console.log(`ret=${ret}`);
    header.textContent = ret;
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
    for (let i = 0; i < jobs.length; i++) {
        let job_item = document.createElement("b");
        job_item.setAttribute("id", jobs[i].id + "_list_item");
        job_item.setAttribute("onclick", "updateSelectedJobInList(" + i + ", " + jobs[i].id + ")");
        job_item.innerHTML = jobs[i].job_title + " || " + jobs[i].organisation_name;
        if (jobs[i].note !== null){
            job_item.innerHTML += ` *`;
        }
        job_item.innerHTML += jobs[i].lists;
        job_list.append(job_item);
        job_item.append(document.createElement("br"))

        // if the previously selected job was marked as applied or hidden so the code will try and jump to the nearest job so the user is not
        // moved back to the top and loses their place
        let adjacent_job = (previously_selected_job_index !== null && i <= previously_selected_job_index)
        // if the previously selected job is still in the current list
        let previously_selected_job = last_selected_job_id === jobs[i].id;
        // make sure the first element is selected at least if none of the above cases end up being true
        let select_first_item = currently_selected_job_id === null;
        if (adjacent_job || previously_selected_job || select_first_item) {
            currently_selected_job_id = jobs[i].id;
            currently_selected_job_index = i;
        }
    }
    // will comment it out since its a bit too jarring atm and I dont want to spend time working out the kinks since its not
    // a necessity
    // if (adjacent_job_id !== null) {
    //     job_list.scrollTop = document.getElementById(adjacent_job_id + "_list_item").offsetTop - job_list.offsetTop - 20;
    // }
    if (jobs.length > 0) {
        updateSelectedJobInList(currently_selected_job_index, currently_selected_job_id, jobs);
    } else {
        setCookie("currently_selected_job_id", null);
        setCookie("currently_selected_job_index", null);
        setCookie("previously_selected_job_index", null);
        document.getElementById('company_info').replaceChildren();
        document.getElementById("number_of_jobs").innerText = `Page ${getCookie("page_number")}/${getCookie("total_number_of_pages")} | Job 0/0`;
    }
}
function updateSelectedJobInList(currently_selected_job_index, currently_selected_job_id, jobs) {
    setCookie("currently_selected_job_id", currently_selected_job_id);
    setCookie("currently_selected_job_index", currently_selected_job_index);
    item = document.getElementById(currently_selected_job_id + "_list_item");
    console.log(`adding highlighting to ${currently_selected_job_id}_list_item`);
    item.style = 'color: blue';
    let param = getParameterForView();
    if (jobs === undefined) {
        $.ajax({
            'url': `${getCookie('list_of_jobs')}?${param}&page=${getCookie("page_number")}`,
            'type': 'GET',
            'cache': false,
            success: function (jobs) {
                updateCompanyPane(jobs, currently_selected_job_id);
                document.getElementById("number_of_jobs").innerText = `Page ${getCookie("page_number")}/${getCookie("total_number_of_pages")} | Job ${((getCookie("page_number")-1) * 25) + currently_selected_job_index+1}/${getCookie("total_number_of_jobs")}`;
            }
        });
    } else {
        updateCompanyPane(jobs, currently_selected_job_id);
        document.getElementById("number_of_jobs").innerText = `Page ${getCookie("page_number")}/${getCookie("total_number_of_pages")} | Job ${((getCookie("page_number")-1) * 25) + currently_selected_job_index+1}/${getCookie("total_number_of_jobs")}`;
    }
}
function addButton(function_call, string){
    let button = document.createElement("button");
    button.setAttribute("onclick", function_call);
    button.innerHTML = string;
    return button;
}
function createCompanyNoteInfo(job_obj_id, note){
    let company_info = document.createElement("company_info_note")
    let company_label = document.createElement("label");
    company_label.style.fontWeight = 'bold';
    company_label.innerHTML = "Note : ";
    company_info.appendChild(company_label);

    let company_input = document.createElement("input");
    company_input.type = "text";
    company_input.setAttribute("onfocusout", "save_note("+job_obj_id+")");
    company_input.setAttribute("id", "note");
    company_input.value = note;
    company_info.appendChild(company_input);
    company_info.appendChild(document.createElement("br"))
    return company_info;

}
function createCompanyTitle(company_title){
    header = document.createElement("h2");
    header.innerHTML = company_title;
    return header;
}
function createListSelectSection(lists, job_lists_for_user, job_id) {
    let job_list = document.createElement("div");
    job_lists_for_user = new Map(job_lists_for_user.map(job_list_for_user => [job_list_for_user.list, job_list_for_user]))
    for (let i = 0; i < lists.length; i++) {
        let option = document.createElement("input");
        option.setAttribute("type", "checkbox");
        option.checked = job_lists_for_user.get(lists[i].id) !== undefined;
        option.id = `job_list_${lists[i].id}`;
        if (option.checked){
            option.setAttribute("onclick", "removeJobToList(" + job_lists_for_user.get(lists[i].id).id + ")");
        }else {
            option.setAttribute("onclick", "addJobToList(" + job_id + ", " + lists[i].id + ")");
        }
        job_list.append(option);
        let option_label = document.createElement("label");
        option_label.setAttribute("for", `job_list_${lists[i].id}`);
        option_label.textContent = lists[i].name;
        job_list.append(option_label);
    }
    return job_list;
}

function createCompanyInfoLine(label, p_tag_id, value){
    let company_info = document.createElement(`company_info_${p_tag_id}`)
    let company_label = document.createElement("label");
    company_label.style.fontWeight = 'bold';
    company_label.innerHTML = label;
    company_info.appendChild(company_label);

    let company_input = document.createElement("p");
    company_input.innerHTML = value;
    company_input.setAttribute("id", p_tag_id)
    company_info.appendChild(company_input);
    return company_info;

}
function createLink(link) {
    let linkElement = document.createElement("a");
    linkElement.href = link;
    linkElement.target = '_blank';
    linkElement.innerHTML = link;
    return linkElement;
}
function updateCompanyPane(jobs, job_obj_id) {
    jobs = new Map(jobs.map(job => [job.id, job]))
    const job = jobs.get(job_obj_id);
    $.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        success: function (all_lists) {
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
    })
}
function hideJob(job_obj_id) {
    setCookie("previously_selected_job_index",getCookie("currently_selected_job_index"))
    let data = {
        "id" : job_obj_id,
        "hide" : true
    }
    $.ajax({
        'url': getCookie('update_user_job_settings').replace("user_job_info_id/", job_obj_id + "/"),
        'type': 'POST',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        data : JSON.stringify(data),
        contentType : 'application/json; charset=utf-8',
        success: function () {
            refreshJobView();
        }
    });
}
function showJob(job_obj_id) {
    setCookie("previously_selected_job_index",getCookie("currently_selected_job_index"))
    let data = {
        "id": job_obj_id,
        "hide": false
    }
    $.ajax({
        'url': getCookie('update_user_job_settings').replace("user_job_info_id/", job_obj_id + "/"),
        'type': 'POST',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
        success: function () {
            refreshJobView();
        }
    });
}
function toggle_applied(job_applied, job_obj_id) {
    setCookie("previously_selected_job_index",getCookie("currently_selected_job_index"))
    let data = {
        "id": job_obj_id,
        "applied": !job_applied
    }
    $.ajax({
        'url': getCookie('update_user_job_settings').replace("user_job_info_id/", job_obj_id + "/"),
        'type': 'POST',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
        success: function () {
            refreshJobView()
        }
    });
}
function clearCookies() {
    setCookie("previously_selected_job_index", null);
    setCookie("previously_selected_job_ids", null);
    setCookie("currently_selected_job_id", null);
    setCookie("currently_selected_job_index", null);
    setCookie("view","inbox")
}
function save_note(job_obj_id){
    setCookie("currently_selected_job_id", job_obj_id);
    let data = {
        "id": job_obj_id,
        "note": document.getElementById("note").value
    }
    $.ajax({
        'url': getCookie('update_user_job_settings').replace("user_job_info_id/", job_obj_id + "/"),
        'type': 'POST',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
        success: function () {
            refreshJobView()
        }
    });
}

function goToPreviousPage() {
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number")-1);

}
function goToNextPage() {
    const list_of_jobs = getCookie('list_of_jobs');
    const view = getCookie("view");
    console.log(`list_index=${view}`);
    const list_id = view.match(/^list_index_\d*$/) ? Number(view.slice(11)) : view;
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number")+1, list_id);
}
function createNewList(url){
    let data = {
        "name": document.getElementById("new_list_name").value
    }
    document.getElementById("new_list_name").value = '';
    $.ajax({
        "url" : url,
        "type" : 'POST',
        'cache' : false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
        success: function (){
            refreshJobView();
            refreshDeleteList();
        }
    })

}
function refreshDeleteList() {
    $.ajax({
        'url': `${getCookie('lists_endpoint')}`,
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        success: function (all_lists) {
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
    })
}
function deleteList() {
    const item_to_delete_index = document.getElementById("delete_list_select_tag").value
        $.ajax({
        "url" : `${getCookie("lists_endpoint")}${item_to_delete_index}`,
        "type" : 'DELETE',
        'cache' : false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        success: function (){
            refreshJobView();
            refreshDeleteList();
        }
    })
}
function addJobToList(job_id, list_id) {
    $.ajax({
            'url': `${getCookie('item_endpoint')}?job_id=${job_id}&list_id=${list_id}`,
            'type': 'POST',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            success: function () {
                refreshJobView();
            }
        }
    )
}
function removeJobToList(item_id){
        $.ajax({
            'url': `${getCookie('item_endpoint')}${item_id}`,
            'type': 'DELETE',
            'cache': false,
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            contentType: 'application/json; charset=utf-8',
            success: function () {
                refreshJobView();
            }
        }
    )
}
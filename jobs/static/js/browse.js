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
    showVisibleJobs()
}
function refreshJobView() {
    const view = getCookie("view")
    if (view === "applied_jobs") {
        showAppliedJobs();
    } else if (view === "hidden_jobs") {
        showHiddenJobs();
    } else {
        showVisibleJobs();
    }

}
function getParameterForView(){
    const view = getCookie("view")
    if (view === "applied_jobs") {
        return `applied=true`;
    } else if (view === "hidden_jobs") {
        return `hidden=true`;
    } else {
        return `visible=true`;
    }
}
function showVisibleJobs() {
    setCookie("view","visible_jobs")
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"));
}
function showHiddenJobs() {
    setCookie("view","hidden_jobs")
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"));
}
function showAppliedJobs() {
    setCookie("view", "applied_jobs")
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"));
}
function goToPage(list_of_jobs_url, param, page_number, list_id) {
    $.ajax({
        'url' : `${getCookie('lists_endpoint')}`,
        'type' : 'GET',
        'cache' : false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        success: function (response) {
            for (let i = 0; i < response.length; i++){
                let job_button = document.createElement("button");
                job_button.setAttribute("onclick", "showList("+response[i].id+")");
                job_button.textContent = response[i].name;
                document.getElementById('lists').appendChild(job_button);
            }
            console.log(response);
        }
    })
    param = `${param}&page=${getCookie("page_number")}`
    if (list_id !== undefined){
        param += `&list=${list_id}`;
    }
    $.ajax({
        'url': `${getCookie('num_pages_endpoint')}?${param}`,
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
            $.ajax({
                'url': `${list_of_jobs_url}?${param}`,
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
    if (view === "applied_jobs") {
        header.textContent = "Applied Jobs";
    } else if (view === "hidden_jobs") {
        header.textContent = "Hidden Jobs";
    } else {
        header.textContent = "Jobs";
    }
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
        'url': getCookie('get_user_job_settings').replace("user_job_info_id/", job.id + "/"),
        'type': 'GET',
        'cache': false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        contentType: 'application/json; charset=utf-8',
        success: function (resp) {
            try {
                const visible_job = !resp['hide'];
                let company_info = document.getElementById('company_info');
                company_info.replaceChildren();
                company_info.appendChild(addButton(visible_job ? "hideJob(" + job.id+")" : "showJob(" + job.id+")", visible_job ? 'Hide Job' : 'Show Job'))
                company_info.appendChild(addButton("toggle_applied(" + resp['applied'] + ", "+job.id+")", resp['applied'] ? 'Mark as Unapplied' : "Mark as Applied"))
                company_info.append(document.createElement("br"), document.createElement("br"));
                company_info.appendChild(createCompanyInfoLine("Applied : ", "none", resp['applied']))
                company_info.appendChild(createCompanyNoteInfo(job.id, resp['note']));
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
    });
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
    setCookie("view","visible_jobs")
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
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number")+1);
}
function createNewList(url){
    let data = {
        "name": document.getElementById("new_list_name").value
    }
    $.ajax({
        "url" : url,
        "type" : 'POST',
        'cache' : false,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
        success: function (list_info){
            console.log(list_info);
            refreshJobView();
        }
    })

}
function showList(list_index) {
    console.log(`showList-${list_index}`);
    setCookie("view",list_index);
    const list_of_jobs = getCookie('list_of_jobs');
    goToPage(list_of_jobs, getParameterForView(), getCookie("page_number"), list_index);
}
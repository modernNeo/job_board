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
                break;
            }
        }
    }
    return cookieValue === "null" ? null : cookieValue;
}
function browser_ready() {
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
function showVisibleJobs() {
    setCookie("view","visible_jobs")
    $.ajax({
        'url': getCookie('list_of_jobs'),
        'type': 'GET',
        'cache': false,
        success: function (jobs) {
            updateJobList(jobs);
        }
    });

}
function showHiddenJobs() {
    setCookie("view","hidden_jobs")
    $.ajax({
        'url': getCookie('list_of_jobs')+"?hidden=true",
        'type': 'GET',
        'cache': false,
        success: function (jobs) {
            updateJobList(jobs);
        }
    });
}
function showAppliedJobs() {
    setCookie("view","applied_jobs")
    $.ajax({
        'url': getCookie('list_of_jobs')+"?applied=true",
        'type': 'GET',
        'cache': false,
        success: function (jobs) {
            updateJobList(jobs);
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

    let index_of_previously_select_job = getCookie("index_of_previously_select_job") === null ? null : Number(getCookie("index_of_previously_select_job"));
    let id_for_new_job_to_select = null;
    let db_id_for_new_job_to_select=null;
    let last_selected_job;
    if (index_of_previously_select_job !== null) {
        setCookie("index_of_previously_select_job", null);
    } else {
        last_selected_job = Number(getCookie("selected_job_id"));
    }
    let index_for_new_job_to_select = 0;
    let job_list = document.getElementById("job_list");
    job_list.replaceChildren();
    for (let i = 0; i < jobs.length; i++) {
        var job_item = document.createElement("b");
        job_item.setAttribute("id", jobs[i].id + "_list_item");
        job_item.setAttribute("onclick", "updateSelectedJobInList(" + jobs[i].job_id + ", " + i + ", "+jobs[i].id+")");
        job_item.innerHTML = jobs[i].job_title + " || " + jobs[i].organisation_name;
        job_list.append(job_item);
        job_item.append(document.createElement("br"))

        // if the previously selected job was marked as applied or hidden so the code will try and jump to the nearest job so the user is not
        // moved back to the top and loses their place
        let adjacent_job = (index_of_previously_select_job !== null && i <= index_of_previously_select_job)
        // if the previously selected job is still in the current list
        let previously_select_job = last_selected_job === jobs[i].job_id;
        // make sure the first element is selected at least if none of the above cases end up being true
        let select_first_item = id_for_new_job_to_select === null;
        if (adjacent_job || previously_select_job || select_first_item ) {
            id_for_new_job_to_select = jobs[i].job_id;
            db_id_for_new_job_to_select = jobs[i].id;
            index_for_new_job_to_select = i;
        }
    }
    // will comment it out since its a bit too jarring atm and I dont want to spend time working out the kinks since its not
    // a necessity
    // if (id_for_new_job_to_select !== null) {
    //     job_list.scrollTop = document.getElementById(id_for_new_job_to_select + "_list_item").offsetTop - job_list.offsetTop - 20;
    // }
    if (jobs.length > 0) {
        updateSelectedJobInList(id_for_new_job_to_select, index_for_new_job_to_select, db_id_for_new_job_to_select, jobs);
    } else {
        setCookie("selected_job_id", null);
        setCookie("selected_job_index", null);
        setCookie("index_of_previously_select_job", null);
        document.getElementById('company_info').replaceChildren();
        document.getElementById("number_of_jobs").innerText = "0/0 jobs";
    }
}
function updateSelectedJobInList(job_id, index_of_job_in_list, job_obj_id, jobs) {
    setCookie("selected_job_id", job_obj_id);
    setCookie("selected_job_index", index_of_job_in_list);
    item = document.getElementById(job_obj_id + "_list_item");
    console.log(`adding highlighting to ${job_obj_id}_list_item`);
    item.style = 'color: blue';
    const view = getCookie("view")
    let param = ""
    if (view === "applied_jobs") {
        param = "?applied=true"
    } else if (view === "hidden_jobs") {
        param = "?hidden=true"
    }
    if (jobs === undefined) {
        $.ajax({
            'url': getCookie('list_of_jobs') + `${param}`,
            'type': 'GET',
            'cache': false,
            success: function (jobs) {
                updateCompanyPane(jobs, job_obj_id);
                document.getElementById("number_of_jobs").innerText = index_of_job_in_list + 1 + "/" + jobs.length + " jobs";
            }
        });
    } else {
        updateCompanyPane(jobs, job_obj_id);
        document.getElementById("number_of_jobs").innerText = index_of_job_in_list + 1 + "/" + jobs.length + " jobs";
    }
}
function addButton(function_call, string){
    let button = document.createElement("button");
    button.setAttribute("onclick", function_call);
    button.innerHTML = string;
    return button;
}
function createCompanyNoteInfo(job_id, job_obj_id, note){
    let company_info = document.createElement("company_info_note")
    let company_label = document.createElement("label");
    company_label.style.fontWeight = 'bold';
    company_label.innerHTML = "Note : ";
    company_info.appendChild(company_label);

    let company_input = document.createElement("input");
    company_input.type = "text";
    company_input.setAttribute("onfocusout", "save_note("+job_id+", "+job_obj_id+")");
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
                company_info.appendChild(addButton(visible_job ? "hideJob(" + job.job_id + ", "+job.id+")" : "showJob(" + job.job_id + ", "+job.id+")", visible_job ? 'Hide Job' : 'Show Job'))
                company_info.appendChild(addButton("toggle_applied(" + job.job_id + ", " + resp['applied'] + ", "+job.id+")", resp['applied'] ? 'Mark as Unapplied' : "Mark as Applied"))
                company_info.append(document.createElement("br"), document.createElement("br"));
                company_info.appendChild(createCompanyInfoLine("Applied : ", "none", resp['applied']))
                company_info.appendChild(createCompanyNoteInfo(job.job_id, job.id, resp['note']));
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
            if (!(previously_selected_job_id === null || previously_selected_job_id === "")) {
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
function hideJob(job_id, job_obj_id) {
    setCookie("index_of_previously_select_job",getCookie("selected_job_index"))
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
function showJob(job_id, job_obj_id) {
    setCookie("index_of_previously_select_job",getCookie("selected_job_index"))
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
function toggle_applied(job_id, job_applied, job_obj_id) {
    setCookie("index_of_previously_select_job",getCookie("selected_job_index"))
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
function save_note(job_id, job_obj_id){
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

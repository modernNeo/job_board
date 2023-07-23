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
function createListSelectSection(all_lists, job_lists_for_user, job_id) {
    let job_list = document.createElement("div");
    job_lists_for_user = new Map(job_lists_for_user.map(job_list_for_user => [job_list_for_user.list, job_list_for_user]))
    for (let i = 0; i < all_lists.length; i++) {
        let option = document.createElement("input");
        option.setAttribute("type", "checkbox");
        option.checked = job_lists_for_user.get(all_lists[i].id) !== undefined;
        option.id = `job_list_${all_lists[i].id}`;
        if (option.checked){
            option.setAttribute("onclick", "removeJobToList(" + job_lists_for_user.get(all_lists[i].id).id + ")");
        }else {
            option.setAttribute("onclick", "addJobToList(" + job_id + ", " + all_lists[i].id + ")");
        }
        job_list.append(option);
        let option_label = document.createElement("label");
        option_label.setAttribute("for", `job_list_${all_lists[i].id}`);
        option_label.textContent = all_lists[i].name;
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
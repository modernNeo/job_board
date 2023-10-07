function addButton(functionCall, string){
    let button = document.createElement("button");
    button.setAttribute("onclick", functionCall);
    button.innerHTML = string;
    return button;
}
function createCompanyNoteInfo(jobObjectId, note, note_exists){
    let companyInfo = document.createElement("company_info_note")
    let companyLabel = document.createElement("label");
    companyLabel.style.fontWeight = 'bold';
    companyLabel.innerHTML = "Note : ";
    companyInfo.appendChild(companyLabel);

    let companyInput = document.createElement("input");
    companyInput.type = "text";
    companyInput.setAttribute("onfocusout", "saveNote("+jobObjectId+", "+note_exists+")");
    companyInput.setAttribute("id", "note");
    companyInput.value = note;
    companyInfo.appendChild(companyInput);
    companyInfo.appendChild(document.createElement("br"))
    return companyInfo;

}
function createCompanyTitle(companyTitle){
    header = document.createElement("h2");
    header.innerHTML = companyTitle;
    return header;
}
function createJobLocationLinkedId(job_board_id){
    id_tag = document.createElement("p");
    id_tag.innerHTML = job_board_id;
    return id_tag;
}
function createListSelectSection(allLists, userSpecificJobList, jobId) {
    let company_pane = document.getElementById("company_info");
    let max_width = (company_pane.offsetWidth === 763) ? 68 : 27;
    let current_width = max_width;
    let jobListDiv = document.createElement("div");
    for (let i = 0; i < allLists.length; i++) {
        if (allLists[i].name !== 'Archived' && allLists[i].name !== 'Applied') {
            let option = document.createElement("input");
            option.setAttribute("type", "checkbox");
            option.checked = userSpecificJobList.get(allLists[i].id) !== undefined;
            option.id = `job_list_${allLists[i].id}`;
            if (option.checked) {
                option.setAttribute("onclick", "removeJobFromList(" + userSpecificJobList.get(allLists[i].id).id + ")");
            } else {
                option.setAttribute("onclick", "addJobToList(" + jobId + ", " + allLists[i].id + ")");
            }
            let optionLabel = document.createElement("label");
            optionLabel.setAttribute("for", `job_list_${allLists[i].id}`);
            optionLabel.textContent = allLists[i].name;

            if (current_width - allLists[i].name.length < 0) {
                jobListDiv.append(document.createElement("br"));
                current_width = max_width;
            }
            current_width -= allLists[i].name.length;
            jobListDiv.append(option);
            jobListDiv.append(optionLabel);
        }
    }
    return jobListDiv;
}

function createCompanyInfoLine(label, pTagID, value){
    let companyInfo = document.createElement(`company_info_${pTagID}`)
    let companyLabel = document.createElement("label");
    companyLabel.style.fontWeight = 'bold';
    companyLabel.innerHTML = label;
    companyInfo.appendChild(companyLabel);

    let companyInput = document.createElement("p");
    companyInput.innerHTML = value;
    companyInput.setAttribute("id", pTagID)
    companyInfo.appendChild(companyInput);
    return companyInfo;

}
function createLink(text_to_display, link) {
    let linkElement = document.createElement("a");
    linkElement.href = link;
    linkElement.target = '_blank';
    linkElement.innerHTML = text_to_display;
    return linkElement;
}
function createDeleteButton(job_location_id) {
    let button = document.createElement("button");
    button.setAttribute("onclick", `deleteJobLocation(${job_location_id})`);
    button.innerHTML = "Delete";
    return button;
}

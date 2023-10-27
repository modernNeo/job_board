async function searchJob() {
    const search_title = document.getElementById("job_title").value.trim();
    const search_id = document.getElementById("job_id").value.trim();
    const search_company = document.getElementById("job_company_name").value.trim();
    if (search_title.length > 0) {
        setCookie("search_title", search_title);
    }else{
        setCookie("search_title", null);
    }
    if (search_id.length > 0) {
        setCookie("search_id", search_id);
    }else{
        setCookie("search_id", null);
    }
    if (search_company.length > 0) {
        setCookie("search_company", search_company);
    }else{
        setCookie("search_company", null);
    }
    await showInbox();
}
async function clearSearch() {
    document.getElementById("job_title").value = "";
    document.getElementById("job_id").value = "";
    document.getElementById("job_company_name").value = "";
    setCookie("search_title", null);
    setCookie("search_id", null);
    setCookie("search_company", null);
    await showInbox();
}
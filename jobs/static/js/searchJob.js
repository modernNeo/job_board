async function searchJob() {
    const search_title = document.getElementById("search_title").value.trim();
    const search_id = document.getElementById("search_id").value.trim();
    const search_company = document.getElementById("search_company").value.trim();
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
    document.getElementById("search_title").value = "";
    document.getElementById("search_id").value = "";
    document.getElementById("search_company").value = "";
    setCookie("search_title", null);
    setCookie("search_id", null);
    setCookie("search_company", null);
    await showInbox();
}
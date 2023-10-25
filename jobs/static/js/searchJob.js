async function searchJob() {
    const search_title = document.getElementById("job_title").value.trim();
    const search_id = document.getElementById("job_id").value.trim();
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
    await showInbox();
}
async function clearSearch() {
    setCookie("search_title", null);
    setCookie("search_id", null);
    await showInbox();
}
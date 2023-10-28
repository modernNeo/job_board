async function searchJob(){
    const currentSearchParams = new URLSearchParams(window.location.search);
    const search_title = document.getElementById("search_title").value.trim();
    const search_id = document.getElementById("search_id").value.trim();
    const search_company = document.getElementById("search_company").value.trim();
    let searchDetected = false;
    if (search_title.length > 0) {
        currentSearchParams.set("search_title", search_title);
        searchDetected = true;
    }
    if (search_id.length > 0) {
        currentSearchParams.set("search_id", search_id);
        searchDetected = true;
    }
    if (search_company.length > 0) {
        currentSearchParams.set("search_company", search_company);
        searchDetected = true;
    }
    if (searchDetected) {
        const view = getCookie("view")
        currentSearchParams.set("view", view)
        window.location.search = currentSearchParams;
    }
}
async function extractSearchParams() {
    let searchDetected = false;
    const currentSearchParams = new URLSearchParams(window.location.search.slice(1));
    if (currentSearchParams.get("search_title") !== null){
        setCookie("search_title", currentSearchParams.get("search_title"));
        document.getElementById("search_title").value = currentSearchParams.get("search_title");
        searchDetected = true;
    } else {
        setCookie("search_title", null);
    }
    if (currentSearchParams.get("search_id") !== null){
        setCookie("search_id", currentSearchParams.get("search_id"));
        document.getElementById("search_id").value = currentSearchParams.get("search_id");
        searchDetected = true;
    }  else {
        setCookie("search_id", null);
    }
    if (currentSearchParams.get("search_company") !== null){
        setCookie("search_company", currentSearchParams.get("search_company"));
        document.getElementById("search_company").value = currentSearchParams.get("search_company");
        searchDetected = true;
    } else {
        setCookie("search_company", null);
    }
    if (currentSearchParams.get("view") !== null){
        setCookie("view", currentSearchParams.get("view"));
    }
    return searchDetected;
}

async function clearSearch() {
    const currentSearchParams = new URLSearchParams(window.location.search.slice(1));
    const newUrl = new URLSearchParams();
    newUrl.set("view", currentSearchParams.get("view"));
    window.location.search = newUrl;
}
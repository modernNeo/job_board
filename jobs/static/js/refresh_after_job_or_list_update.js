
async function refresh_after_job_or_list_update(all_lists) {
    let func = await getListFuncOrParameterOrHeader(all_lists, "func");
    if (typeof func === "function") {
        await func()
    } else {
        await showList(Number(func.slice(9)), all_lists);
    }
}
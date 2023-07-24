
async function refreshAfterJobOrListUpdate(allLists) {
    let func = await getListFuncOrParameterOrHeader(allLists, "func");
    if (typeof func === "function") {
        await func()
    } else {
        await showList(Number(func.slice(9)), allLists);
    }
}
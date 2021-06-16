document.onreadystatechange = () => {
    document.getElementById("uploadForm").onsubmit = () => {
        //e.preventDefault();

        $("#pageloader").show();
        //$("#uploadForm").submit();
    }

    const tbodys = document.getElementsByTagName("tbody");
    if (tbodys.length !== 0) {
        const tbody = tbodys[0];

        for (const tr of tbody.children) {
            const status_td = tr.children[5];

            if (status_td.dataset.failed === "yes") {
                $(status_td.getElementsByClassName("btn")).popover({
                    content: status_td.dataset.failedMsg,
                    trigger: "hover",
                    placement: "top",
                    html: true,
                })
            }
            else if (status_td.dataset.processing === "yes"){
            }
        }
    }
}

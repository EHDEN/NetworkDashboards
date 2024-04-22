function update_upload_status(td, new_text, new_icon, new_color) {
    td.getElementsByClassName("status-text")[0].innerText = ` ${new_text}`;

    if (new_icon) {  // assume if new_icon is not undefined, new_color is also not undefined
        td.getElementsByTagName("i")[0].className = new_icon;
        td.className = new_color;
    }
}

function add_failure_message_popup(td, message) {
    $(td.getElementsByClassName("btn")).popover({
        content: message,
        trigger: "hover",
        placement: "top",
        html: true,
    })
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("uploadForm").onsubmit = () => {
        $("#pageloader").show();
    }

    const tbodys = document.getElementsByTagName("tbody");
    if (tbodys.length !== 0) {
        const tbody = tbodys[0];

        for (const tr of tbody.children) {
            const numberOfColumns = tr.children.length;
            const status_td = tr.children[numberOfColumns-1];
            
               
            if (status_td.dataset.failed === "yes") {
                add_failure_message_popup(status_td, status_td.dataset.failureMsg);
            }
            else if (status_td.dataset.processing === "yes"){
                const interval_id = setInterval(() => {
                    fetch(`upload/${status_td.dataset.uploadId}/status/`)
                        .then(r => r.json())
                        .then(r => {
                            if (r.status === "Done") {
                                tr.children[numberOfColumns - 5].innerText = r.data.r_package_version;
                                tr.children[numberOfColumns - 4].innerText = r.data.generation_date;
                                tr.children[numberOfColumns - 3].innerText = r.data.cdm_version;
                                tr.children[numberOfColumns - 2].innerText = r.data.vocabulary_version;

                                update_upload_status(status_td, "Done", "fas fa-check", "status-done");

                                clearInterval(interval_id);
                            }
                            else if (r.status === "Failed") {
                                update_upload_status(status_td, "Failed", "fas fa-times", "status-failed");

                                status_td.innerHTML += ' <a class="btn btn-danger failed-upload-msg"><i class="far fa-comment-alt"></i></a>';
                                add_failure_message_popup(status_td, r.failure_msg)

                                clearInterval(interval_id);
                            }
                            else {
                                update_upload_status(status_td, r.status);
                            }
                        })
                }, 5000)
            }
        }
    }
})

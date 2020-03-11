
// keep track of the current li clicked
let clicked;

// keep track of what groups are expanded
let groupsExpanded = [];

function updateHoverClasses(target, action) {
    if (action === "add") {
        target.addClass("hovered-background");
        target.find(".icon-div")
            .addClass("hovered-background")
            .addClass("hovered-text");
        target.find("span")
            .addClass("hovered-text");
    }
    else {
        target.removeClass("hovered-background");
        target.find(".icon-div")
            .removeClass("hovered-background")
            .removeClass("hovered-text");
        target.find("span")
            .removeClass("hovered-text");
    }
}

$(".head-nav li").hover(
    event => {
        // display the scrollbar if it is needed (elements extend the max height)
        if ($(".simplebar-track.simplebar-vertical").css("visibility") === "visible") {
            $(".simplebar-scrollbar").addClass("simplebar-visible");
        }

        const hovered = $(event.currentTarget);
        updateHoverClasses(hovered, "add");

        if (hovered.hasClass("top-group-li")) {
            hovered.addClass("top-group-li-hovered");
            hovered.find(".li-content span").addClass("span-on-li-hovered");
        }
        else if (hovered.hasClass("no-group-li")) {
            hovered.addClass("no-group-li-hovered");
            hovered.find(".li-content span").addClass("span-on-li-hovered");
        }

        for (let i = 0; i < groupsExpanded.length; i++) {
            if (groupsExpanded[i].is(hovered)) {
                break;
            }
        }
    },
    event => {
        // hide the scrollbar when collapsing the side menu
        $(".simplebar-scrollbar").removeClass("simplebar-visible");

        const hovered = $(event.currentTarget);

        if (hovered.hasClass("top-group-li")) {
            hovered.removeClass("top-group-li-hovered");
            hovered.find(".li-content span").removeClass("span-on-li-hovered");
        }
        else if (hovered.hasClass("no-group-li")) {
            hovered.removeClass("no-group-li-hovered");
            hovered.find(".li-content span").removeClass("span-on-li-hovered");
        }

        if (hovered.is(clicked)) {
            return;
        }
        updateHoverClasses(hovered, "remove");
    },
);

$(".head-nav li:not(.top-group-li)").click(event => {
    const liClicked = $(event.currentTarget);

    if (clicked) {
        if (liClicked.is(clicked)) {
            return;
        }

        updateHoverClasses(clicked, "remove");
    }

    clicked = liClicked;
    window.location.hash = clicked.find("span").text().trim();
    updateHoverClasses(clicked, "add");

    $("#main_iframe")
        .addClass("hide")
        .attr("src", clicked.attr("url"));
    $("#loading_screen").removeClass("hide");
});

$(".head-nav li.top-group-li").click(event => {
    const clicked = $(event.currentTarget);
    const wasExpanded = clicked.attr("aria-expanded");

    if (wasExpanded === "false") {
        groupsExpanded.push(clicked);
    }
    else {
        for (let i = 0; i < groupsExpanded.length; i++) {
            if (groupsExpanded[i].is(clicked)) {
                groupsExpanded.splice(i, 1);
                break;
            }
        }
    }
});

$("#main_iframe").on("load", event => {
    $("#loading_screen").addClass("hide");
    $("#main_iframe").removeClass("hide");
});

$(document).ready(event => {
    let preSelectedTab = false;

    const candidatesToDisplay = $(".head-nav li:not([aria-expanded])");
    if (window.location.hash) {
        const tabToDisplayTitle = decodeURI(window.location.hash.substr(1));
        for (let li of candidatesToDisplay) {
            li = $(li);
            const title = li.find("span").text().trim();

            if (title === tabToDisplayTitle) {
                clicked = li;
                updateHoverClasses(clicked, "add");
                $("#main_iframe").attr("src", clicked.attr("url"));
                preSelectedTab = true;
                break;
            }
        }
    }

    if (!preSelectedTab) {
        clicked = candidatesToDisplay.first();
        window.location.hash = clicked.find("span").text().trim();
        updateHoverClasses(clicked, "add");
        $("#main_iframe").attr("src", clicked.attr("url"));
    }

    const clickedParent = clicked.parent();
    if (!clickedParent.is("ul")) {
        clickedParent.collapse("toggle");
    }
});

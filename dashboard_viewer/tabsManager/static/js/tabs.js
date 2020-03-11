
// keep track of the current li clicked
let clicked;

let hoveredGroup;

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

$(".head-nav .tab").hover(
    event => {
        // display the scrollbar if it is needed (elements extend the max height)
        if ($(".simplebar-track.simplebar-vertical").css("visibility") === "visible") {
            $(".simplebar-scrollbar").addClass("simplebar-visible");
        }

        const hovered = $(event.currentTarget);
        updateHoverClasses(hovered, "add");

        if (hovered.hasClass("tab-group")) {
            hovered.addClass("tab-group-hovered");
            hovered.find("span").addClass("span-on-li-hovered");
        }
        else if (hovered.hasClass("tab-single")) {
            hovered.addClass("tab-single-hovered");
            hovered.find("span").addClass("span-on-li-hovered");
        }
    },
    event => {
        // hide the scrollbar when collapsing the side menu
        $(".simplebar-scrollbar").removeClass("simplebar-visible"); // TODO move this to hover out of nav-head

        const hovered = $(event.currentTarget);

        if (hovered.is(clicked)) {
            return;
        }
        updateHoverClasses(hovered, "remove");

        if (hovered.parents().is(hoveredGroup)) {
            return;
        }

        if (hovered.hasClass("tab-group")) {
            hovered.removeClass("tab-group-hovered");
            hovered.find("span").removeClass("span-on-li-hovered");
        }
        else if (hovered.hasClass("tab-single")) {
            hovered.removeClass("tab-single-hovered");
            hovered.find("span").removeClass("span-on-li-hovered");
        }
    },
);

$(".head-nav .tab-with-url").click(event => {
    const tabClicked = $(event.currentTarget);

    if (clicked) {
        if (tabClicked.is(clicked)) {
            return;
        }

        updateHoverClasses(clicked, "remove");
    }

    clicked = tabClicked;
    window.location.hash = clicked.find("span").text().trim();
    updateHoverClasses(clicked, "add");

    $("#main_iframe")
        .addClass("hide")
        .attr("src", clicked.attr("url"));
    $("#loading_screen").removeClass("hide");
});

$(".head-nav .group").hover(
    event => {
        hoveredGroup = $(event.currentTarget);

        const groupTop = hoveredGroup.children().first();
        groupTop.addClass("tab-group-hovered");
        groupTop.find("span").addClass("span-on-li-hovered");

        const subTabs = hoveredGroup.children().last().children();
        for (let i = 0; i < subTabs.length; i++) {
            const tab = $(subTabs[i]);

            tab.css("width", "380px");
            if (i === subTabs.length - 1) { // last
                tab.css("border-bottom-right-radius", "20px");
            }
            tab.find("span").addClass("span-on-li-hovered")
        }
    },
    event => {
        const groupTop = hoveredGroup.children().first();
        groupTop.removeClass("tab-group-hovered");
        groupTop.find("span").removeClass("span-on-li-hovered");

        const subTabs = hoveredGroup.children().last().children();
        for (let i = 0; i < subTabs.length; i++) {
            const tab = $(subTabs[i]);

            tab.css("width", "100px"); // TODO use classes here
            if (i === subTabs.length - 1) { // last
                tab.css("border-bottom-right-radius", "");
            }
            tab.find("span").removeClass("span-on-li-hovered")
        }

        hoveredGroup = undefined;
    },
);

$("#main_iframe").on("load", event => {
    $("#loading_screen").addClass("hide");
    $("#main_iframe").removeClass("hide");
});

$(document).ready(event => {
    let preSelectedTab = false;

    const candidatesToDisplay = $(".head-nav .tab-with-url");
    if (window.location.hash) {
        const tabToDisplayTitle = decodeURI(window.location.hash.substr(1));
        for (let tab of candidatesToDisplay) {
            tab = $(tab);
            const title = tab.find("span").text().trim();

            if (title === tabToDisplayTitle) {
                clicked = tab;
                updateHoverClasses(clicked, "add");
                $("#main_iframe").attr("src", clicked.attr("url"));
                preSelectedTab = true;
                break;
            }
        }
    }

    if (!preSelectedTab) {
        clicked = candidatesToDisplay.first(); // TODO this can be a group tab
        window.location.hash = clicked.find("span").text().trim();
        updateHoverClasses(clicked, "add");
        $("#main_iframe").attr("src", clicked.attr("url"));
    }

    const clickedParent = clicked.parent();
    if (clickedParent.hasClass("collapse")) {
        clickedParent.collapse("toggle");
    }
});


function updateHoverColorClasses(target, action) {
    if (action === "add") {
        if (target.hasClass("tab-within-group")) {
            target.addClass("hovered-background-within-group");
            target.find(".icon-div")
                .addClass("hovered-background-within-group")
                .addClass("hovered-text-within-group");
            target.find("span")
                .addClass("hovered-text-within-group");
        }
        else {
            target.addClass("hovered-background");
            target.find(".icon-div")
                .addClass("hovered-background")
                .addClass("hovered-text");
            target.find("span")
                .addClass("hovered-text");
        }
    }
    else {
        if (target.hasClass("tab-within-group")) {
            target.removeClass("hovered-background-within-group");
            target.find(".icon-div")
                .removeClass("hovered-background-within-group")
                .removeClass("hovered-text-within-group");
            target.find("span")
                .removeClass("hovered-text-within-group");
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
}

function updateHoverExpandedClasses(target, action, last) {
    if (action === "add") {
        $(".head-nav").addClass("nav-hovered-width");
        target.addClass("nav-hovered-width");
        if (target.hasClass("tab-group")) {
            target.addClass("tab-group-hovered-border-radius");
        }
        else if (target.hasClass("tab-single")) {
            target.addClass("tab-single-hovered-border-radius");
        }
        else if (last) {
            target.addClass("last-tab-within-group-border-radius")
        }

        if (target.hasClass("tab-within-group")) {
            target.find("span").addClass("tab-within-group-tile-hovered");
        }
        else {
            target.find("span").addClass("tab-title-hovered");
        }
    }
    else {
        $(".head-nav").removeClass("nav-hovered-width");
        target.removeClass("nav-hovered-width");
        if (target.hasClass("tab-group")) {
            target.removeClass("tab-group-hovered-border-radius");
        }
        else if (target.hasClass("tab-single")) {
            target.removeClass("tab-single-hovered-border-radius");
        }
        else if (last) {
            target.removeClass("last-tab-within-group-border-radius")
        }

        if (target.hasClass("tab-within-group")) {
            target.find("span").removeClass("tab-within-group-tile-hovered");
        }
        else {
            target.find("span").removeClass("tab-title-hovered");
        }
    }
}


// keep track of the current tab being displayed.
let clicked;

/**
 * keep track of the current group of tabs being hovered.
 * this allows to keep tabs of the same group expanded while the user
 *  has the mouse within a group of tabs
 */
let hoveredGroup;


$(".head-nav .tab").hover(
    event => {
        // display the scrollbar if it is needed (elements extend the max height)
        if ($(".simplebar-track.simplebar-vertical").css("visibility") === "visible") {
            $(".simplebar-scrollbar").addClass("simplebar-visible");
        }

        const hovered = $(event.currentTarget);
        updateHoverColorClasses(hovered, "add");
        updateHoverExpandedClasses(hovered, "add");
    },
    event => {
        // hide the scrollbar when collapsing the side menu
        $(".simplebar-scrollbar").removeClass("simplebar-visible");

        const hovered = $(event.currentTarget);

        // only reset the expanded classes if the mouse left the group that
        //  the current tab belongs to
        if (!hovered.parents().is(hoveredGroup)) {
            updateHoverExpandedClasses(hovered, "remove");
        }

        // only reset the color classes if the current tab is not the one
        //  being displayed/clicked
        if (!hovered.is(clicked)) {
            updateHoverColorClasses(hovered, "remove");
        }
    },
);

$(".head-nav .tab-with-url").click(event => {
    const tabClicked = $(event.currentTarget);

    if (clicked) {
        if (tabClicked.is(clicked)) {
            return;
        }

        updateHoverColorClasses(clicked, "remove");
    }

    clicked = tabClicked;
    window.location.hash = clicked.find("span").text().trim();
    updateHoverColorClasses(clicked, "add");

    $("#main_iframe")
        .addClass("hide")
        .attr("src", clicked.attr("url"));
    $("#loading_screen").removeClass("hide");
});

$(".head-nav .group").hover(
    event => {
        hoveredGroup = $(event.currentTarget);

        const groupTop = hoveredGroup.children().first();
        updateHoverExpandedClasses(groupTop, "add");

        const subTabs = hoveredGroup.children().last().children();
        for (let i = 0; i < subTabs.length; i++) {
            const tab = $(subTabs[i]);

            updateHoverExpandedClasses(tab, "add", i === subTabs.length - 1);
        }
    },
    event => {
        const hoveredGroupTmp = hoveredGroup;
        hoveredGroup = undefined;

        const groupTop = hoveredGroupTmp.children().first();
        updateHoverExpandedClasses(groupTop, "remove");

        const subTabs = hoveredGroupTmp.children().last().children();
        for (let i = 0; i < subTabs.length; i++) {
            const tab = $(subTabs[i]);

            updateHoverExpandedClasses(tab, "remove", i === subTabs.length - 1);
        }
    },
);

$("#main_iframe").on("load", event => {
    $("#loading_screen").addClass("hide");
    $("#main_iframe").removeClass("hide");
});

$(document).ready(event => {
    $(".head-nav").height(`calc(100% - ${$("#logo-container").outerHeight(true)}px)`);

    let preSelectedTab = false;

    const candidatesToDisplay = $(".head-nav .tab-with-url");
    if (window.location.hash) {
        const tabToDisplayTitle = decodeURI(window.location.hash.substr(1));
        for (let tab of candidatesToDisplay) {
            tab = $(tab);
            const title = tab.find("span").text().trim();

            if (title === tabToDisplayTitle) {
                clicked = tab;
                updateHoverColorClasses(clicked, "add");
                $("#main_iframe").attr("src", clicked.attr("url"));
                preSelectedTab = true;
                break;
            }
        }
    }

    if (!preSelectedTab) {
        clicked = candidatesToDisplay.first();
        updateHoverColorClasses(clicked, "add");
        $("#main_iframe").attr("src", clicked.attr("url"));
    }

    const clickedParent = clicked.parent();
    if (clickedParent.hasClass("collapse")) {
        clickedParent.collapse("toggle");
    }
});

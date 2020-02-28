
// keep track of the current li clicked
let clicked;

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

        updateHoverClasses($(event.currentTarget), "add");
    },
    event => {
        // hide the scrollbar when collapsing the side menu
        $(".simplebar-scrollbar").removeClass("simplebar-visible");

        const hovered = $(event.currentTarget);
        if (hovered.is(clicked)) {
            return;
        }
        updateHoverClasses(hovered, "remove");
    },
);

$(".head-nav li:not([aria-expanded])").click(event => {
    const liClicked = $(event.currentTarget);

    if (clicked) {
        if (liClicked.is(clicked)) {
            return;
        }

        updateHoverClasses(clicked, "remove");
    }

    clicked = liClicked;
    updateHoverClasses(clicked, "add");

    const url = liClicked.attr("url");
    const iframe = $("#main_iframe");
    iframe.attr("src", url);
    iframe.on("load", event => {
        console.log("done");
    })
});

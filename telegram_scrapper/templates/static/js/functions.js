var toggleReportPanel = function(e) {
    graph = e.parentNode.querySelector(".graph");
    icon = e.querySelector("i");
    if (graph && icon) {
        graph.classList.toggle("collapsed");
        icon.classList.toggle("la-chevron-circle-up");
        icon.classList.toggle("la-chevron-circle-down");
    }
};


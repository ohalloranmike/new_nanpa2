(function () {
  function initDualScroll(root) {
    var top = root.querySelector(".data-table-scroll-top");
    var body = root.querySelector(".data-table-scroll-body");
    var table = body && body.querySelector("table");
    var spacer = top && top.querySelector(".data-table-scroll-spacer");
    if (!top || !body || !table || !spacer) {
      return;
    }

    var syncing = false;

    function syncWidth() {
      spacer.style.width = table.scrollWidth + "px";
    }

    function linkScroll(source, target) {
      source.addEventListener("scroll", function () {
        if (syncing) {
          return;
        }
        syncing = true;
        target.scrollLeft = source.scrollLeft;
        syncing = false;
      });
    }

    syncWidth();
    linkScroll(top, body);
    linkScroll(body, top);

    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(syncWidth).observe(table);
    } else {
      window.addEventListener("resize", syncWidth);
    }
  }

  function initAll() {
    document.querySelectorAll("[data-table-dual-scroll]").forEach(initDualScroll);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();

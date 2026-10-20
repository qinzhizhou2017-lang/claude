(() => {
  const root = document.documentElement;
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const behavior = reduce ? "auto" : "smooth";

  /* 字号：只在本浏览器记住 */
  const FS_KEY = "ai-report-font-size";
  try { const v = localStorage.getItem(FS_KEY); if (v) root.style.setProperty("--fs", v + "px"); } catch (e) {}
  const curFs = () => parseFloat(getComputedStyle(document.body).fontSize) || 18;
  function setFs(px) {
    px = Math.max(15, Math.min(26, Math.round(px)));
    root.style.setProperty("--fs", px + "px");
    try { localStorage.setItem(FS_KEY, String(px)); } catch (e) {}
  }
  $("#fs-down").addEventListener("click", () => setFs(curFs() - 1));
  $("#fs-up").addEventListener("click", () => setFs(curFs() + 1));

  /* 表格：一键展开或收起正文表格（参考文献与数据证据表除外） */
  const exhibits = $$("details.exhibit:not(.big)");
  const tbtn = $("#tables");
  function syncTables() {
    const allOpen = exhibits.every((d) => d.open);
    tbtn.textContent = allOpen ? "收起表格" : "展开表格";
    tbtn.setAttribute("aria-pressed", String(allOpen));
  }
  tbtn.addEventListener("click", () => {
    const allOpen = exhibits.every((d) => d.open);
    exhibits.forEach((d) => { d.open = !allOpen; });
    syncTables();
  });
  exhibits.forEach((d) => d.addEventListener("toggle", syncTables));
  syncTables();

  /* 目录抽屉（窄屏） */
  const tocBtn = $("#toc-btn"), scrim = $("#scrim");
  function openToc(open) {
    document.body.classList.toggle("toc-open", open);
    scrim.hidden = !open;
    tocBtn.setAttribute("aria-expanded", String(open));
    if (open) {
      const a = $("#toc a.active");
      if (a) a.scrollIntoView({ block: "center" });
    }
  }
  tocBtn.addEventListener("click", () => openToc(!document.body.classList.contains("toc-open")));
  scrim.addEventListener("click", () => openToc(false));

  /* 跳转：先展开所在的表格，再滚动 */
  const back = $("#back");
  let backY = null;
  function reveal(el) {
    let d = el.closest("details");
    while (d) { d.open = true; d = d.parentElement && d.parentElement.closest("details"); }
  }
  function go(id, remember) {
    const el = document.getElementById(id);
    if (!el) return false;
    if (remember) { backY = window.scrollY; back.hidden = false; }
    reveal(el);
    el.scrollIntoView({ behavior, block: el.tagName === "TR" ? "center" : "start" });
    if (el.tagName === "TR") {
      el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash");
    }
    return true;
  }
  back.addEventListener("click", () => {
    if (backY !== null) window.scrollTo({ top: backY, behavior });
    backY = null; back.hidden = true;
  });

  /* 来源卡片 */
  const pop = $("#pop");
  let popFor = null, popAnchor = null;
  function cellText(row, i) { return row.cells[i] ? row.cells[i].textContent.trim() : ""; }
  function showPop(id, anchor) {
    const row = document.getElementById(id);
    if (!row || !row.cells) return;
    popFor = id; popAnchor = anchor;
    $("#pop-id").textContent = id;
    $("#pop-lvl").textContent = "证据等级 " + cellText(row, 3);
    $("#pop-title").textContent = cellText(row, 1);
    $("#pop-org").textContent = [cellText(row, 2), "发布 " + cellText(row, 4)].filter(Boolean).join(" · ");
    $("#pop-acc").textContent = "访问状态：" + cellText(row, 6) + " · 原台账 " + cellText(row, 8);
    const link = row.cells[7] && row.cells[7].querySelector("a");
    const pl = $("#pop-link");
    if (link) { pl.href = link.href; pl.hidden = false; } else { pl.removeAttribute("href"); pl.hidden = true; }
    back.hidden = true;
    pop.hidden = false;
    $("#pop-x").focus({ preventScroll: true });
  }
  function hidePop(restoreFocus) {
    if (pop.hidden) return;
    pop.hidden = true;
    if (backY !== null) back.hidden = false;
    if (restoreFocus && popAnchor) popAnchor.focus({ preventScroll: true });
  }
  $("#pop-x").addEventListener("click", () => hidePop(true));
  $("#pop-go").addEventListener("click", () => { const id = popFor; hidePop(false); go(id, true); });

  document.addEventListener("click", (e) => {
    const a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) {
      if (!pop.hidden && !pop.contains(e.target)) hidePop(false);
      return;
    }
    const id = decodeURIComponent(a.getAttribute("href").slice(1));
    e.preventDefault();
    if (a.classList.contains("cite")) { showPop(id, a); return; }
    hidePop(false);
    const inToc = !!a.closest("#toc");
    go(id, !inToc && !a.closest(".chapters"));
    if (inToc) openToc(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { hidePop(true); openToc(false); }
  });

  /* 当前位置：高亮目录、显示章名、阅读进度 */
  const heads = $$("main h2[id], main h3[id], main .part[id]");
  const tocLinks = new Map($$("#toc a").map((a) => [a.getAttribute("href").slice(1), a]));
  const where = $("#where"), prog = $("#prog");
  const defaultWhere = where.textContent;
  let active = null, ticking = false;
  function spy() {
    ticking = false;
    const line = (parseFloat(getComputedStyle(root).getPropertyValue("--bar")) || 54) + 40;
    let cur = null;
    for (const h of heads) {
      if (h.getBoundingClientRect().top - line <= 0) cur = h; else break;
    }
    const id = cur ? cur.id : null;
    if (id !== active) {
      if (active && tocLinks.get(active)) tocLinks.get(active).classList.remove("active");
      const link = id && tocLinks.get(id);
      if (link) {
        link.classList.add("active");
        const box = document.getElementById("toc");
        const y = link.offsetTop;
        if (y < box.scrollTop + 40 || y > box.scrollTop + box.clientHeight - 60) box.scrollTop = y - box.clientHeight / 3;
      }
      active = id;
      let h2 = cur;
      if (cur && cur.dataset.ch) h2 = document.getElementById(cur.dataset.ch);
      where.textContent = h2 && h2.dataset && h2.dataset.short ? h2.dataset.short : (cur && cur.classList.contains("part") ? "附录" : defaultWhere);
    }
    const max = document.documentElement.scrollHeight - window.innerHeight;
    prog.style.width = (max > 0 ? Math.min(100, (window.scrollY / max) * 100) : 0) + "%";
  }
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(spy); } }, { passive: true });
  window.addEventListener("resize", spy);
  spy();

  /* 打开带锚点的链接时直接定位 */
  const h = location.hash.slice(1);
  if (h) setTimeout(() => go(h, false), 60);
})();

const $ = s => document.querySelector(s);
let filter = "", editId = null;

const api = async (url, method = "GET", body) => {
  const res = await fetch(url, {method, headers: {"Content-Type": "application/json"},
    body: body ? JSON.stringify(body) : undefined});
  const data = res.status === 204 ? null : await res.json();
  if (!res.ok) throw data;
  return data;
};
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const toast = m => { const t = $("#toast"); t.textContent = m; t.className = "show"; setTimeout(() => t.className = "", 2200); };
const fmt = d => d ? new Date(d + "T00:00").toLocaleDateString("en-GB") : "No deadline";

async function load() {
  const p = new URLSearchParams();
  if (filter === "overdue") p.set("overdue", "1"); else if (filter) p.set("status", filter);
  if ($("#search").value.trim()) p.set("search", $("#search").value.trim());
  try {
    const tasks = await api("/api/tasks?" + p);
    $("#list").innerHTML = tasks.length
      ? `<div class="hdr"><div>Title</div><div>Priority</div><div>Status</div><div>Deadline</div><div></div></div>` +
        tasks.map(t => `<div class="r ${t.status === "Completed" ? "done" : ""}">
          <div class="t"><b>${esc(t.title)}</b><span>${esc(t.description)}</span></div>
          <div><span class="pill ${t.priority}">${t.priority}</span></div>
          <div><span class="pill ${t.status}">${t.status}</span></div>
          <div class="${t.overdue ? "od" : ""}">${fmt(t.deadline)}${t.overdue ? " (overdue)" : ""}</div>
          <div class="ic">
            <button class="ck" title="Toggle status" aria-label="Toggle status" onclick="toggle(${t.id},'${t.status}')">✓</button>
            <button class="ed" title="Edit" aria-label="Edit" onclick='edit(${JSON.stringify(t).replace(/'/g, "&#39;")})'>✎</button>
            <button class="del" title="Delete" aria-label="Delete" onclick="del(${t.id})">🗑</button>
          </div></div>`).join("")
      : `<div class="empty">No tasks here yet. Create one to get started.</div>`;
  } catch { toast("Could not load tasks."); }
}

async function toggle(id, s) {
  await api(`/api/tasks/${id}`, "PATCH", {status: s === "Pending" ? "Completed" : "Pending"}); load();
}
async function del(id) {
  if (!confirm("Delete this task?")) return;
  await api(`/api/tasks/${id}`, "DELETE"); toast("Task deleted"); load();
}
function openForm(t) {
  editId = t?.id ?? null;
  $("#dlgTitle").textContent = t ? "Edit task" : "New task";
  $("#title").value = t?.title ?? ""; $("#desc").value = t?.description ?? "";
  $("#deadline").value = t?.deadline ?? ""; $("#priority").value = t?.priority ?? "Medium";
  $("#e-title").textContent = $("#e-deadline").textContent = "";
  $("#dlg").showModal();
}
const edit = t => openForm(t);

$("#new").onclick = () => openForm();
$("#cancel").onclick = () => $("#dlg").close();
$("#form").onsubmit = async e => {
  e.preventDefault();
  const body = {title: $("#title").value, description: $("#desc").value,
                deadline: $("#deadline").value, priority: $("#priority").value};
  if (!body.title.trim()) { $("#e-title").textContent = "Title is required."; return; }
  try {
    await api(editId ? `/api/tasks/${editId}` : "/api/tasks", editId ? "PUT" : "POST", body);
    $("#dlg").close(); toast(editId ? "Task updated" : "Task created"); load();
  } catch (err) {
    $("#e-title").textContent = err.errors?.title ?? "";
    $("#e-deadline").textContent = err.errors?.deadline ?? "";
  }
};
$("#tabs").onclick = e => {
  if (!e.target.dataset.f && e.target.dataset.f !== "") return;
  filter = e.target.dataset.f;
  document.querySelectorAll("#tabs button").forEach(b => b.classList.toggle("on", b === e.target));
  load();
};
let timer; $("#search").oninput = () => { clearTimeout(timer); timer = setTimeout(load, 250); };
load();

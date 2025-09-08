// static/app.js
function $(sel){return document.querySelector(sel);}
function $all(sel){return document.querySelectorAll(sel);}
function toast(msg, type="info"){
  const n=document.createElement("div");
  n.className="flash "+(type==="error"?"error":"success");
  n.textContent=msg;
  document.body.appendChild(n);
  setTimeout(()=>n.remove(),3000);
}

document.addEventListener("DOMContentLoaded", () => {
  // ===== Home/About toggle =====
  const toggle = $("#homeAboutToggle");
  if (toggle){
    toggle.addEventListener("change", () => {
      const to = toggle.checked ? toggle.dataset.about : toggle.dataset.home;
      if (to) window.location.href = to;
    });
  }

  // ===== Calculation (screening) form validation =====
  const calcForm = $("#calc-form");
  if (calcForm){
    calcForm.addEventListener("submit", (e)=>{
      const jd = calcForm.querySelector("#jd_file");
      const resumes = calcForm.querySelector("#resume_files");
      if (!jd?.files?.length){ e.preventDefault(); toast("Please select a Job Description PDF","error"); return; }
      if (!resumes?.files?.length){ e.preventDefault(); toast("Please select at least one Resume PDF","error"); return; }
      if (![...jd.files].every(f=>f.name.toLowerCase().endsWith(".pdf"))){ e.preventDefault(); toast("JD must be a PDF","error"); return; }
      if (![...resumes.files].every(f=>f.name.toLowerCase().endsWith(".pdf"))){ e.preventDefault(); toast("All resumes must be PDFs","error"); return; }
    });
  }

  // ===== Login form validation =====
  const loginForm = $("#login-form");
  if (loginForm){
    loginForm.addEventListener("submit",(e)=>{
      const email = loginForm.querySelector("input[name='email']").value.trim();
      const pw = loginForm.querySelector("input[name='password']").value;
      if (!email || !pw){ e.preventDefault(); toast("Please enter email and password","error"); }
    });
  }

  // ===== Register form validation (now includes password rule) =====
  const regForm = $("#register-form");
  if (regForm){
    regForm.addEventListener("submit",(e)=>{
      const cn = regForm.querySelector("input[name='company_name']").value.trim();
      const email = regForm.querySelector("input[name='email']").value.trim();
      const pw = regForm.querySelector("input[name='password']").value;

      if (!cn || !email || !pw){
        e.preventDefault(); toast("All fields are required","error"); return;
      }

      const passOk = /^(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{8,}$/.test(pw);
      if (!passOk){
        e.preventDefault();
        toast("Password must be ≥8 chars, include an uppercase and a special character.","error");
      }
    });
  }

  // ===== Results toolbar actions (Top-N) =====
  const filterForm = $("#filter-form");
  const homeBtn = $("#btn-home");
  if (filterForm){
    const sel = filterForm.querySelector("#topN");
    if (sel){
      sel.addEventListener("change", () => filterForm.submit()); // auto-apply on change
    }
  }
  if (homeBtn){
    homeBtn.addEventListener("click", () => { window.location.href = "/"; });
  }

  // ===== Resume Detail Modal =====
  const modal = $("#resume-modal");
  const modalTitle = $("#modal-title");
  const modalEmail = $("#modal-email");
  const modalPhone = $("#modal-phone");
  const modalLinkedIn = $("#modal-linkedin");
  const modalText = $("#modal-text");
  const modalClose = $("#modal-close");

  function openModal(){ modal.classList.add("open"); modal.setAttribute("aria-hidden","false"); }
  function closeModal(){ modal.classList.remove("open"); modal.setAttribute("aria-hidden","true"); }
  if (modalClose) modalClose.addEventListener("click", closeModal);
  if (modal) modal.addEventListener("click", (e)=>{ if(e.target===modal) closeModal(); });
  document.addEventListener("keydown", (e)=>{ if(e.key==="Escape") closeModal(); });

  document.addEventListener("click", async (e) => {
    const link = e.target.closest(".resume-link");
    if (!link) return;
    e.preventDefault();
    const filename = link.dataset.filename;
    try {
      const resp = await fetch(`/api/resume_detail?file=${encodeURIComponent(filename)}`);
      const data = await resp.json();
      if (!data.ok) throw new Error(data.error || "Failed to load resume detail");

      modalTitle.textContent = data.filename || "Resume";
      modalEmail.textContent = data.email || "—";
      modalPhone.textContent = data.phone || "—";
      if (data.linkedin) {
        modalLinkedIn.textContent = data.linkedin;
        modalLinkedIn.href = data.linkedin.startsWith("http") ? data.linkedin : ("https://" + data.linkedin);
      } else {
        modalLinkedIn.textContent = "—";
        modalLinkedIn.removeAttribute("href");
      }
      modalText.textContent = data.text || "";

      openModal();
    } catch (err) {
      console.error(err);
      toast("Unable to load resume detail", "error");
    }
  });
});
// --- Nav active (in case Jinja couldn't add .active) ---
document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(a=>{
    if (a.getAttribute('href') === path) a.classList.add('active');
  });
});

// --- Simple accordion fallback (for browsers without <details> polish) ---
document.addEventListener("click", (e)=>{
  const sum = e.target.closest('summary');
  if (!sum) return;
  // allow default toggle; just add a tiny ripple/visual if needed later
});

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

  // ===== Register form validation =====
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

  // ===== Results toolbar: numeric "Show top" with capping =====
  const rowsTbody = document.getElementById('resumeRows');
  const topInput  = document.getElementById('topCount');
  const statusEl  = document.getElementById('topStatus');
  const homeBtn   = document.getElementById('btn-home');

  if (homeBtn){
    homeBtn.addEventListener("click", () => { window.location.href = "/"; });
  }

  if (rowsTbody && topInput){
    const allRows = Array.from(rowsTbody.querySelectorAll('tr'));
    const total   = allRows.length;

    function applyTop(){
      let n = parseInt(topInput.value, 10);
      if (isNaN(n) || n < 1) n = total;
      const capped = Math.min(Math.max(1, n), total);

      allRows.forEach((tr, idx) => {
        tr.style.display = (idx < capped) ? "" : "none";
      });

      if (statusEl){
        if (n > total) {
          statusEl.textContent = `Showing ${capped} of ${total} (capped to available)`;
          statusEl.classList.remove('text-gray-600');
          statusEl.classList.add('text-orange-600');
        } else {
          statusEl.textContent = `Showing ${capped} of ${total}`;
          statusEl.classList.remove('text-orange-600');
          statusEl.classList.add('text-gray-600');
        }
      }
    }

    // initial + live updates
    applyTop();
    topInput.addEventListener('input', applyTop);
    topInput.addEventListener('change', applyTop);
  }

  // ===== Resume Detail Modal (LinkedIn removed) =====
  const modal = $("#resume-modal");
  const modalTitle = $("#modal-title");
  const modalEmail = $("#modal-email");
  const modalPhone = $("#modal-phone");
  const modalText  = $("#modal-text");
  const modalClose = $("#modal-close");

  function openModal(){ if(modal){ modal.classList.add("open"); modal.setAttribute("aria-hidden","false"); } }
  function closeModal(){ if(modal){ modal.classList.remove("open"); modal.setAttribute("aria-hidden","true"); } }

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

      if (modalTitle) modalTitle.textContent = data.filename || "Resume";
      if (modalEmail) modalEmail.textContent = data.email || "—";
      if (modalPhone) modalPhone.textContent = data.phone || "—";
      if (modalText)  modalText.textContent  = data.text || "";

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

// --- Simple accordion fallback ---
document.addEventListener("click", (e)=>{
  const sum = e.target.closest('summary');
  if (!sum) return;
});

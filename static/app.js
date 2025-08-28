// static/app.js
function $(sel){return document.querySelector(sel);}
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
      if (!cn || !email || !pw){ e.preventDefault(); toast("All fields are required","error"); }
    });
  }

  // ===== Results toolbar actions =====
  const filterForm = $("#filter-form");
  const homeBtn = $("#btn-home");
  if (filterForm){
    const sel = filterForm.querySelector("#min");
    if (sel){
      sel.addEventListener("change", () => filterForm.submit()); // auto-apply on change
    }
  }
  if (homeBtn){
    homeBtn.addEventListener("click", () => { window.location.href = "/"; });
  }
});

const resume = document.getElementById("resume");
const fileLabel = document.getElementById("fileLabel");
const job = document.getElementById("job");
const results = document.getElementById("results");
const message = document.getElementById("message");
const targetRole = document.getElementById("targetRole");
let interviewSession = null;

resume.addEventListener("change", () => {
  fileLabel.textContent = resume.files[0]?.name || "Choose PDF, DOCX or TXT";
  document.getElementById("workspaceFile").textContent = resume.files[0]?.name || "No resume selected";
  updateWorkspaceRole();
});

function updateWorkspaceRole() {
  const selected = job.selectedOptions[0]?.textContent || "Choose a target role in Analyze.";
  document.getElementById("workspaceRole").textContent = selected;
  document.getElementById("interviewRoleLabel").textContent = selected;
}

function showView(viewId) {
  document.querySelectorAll(".page-view").forEach(view => view.classList.toggle("hidden", view.id !== viewId));
  document.querySelectorAll(".nav-button").forEach(button => button.classList.toggle("active", button.dataset.view === viewId));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => showView(button.dataset.view)));

async function loadJobs() {
  const res = await fetch("/api/jobs");
  const jobs = await res.json();
  job.innerHTML = jobs.map(j =>
    `<option value="${j.id}">${j.title} — ${j.company}</option>`
  ).join("");
}
loadJobs().then(() => {
  updateWorkspaceRole();
});
job.addEventListener("change", () => {
  updateWorkspaceRole();
});

function showError(err) {
  message.textContent = err.message || "Something went wrong.";
  results.classList.add("hidden");
}

async function postFile(url, extra = {}) {
  if (!resume.files[0]) throw new Error("Please upload a resume first.");
  const fd = new FormData();
  fd.append("resume", resume.files[0]);
  Object.entries(extra).forEach(([k, v]) => fd.append(k, v));

  message.textContent = "Analyzing… the first run may download the AI model.";
  const res = await fetch(url, { method: "POST", body: fd });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

document.getElementById("analyzeBtn").onclick = async () => {
  try {
    const data = await postFile("/api/analyze", { job_id: job.value });
    renderAnalysis(data);
    message.textContent = "Analysis complete.";
  } catch (e) { showError(e); }
};

document.getElementById("recommendBtn").onclick = async () => {
  try {
    const data = await postFile("/api/recommend");
    renderRecommendations(data);
    message.textContent = "Recommendations generated.";
  } catch (e) { showError(e); }
};

document.getElementById("roadmapBtn").onclick = async () => {
  const button = document.getElementById("roadmapBtn");
  button.disabled = true;
  try {
    const data = await postFile("/api/roadmap", { job_id: job.value });
    renderRoadmap(data);
    message.textContent = "Your personalized roadmap is ready.";
  } catch (e) { showError(e); }
  finally { button.disabled = false; }
};

document.getElementById("tailorBtn").onclick = async () => {
  const button = document.getElementById("tailorBtn");
  const description = document.getElementById("jobDescription").value.trim();
  if (!description) { message.textContent = "Paste the job description first."; return; }
  button.disabled = true;
  try {
    const selectedRole = targetRole.value.trim() || job.selectedOptions[0]?.textContent || "Target role";
    const data = await postFile("/api/tailor", { job_description: description, target_role: selectedRole });
    renderTailoring(data);
    message.textContent = "Resume tailoring suggestions are ready.";
  } catch (e) { message.textContent = e.message || "Could not tailor this resume."; }
  finally { button.disabled = false; }
};

document.getElementById("startInterviewBtn").onclick = async () => {
  const button = document.getElementById("startInterviewBtn");
  button.disabled = true;
  try {
    const data = await postFile("/api/interview/questions", { job_id: job.value });
    interviewSession = { ...data, index: 0, answers: {}, feedback: {} };
    renderInterviewQuestion();
    message.textContent = "Your interview practice is ready.";
  } catch (e) { message.textContent = e.message || "Could not create practice questions."; }
  finally { button.disabled = false; }
};

function pills(items, missing=false) {
  if (!items.length) return "<span class='muted'>None detected</span>";
  return `<div class="pills">${items.map(x => `<span class="pill ${missing ? "missing" : ""}">${x}</span>`).join("")}</div>`;
}

function renderAnalysis(data) {
  const a = data.analysis;
  results.classList.remove("hidden");
  results.innerHTML = `
    <div class="result-head">
      <div>
        <span class="eyebrow">SCREENING REPORT</span>
        <h2>${data.job.title}</h2>
        <p class="muted">${data.candidate} • ${data.job.company} • ${a.decision}</p>
      </div>
      <div class="score">${a.score}%</div>
    </div>
    <div class="columns">
      <div>
        <h3>Score breakdown</h3>
        <p>Semantic similarity <b>${a.semantic_score}%</b></p>
        <div class="bar"><i style="width:${a.semantic_score}%"></i></div>
        <p>Skill coverage <b>${a.skill_score}%</b></p>
        <div class="bar"><i style="width:${a.skill_score}%"></i></div>
        <p>Profile signals <b>${a.profile_score}%</b></p>
        <div class="bar"><i style="width:${a.profile_score}%"></i></div>
      </div>
      <div>
        <h3>Why this score?</h3>
        <ul>${a.explanation.map(x => `<li>${x}</li>`).join("")}</ul>
      </div>
    </div>
    <div class="columns">
      <div><h3>Matched skills</h3>${pills(a.matched_skills)}</div>
      <div><h3>Skill gaps</h3>${pills(a.missing_skills, true)}</div>
    </div>
    <div style="margin-top:22px">
      <h3>Candidate skill inventory</h3>${pills(a.candidate_skills)}
    </div>
  `;
}

function renderRecommendations(data) {
  results.classList.remove("hidden");
  results.innerHTML = `
    <div class="result-head">
      <div><span class="eyebrow">JOB RECOMMENDATIONS</span><h2>${data.candidate}</h2></div>
    </div>
    <p class="muted">Ranked using the same explainable matching pipeline. Use these as recommendations, not automatic hiring decisions.</p>
    ${data.recommendations.map((x, i) => `
      <div class="rec">
        <strong>#${i+1} ${x.job.title} — ${x.job.company}</strong>
        <small>${x.job.location} • Match: <b>${x.analysis.score}%</b> • ${x.analysis.decision}</small>
        <p>${x.analysis.explanation[0]} ${x.analysis.missing_skills.length ? "Gaps: " + x.analysis.missing_skills.slice(0,5).join(", ") : "No major required-skill gaps detected."}</p>
      </div>
    `).join("")}
  `;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}

function renderTailoring(data) {
  const output = document.getElementById("tailorResults");
  output.classList.remove("hidden");
  output.innerHTML = `
    <div class="tool-result-heading"><span class="eyebrow">EVIDENCE-BASED SUGGESTIONS</span><h3>${escapeHtml(data.target_role)}</h3></div>
    <div class="tailor-columns">
      <div><h4>Skills already supported</h4>${data.matched_skills.length ? `<div class="pills">${data.matched_skills.map(skill => `<span class="pill">${escapeHtml(skill)}</span>`).join("")}</div>` : `<p class="muted">No shared skills detected from the built-in skill list.</p>`}</div>
      <div><h4>Not found in this resume</h4>${data.not_found_skills.length ? `<div class="pills">${data.not_found_skills.map(skill => `<span class="pill missing">${escapeHtml(skill)}</span>`).join("")}</div>` : `<p class="muted">No listed skill gaps detected.</p>`}</div>
    </div>
    ${data.suggestions.length ? `<h4>What to emphasize</h4>${data.suggestions.map(item => `<article class="suggestion-card"><b>${escapeHtml(item.skill)}</b><p>${escapeHtml(item.action)}</p>${item.evidence ? `<small>Resume evidence: ${escapeHtml(item.evidence)}</small>` : ""}</article>`).join("")}` : ""}
    <h4>Resume evidence to bring forward</h4>
    ${data.evidence.length ? data.evidence.map(item => `<article class="evidence-card"><p>“${escapeHtml(item.text)}”</p><small>Relevant terms: ${escapeHtml(item.matched_skills.concat(item.matched_terms).join(", "))}</small></article>`).join("") : `<p class="muted">No clear matching resume lines found. Add accurate detail to your resume before tailoring.</p>`}
    <p class="grounding-note">${escapeHtml(data.grounding_note)}</p>
  `;
}

function renderInterviewQuestion() {
  if (!interviewSession) return;
  const output = document.getElementById("interviewResults");
  const current = interviewSession.questions[interviewSession.index];
  const savedAnswer = interviewSession.answers[current.id] || "";
  const feedback = interviewSession.feedback[current.id];
  output.classList.remove("hidden");
  output.innerHTML = `
    <div class="interview-progress"><span>QUESTION ${interviewSession.index + 1} OF ${interviewSession.questions.length}</span><span>${escapeHtml(current.type)}</span></div>
    <h3 class="interview-question">${escapeHtml(current.question)}</h3>
    <details class="resume-anchor"><summary>Why this question?</summary><p>${escapeHtml(current.anchor)}</p></details>
    <label class="field-label" for="interviewAnswer">Your answer</label>
    <textarea id="interviewAnswer" rows="6" maxlength="8000" placeholder="Try Situation, Task, Action, Result (STAR). Use your own accurate example.">${escapeHtml(savedAnswer)}</textarea>
    <button type="button" id="reviewAnswerBtn" class="primary">Review my answer</button>
    ${feedback ? `<div class="feedback-card"><span class="eyebrow">PRACTICE NOTES</span><p class="muted">${escapeHtml(feedback.scope_note)}</p><ul>${feedback.practice_notes.map(note => `<li>${escapeHtml(note)}</li>`).join("")}</ul><p><b>Try this structure:</b> ${escapeHtml(feedback.framework)}</p><small>${feedback.word_count} words</small></div>` : ""}
    <div class="interview-nav"><button type="button" id="previousQuestionBtn" class="secondary" ${interviewSession.index === 0 ? "disabled" : ""}>Previous</button><button type="button" id="nextQuestionBtn" class="secondary">${interviewSession.index === interviewSession.questions.length - 1 ? "Finish" : "Next question"}</button></div>
  `;
  document.getElementById("reviewAnswerBtn").onclick = async () => {
    const answer = document.getElementById("interviewAnswer").value.trim();
    if (answer.length < 10) { message.textContent = "Write a little more before reviewing your answer."; return; }
    const button = document.getElementById("reviewAnswerBtn");
    button.disabled = true;
    interviewSession.answers[current.id] = answer;
    const form = new FormData();
    form.append("question", current.question);
    form.append("anchor", current.anchor);
    form.append("answer", answer);
    try {
      const response = await fetch("/api/interview/feedback", { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not review this answer.");
      interviewSession.feedback[current.id] = data;
      renderInterviewQuestion();
      message.textContent = "Practice notes updated.";
    } catch (error) {
      button.disabled = false;
      message.textContent = error.message || "Could not review this answer.";
    }
  };
  document.getElementById("previousQuestionBtn").onclick = () => {
    interviewSession.answers[current.id] = document.getElementById("interviewAnswer").value;
    if (interviewSession.index > 0) { interviewSession.index -= 1; renderInterviewQuestion(); }
  };
  document.getElementById("nextQuestionBtn").onclick = () => {
    interviewSession.answers[current.id] = document.getElementById("interviewAnswer").value;
    if (interviewSession.index < interviewSession.questions.length - 1) {
      interviewSession.index += 1;
      renderInterviewQuestion();
    } else {
      output.innerHTML = `<div class="feedback-card"><h3>Practice session complete</h3><p>You reviewed ${Object.keys(interviewSession.feedback).length} of ${interviewSession.questions.length} answers. You can restart to practise again.</p></div>`;
    }
  };
}

function renderRoadmapLegacy(data) {
  const key = `fairmatch-roadmap-${data.job.id}-${data.candidate}`;
  let done = {};
  try { done = JSON.parse(localStorage.getItem(key) || "{}"); } catch (_) {}
  const actions = data.phases.flatMap((phase, phaseIndex) =>
    phase.actions.map((action, actionIndex) => ({ ...action, phaseIndex, actionIndex }))
  );
  const completed = () => actions.filter(a => done[`${a.phaseIndex}-${a.actionIndex}`]).length;
  results.classList.remove("hidden");
  results.innerHTML = `
    <div class="result-head roadmap-head">
      <div><span class="eyebrow">ADAPTIVE CAREER ROADMAP</span><h2>Your next 90 days</h2>
        <p class="muted">${data.job.title} · Built from ${data.starting_point} in your resume.</p></div>
      <div class="roadmap-match"><b>${data.match_score}%</b><small>starting match</small></div>
    </div>
    <div class="roadmap-focus"><strong>Focus skills</strong>${pills(data.focus_skills)}<small>${data.missing_skills.length ? "Priority gaps from your resume analysis" : "Build deeper evidence in skills already detected"}</small></div>
    <div class="roadmap-progress"><div><strong>Roadmap progress</strong><span id="roadmapProgressCount"></span></div><div class="bar"><i id="roadmapProgressBar"></i></div></div>
    <div class="roadmap-phases">${data.phases.map((phase, phaseIndex) => `
      <section class="roadmap-phase"><div class="phase-top"><span class="phase-days">DAYS ${phase.days}</span><span class="phase-theme">${phase.theme}</span></div>
        <h3>${phase.title}</h3><p class="muted">${phase.summary}</p>
        <div class="roadmap-actions">${phase.actions.map((action, actionIndex) => {
          const id = `${phaseIndex}-${actionIndex}`;
          return `<article class="roadmap-action ${done[id] ? "is-done" : ""}"><label class="roadmap-check"><input type="checkbox" data-roadmap-id="${id}" ${done[id] ? "checked" : ""}><span></span></label><div><span class="action-kind">${action.kind}</span><h4>${action.title}</h4><p>${action.detail}</p><div class="evidence"><b>Done when</b> ${action.evidence}</div></div></article>`;
        }).join("")}</div>
      </section>`).join("")}</div>
    <p class="roadmap-note">A flexible guide, not a guarantee of employment. Adapt the pace to your schedule and verify course choices for your level.</p>
  `;
  const updateProgress = () => {
    const count = completed();
    document.getElementById("roadmapProgressCount").textContent = `${count} of ${actions.length} actions complete`;
    document.getElementById("roadmapProgressBar").style.width = `${actions.length ? count / actions.length * 100 : 0}%`;
  };
  results.querySelectorAll("[data-roadmap-id]").forEach(box => box.addEventListener("change", () => {
    done[box.dataset.roadmapId] = box.checked;
    localStorage.setItem(key, JSON.stringify(done));
    box.closest(".roadmap-action").classList.toggle("is-done", box.checked);
    updateProgress();
  }));
  updateProgress();
}

function renderRoadmap(data) {
  const roadmapResults = document.getElementById("roadmapResults");
  const key = `fairmatch-roadmap-${data.job.id}-${data.candidate}`;
  let done = {};
  try { done = JSON.parse(localStorage.getItem(key) || "{}"); } catch (_) {}
  const tasks = data.phases.flatMap((phase, phaseIndex) =>
    phase.actions.map((action, actionIndex) => ({ phaseIndex, actionIndex, action }))
  );
  const phaseDone = index => data.phases[index].actions.filter((_, taskIndex) => done[`${index}-${taskIndex}`]).length;
  const allDone = () => tasks.filter(task => done[`${task.phaseIndex}-${task.actionIndex}`]).length;
  let activePhase = data.phases.findIndex((phase, index) => phaseDone(index) < phase.actions.length);
  if (activePhase < 0) activePhase = 0;

  roadmapResults.classList.remove("hidden");
  roadmapResults.innerHTML = `
    <div class="result-head roadmap-head">
      <div><span class="eyebrow">YOUR PERSONAL CAREER PLAN</span><h2>One step at a time</h2>
        <p class="muted">A 90-day plan for ${data.job.title}, based on ${data.starting_point} in your resume.</p></div>
      <div class="roadmap-match"><b>${data.match_score}%</b><small>current role match</small></div>
    </div>
    <div class="roadmap-focus"><div><strong>Your focus skills</strong><small>${data.missing_skills.length ? "These are the main gaps this plan targets." : "Build deeper evidence in skills already on your resume."}</small></div>${pills(data.focus_skills)}</div>
    <div class="roadmap-progress"><div><strong>Overall progress</strong><span id="roadmapProgressCount"></span></div><div class="bar"><i id="roadmapProgressBar"></i></div></div>
    <nav class="roadmap-tabs" aria-label="Roadmap phases">${data.phases.map((phase, index) => `
      <button type="button" class="roadmap-tab" data-phase-to="${index}"><span class="tab-number">${index + 1}</span><span class="tab-label"><b>Days ${phase.days}</b><small>${phase.theme}</small></span><span class="tab-count" id="phaseTabCount${index}"></span></button>`).join("")}
    </nav>
    <section id="activeRoadmapPhase" class="roadmap-phase"></section>
    <div class="roadmap-controls"><button type="button" id="previousPhaseBtn" class="phase-nav-button">Previous phase</button><span id="phaseStepLabel" class="muted"></span><button type="button" id="nextPhaseBtn" class="primary phase-nav-button">Next phase</button></div>
    <p class="roadmap-note">Check off actions as you finish them. Progress is saved in this browser so you can return later.</p>
  `;

  const updateProgress = () => {
    const count = allDone();
    document.getElementById("roadmapProgressCount").textContent = `${count} of ${tasks.length} actions complete`;
    document.getElementById("roadmapProgressBar").style.width = `${tasks.length ? count / tasks.length * 100 : 0}%`;
    data.phases.forEach((phase, index) => {
      const count = phaseDone(index);
      document.getElementById(`phaseTabCount${index}`).textContent = count === phase.actions.length ? "Done" : `${count}/${phase.actions.length}`;
    });
  };

  const renderPhase = () => {
    const phase = data.phases[activePhase];
    const count = phaseDone(activePhase);
    document.getElementById("activeRoadmapPhase").innerHTML = `
      <div class="phase-top"><div><span class="phase-days">DAYS ${phase.days} · PHASE ${activePhase + 1} OF ${data.phases.length}</span><h3>${phase.title}</h3></div><span class="phase-counter">${count} of ${phase.actions.length} done</span></div>
      <p class="phase-summary">${phase.summary}</p>
      <div class="roadmap-actions">${phase.actions.map((action, actionIndex) => {
        const id = `${activePhase}-${actionIndex}`;
        return `<article class="roadmap-action ${done[id] ? "is-done" : ""}"><label class="roadmap-check"><input type="checkbox" data-roadmap-id="${id}" ${done[id] ? "checked" : ""}><span></span></label><div class="action-copy"><span class="action-kind">${action.kind}</span><h4>${action.title}</h4><p>${action.detail}</p><div class="evidence"><b>Your finish line</b><span>${action.evidence}</span></div></div></article>`;
      }).join("")}</div>
      ${count === phase.actions.length ? `<p class="phase-complete">Phase complete. Move on whenever you’re ready.</p>` : ""}
    `;
    document.getElementById("phaseStepLabel").textContent = `Phase ${activePhase + 1} of ${data.phases.length}`;
    document.getElementById("previousPhaseBtn").disabled = activePhase === 0;
    document.getElementById("nextPhaseBtn").textContent = activePhase === data.phases.length - 1 ? "Back to first phase" : "Next phase";
    roadmapResults.querySelectorAll("[data-phase-to]").forEach(tab => tab.classList.toggle("active", Number(tab.dataset.phaseTo) === activePhase));
    roadmapResults.querySelectorAll("[data-roadmap-id]").forEach(box => box.addEventListener("change", () => {
      done[box.dataset.roadmapId] = box.checked;
      try { localStorage.setItem(key, JSON.stringify(done)); } catch (_) {}
      renderPhase();
      updateProgress();
    }));
  };

  roadmapResults.querySelectorAll("[data-phase-to]").forEach(tab => tab.addEventListener("click", () => {
    activePhase = Number(tab.dataset.phaseTo);
    renderPhase();
  }));
  document.getElementById("previousPhaseBtn").addEventListener("click", () => {
    if (activePhase > 0) { activePhase -= 1; renderPhase(); }
  });
  document.getElementById("nextPhaseBtn").addEventListener("click", () => {
    activePhase = (activePhase + 1) % data.phases.length;
    renderPhase();
  });
  updateProgress();
  renderPhase();
}

/**
 * College Student Management System (SMS) - Application Logic
 * Role-Based Access Control, Real-Time Calculations, and Data Orchestration
 */

// Application State
const state = {
  currentTab: 'dashboard',
  user: null,
  students: [],
  subjects: [],
  grades: [],
  dashboardData: null,
  cachedTeachers: [],
};

// Pure SVG Icons for Minimalist Professional Aesthetics (Zero Emojis)
const ICONS = {
  academicCap: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"/></svg>`,
  chart: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>`,
  users: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>`,
  book: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>`,
  award: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/></svg>`,
  trash: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>`,
  search: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>`,
  fileText: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`,
  check: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`,
};

// Score Derivation Utility (matches backend calculation)
function deriveGradeFromScore(scoreVal) {
  const score = parseFloat(scoreVal);
  if (isNaN(score)) return { letter: '-', points: '-' };
  if (score >= 90) return { letter: 'A', points: '4.00' };
  if (score >= 80) return { letter: 'B', points: '3.00' };
  if (score >= 70) return { letter: 'C', points: '2.00' };
  if (score >= 60) return { letter: 'D', points: '1.00' };
  return { letter: 'F', points: '0.00' };
}

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

// Initialization
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  setupModals();
  setupLiveScoreComputation();
  setupEventListeners();

  if (api.isAuthenticated()) {
    try {
      const me = await api.getMe();
      state.user = me;
      updateUserInterface();
      await loadInitialData();
    } catch {
      openLoginModal();
    }
  } else {
    openLoginModal();
  }
});

// Setup Navigation
function setupNavigation() {
  const navBtns = document.querySelectorAll('.nav-item[data-tab]');
  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      switchTab(target);
    });
  });
}

function switchTab(tabId) {
  state.currentTab = tabId;

  // Update nav buttons
  document.querySelectorAll('.nav-item[data-tab]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });

  // Update panels
  document.querySelectorAll('.view-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === `view-${tabId}`);
  });

  // Update Page Header Title
  const titles = {
    dashboard: 'Executive Dashboard',
    students: 'Student Directory',
    subjects: 'Academic Curriculum',
    grades: 'Grade Registry',
  };
  document.getElementById('pageTitle').textContent = titles[tabId] || 'College SMS';

  // Load relevant data for the tab
  if (tabId === 'dashboard') loadDashboardData();
  if (tabId === 'students') loadStudentsData();
  if (tabId === 'subjects') loadSubjectsData();
  if (tabId === 'grades') loadGradesData();
}

// Update UI based on Current User & Role
function updateUserInterface() {
  const user = state.user;
  if (!user) return;

  const role = user.role || 'student';
  const roleDisplay = role.toUpperCase();
  const userName = user.first_name && user.last_name 
    ? `${user.first_name} ${user.last_name}` 
    : user.username;

  document.getElementById('displayUserName').textContent = userName;
  document.getElementById('userAvatarInitial').textContent = userName.charAt(0).toUpperCase();

  const badge = document.getElementById('displayUserRole');
  badge.textContent = roleDisplay;
  badge.className = `user-role-badge role-${role}`;

  // Role selector sync
  const roleSelector = document.getElementById('demoRoleSelector');
  if (roleSelector) {
    if (user.username === 'admin') roleSelector.value = 'admin';
    else if (user.username === 'teacher_smith') roleSelector.value = 'teacher_smith';
    else if (user.username === 'teacher_jones') roleSelector.value = 'teacher_jones';
    else if (user.username === 'student_alice') roleSelector.value = 'student_alice';
    else roleSelector.value = '';
  }

  // Permission Visibility Rules
  const isAdmin = role === 'admin';
  const isTeacher = role === 'teacher';
  const isStudent = role === 'student';

  // Admin-only creation buttons
  document.getElementById('btnOpenAddStudent').style.display = isAdmin ? 'inline-flex' : 'none';
  document.getElementById('btnOpenAddSubject').style.display = isAdmin ? 'inline-flex' : 'none';

  // Grade recording: Admin or Teacher
  document.getElementById('btnOpenAddGrade').style.display = (isAdmin || isTeacher) ? 'inline-flex' : 'none';

  // Student specific view adjustments
  if (isStudent) {
    // If student, navigate to students tab by default to view their transcript
    document.getElementById('navDashboard').style.display = 'none';
    if (state.currentTab === 'dashboard') {
      switchTab('students');
    }
  } else {
    document.getElementById('navDashboard').style.display = 'flex';
  }
}

// Initial Data Load
async function loadInitialData() {
  await Promise.all([
    loadDashboardData(),
    loadStudentsData(),
    loadSubjectsData(),
    loadGradesData(),
  ]);
}

// Dashboard View Data
async function loadDashboardData() {
  if (state.user && state.user.role === 'student') return;
  try {
    const data = await api.getDashboardSummary();
    state.dashboardData = data;

    document.getElementById('metricTotalStudents').textContent = data.total_students;
    document.getElementById('metricTotalSubjects').textContent = data.total_subjects;
    document.getElementById('metricTotalGrades').textContent = data.total_grades;
    document.getElementById('metricAverageGpa').textContent = data.average_gpa.toFixed(2);
    document.getElementById('metricPassingRate').textContent = `${data.passing_rate}%`;
    document.getElementById('metricTotalTeachers').textContent = data.total_teachers;

    // Render Grade Distribution Bars
    const totalGrades = data.total_grades || 1;
    const dist = data.grade_distribution || { A: 0, B: 0, C: 0, D: 0, F: 0 };
    
    ['A', 'B', 'C', 'D', 'F'].forEach(letter => {
      const count = dist[letter] || 0;
      const pct = Math.round((count / totalGrades) * 100);
      const bar = document.getElementById(`bar-${letter}`);
      const label = document.getElementById(`count-${letter}`);
      if (bar) bar.style.width = `${pct}%`;
      if (label) label.textContent = `${count} (${pct}%)`;
    });
  } catch (err) {
    console.error('Failed to load dashboard:', err);
  }
}

// Students View Data
async function loadStudentsData() {
  const search = document.getElementById('searchStudents').value.trim();
  const program = document.getElementById('filterStudentProgram').value;

  try {
    const res = await api.getStudents(search, program);
    const students = res.results || res;
    state.students = students;

    const tbody = document.getElementById('studentsTableBody');
    tbody.innerHTML = '';

    if (!students || students.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No student records found.</td></tr>`;
      return;
    }

    students.forEach(s => {
      const tr = document.createElement('tr');
      const gpa = s.gpa !== undefined && s.gpa !== null ? s.gpa.toFixed(2) : '0.00';
      const isAdmin = state.user && state.user.role === 'admin';

      tr.innerHTML = `
        <td><span class="code-badge">${s.id}</span></td>
        <td style="font-weight: 600; color: var(--slate-900);">${s.name}</td>
        <td>${s.email}</td>
        <td>${s.program}</td>
        <td>${s.year_level}</td>
        <td><span class="gpa-pill">${gpa}</span></td>
        <td style="text-align: right;">
          <button class="btn btn-secondary btn-sm" onclick="viewStudentTranscript('${s.id}')" title="View Transcript">
            ${ICONS.fileText} Transcript
          </button>
          ${isAdmin ? `
            <button class="btn btn-danger-outline btn-sm" onclick="deleteStudentRecord('${s.id}')" title="Delete Student">
              ${ICONS.trash}
            </button>
          ` : ''}
        </td>
      `;
      tbody.appendChild(tr);
    });

    // Update count badge
    document.getElementById('badgeStudentsCount').textContent = students.length;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// View Student Transcript (all grades + computed GPA)
async function viewStudentTranscript(studentId) {
  try {
    const data = await api.getStudentGrades(studentId);
    
    document.getElementById('transcriptStudentName').textContent = data.student_name;
    document.getElementById('transcriptStudentId').textContent = data.student_id;
    document.getElementById('transcriptStudentEmail').textContent = data.email;
    document.getElementById('transcriptStudentProgram').textContent = `${data.program} • ${data.year_level}`;
    document.getElementById('transcriptGpa').textContent = data.gpa.toFixed(2);
    document.getElementById('transcriptTotalGrades').textContent = data.total_grades;

    const tbody = document.getElementById('transcriptTableBody');
    tbody.innerHTML = '';

    if (!data.grades || data.grades.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No academic grades recorded for this student yet.</td></tr>`;
    } else {
      data.grades.forEach(g => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><span class="code-badge">${g.subject.code}</span></td>
          <td style="font-weight: 500;">${g.subject.name}</td>
          <td>${g.subject.units}</td>
          <td style="font-weight: 600;">${parseFloat(g.score).toFixed(2)}</td>
          <td><span class="grade-badge grade-${g.letter}">${g.letter}</span></td>
          <td style="font-weight: 700;">${parseFloat(g.grade_points).toFixed(2)}</td>
        `;
        tbody.appendChild(row);
      });
    }

    openModal('modalTranscript');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Subjects View Data
async function loadSubjectsData() {
  const search = document.getElementById('searchSubjects').value.trim();
  try {
    const res = await api.getSubjects(search);
    const subjects = res.results || res;
    state.subjects = subjects;

    const tbody = document.getElementById('subjectsTableBody');
    tbody.innerHTML = '';

    if (!subjects || subjects.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No curriculum subjects registered.</td></tr>`;
      return;
    }

    const isAdmin = state.user && state.user.role === 'admin';

    subjects.forEach(sub => {
      const tr = document.createElement('tr');
      const instructorName = sub.instructor_name || 'Unassigned';

      tr.innerHTML = `
        <td><span class="code-badge">${sub.code}</span></td>
        <td style="font-weight: 600; color: var(--slate-900);">${sub.name}</td>
        <td>${sub.units} Units</td>
        <td>${instructorName}</td>
        <td style="text-align: right;">
          ${isAdmin ? `
            <button class="btn btn-danger-outline btn-sm" onclick="deleteSubjectRecord(${sub.id})" title="Delete Subject">
              ${ICONS.trash}
            </button>
          ` : '<span style="color: var(--slate-400); font-size: 12px;">Active</span>'}
        </td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById('badgeSubjectsCount').textContent = subjects.length;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Grades View Data
async function loadGradesData() {
  const studentQuery = document.getElementById('filterGradeStudent').value.trim();
  const subjectQuery = document.getElementById('filterGradeSubject').value.trim();

  try {
    const res = await api.getGrades(studentQuery, subjectQuery);
    const grades = res.results || res;
    state.grades = grades;

    const tbody = document.getElementById('gradesTableBody');
    tbody.innerHTML = '';

    if (!grades || grades.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No matching grade records found.</td></tr>`;
      return;
    }

    const canEdit = state.user && (state.user.role === 'admin' || state.user.role === 'teacher');

    grades.forEach(g => {
      const tr = document.createElement('tr');
      const instructor = g.recorded_by_username || '-';

      tr.innerHTML = `
        <td><span class="code-badge">${g.student}</span> <span style="margin-left: 6px; font-weight: 500;">${g.student_name || ''}</span></td>
        <td><span class="code-badge">${g.subject_code}</span> <span style="margin-left: 6px;">${g.subject_name}</span></td>
        <td style="font-weight: 700; color: var(--slate-900);">${parseFloat(g.score).toFixed(2)}</td>
        <td><span class="grade-badge grade-${g.letter}">${g.letter}</span></td>
        <td style="font-weight: 600;">${parseFloat(g.grade_points).toFixed(2)}</td>
        <td>${instructor}</td>
        <td style="text-align: right;">
          ${canEdit ? `
            <button class="btn btn-danger-outline btn-sm" onclick="deleteGradeRecord(${g.id})" title="Remove Grade">
              ${ICONS.trash}
            </button>
          ` : '<span style="color: var(--slate-400); font-size: 12px;">Recorded</span>'}
        </td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById('badgeGradesCount').textContent = grades.length;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Live Score Computation Preview in Add Grade Modal
function setupLiveScoreComputation() {
  const scoreInput = document.getElementById('inputGradeScore');
  const previewLetter = document.getElementById('previewGradeLetter');
  const previewPoints = document.getElementById('previewGradePoints');

  scoreInput.addEventListener('input', () => {
    const { letter, points } = deriveGradeFromScore(scoreInput.value);
    previewLetter.textContent = letter;
    previewPoints.textContent = points;

    previewLetter.className = `preview-metric-val`;
    if (letter === 'A') previewLetter.style.color = 'var(--gold-600)';
    else if (letter === 'F') previewLetter.style.color = 'var(--red-600)';
    else previewLetter.style.color = 'var(--slate-900)';
  });
}

// Modal Handlers
function setupModals() {
  // Close buttons
  document.querySelectorAll('.modal-close-btn, .btn-modal-cancel').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const modal = e.target.closest('.modal-backdrop');
      if (modal) modal.classList.remove('active');
    });
  });

  // Open Add Student
  document.getElementById('btnOpenAddStudent').addEventListener('click', () => {
    document.getElementById('formAddStudent').reset();
    openModal('modalAddStudent');
  });

  // Open Add Subject
  document.getElementById('btnOpenAddSubject').addEventListener('click', async () => {
    document.getElementById('formAddSubject').reset();
    openModal('modalAddSubject');
  });

  // Open Add Grade
  document.getElementById('btnOpenAddGrade').addEventListener('click', async () => {
    document.getElementById('formAddGrade').reset();
    document.getElementById('previewGradeLetter').textContent = '-';
    document.getElementById('previewGradePoints').textContent = '-';

    // Populate student and subject options
    populateGradeFormDropdowns();
    openModal('modalAddGrade');
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

// Populate dropdowns in Add Grade modal
async function populateGradeFormDropdowns() {
  const studentSelect = document.getElementById('inputGradeStudent');
  const subjectSelect = document.getElementById('inputGradeSubject');

  // Load all students
  const resStudents = await api.getStudents();
  const students = resStudents.results || resStudents;
  studentSelect.innerHTML = '<option value="">Select student...</option>';
  students.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = `${s.id} - ${s.name} (${s.program})`;
    studentSelect.appendChild(opt);
  });

  // Load subjects
  const resSubjects = await api.getSubjects();
  const subjects = resSubjects.results || resSubjects;
  subjectSelect.innerHTML = '<option value="">Select subject...</option>';

  const user = state.user;
  const isTeacher = user && user.role === 'teacher';

  subjects.forEach(sub => {
    // If user is teacher, emphasize or restrict to assigned subjects
    const isAssigned = sub.instructor === user.id || (sub.instructor_name && sub.instructor_name.includes(user.username));
    const opt = document.createElement('option');
    opt.value = sub.id;
    opt.textContent = `${sub.code} - ${sub.name} (${sub.units} units)`;

    if (isTeacher && !isAssigned) {
      opt.textContent += ' [Not your assigned subject]';
      opt.disabled = true;
    }
    subjectSelect.appendChild(opt);
  });
}

// Event Listeners for Forms & Filters
function setupEventListeners() {
  // Login Form
  document.getElementById('formLogin').addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = document.getElementById('loginUsername').value.trim();
    const p = document.getElementById('loginPassword').value.trim();
    try {
      await api.login(u, p);
      const me = await api.getMe();
      state.user = me;
      updateUserInterface();
      closeModal('modalLogin');
      showToast(`Signed in as ${u} (${me.role})`, 'success');
      await loadInitialData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Logout Button
  document.getElementById('btnLogout').addEventListener('click', async () => {
    await api.logout();
    state.user = null;
    openLoginModal();
    showToast('Signed out successfully.', 'info');
  });

  // Role Switcher Select (Top Bar)
  document.getElementById('demoRoleSelector').addEventListener('change', async (e) => {
    const target = e.target.value;
    if (!target) return;
    const creds = {
      admin: { u: 'admin', p: 'admin123' },
      teacher_smith: { u: 'teacher_smith', p: 'teacher123' },
      teacher_jones: { u: 'teacher_jones', p: 'teacher123' },
      student_alice: { u: 'student_alice', p: 'student123' },
    };
    const c = creds[target];
    if (c) {
      try {
        await api.login(c.u, c.p);
        const me = await api.getMe();
        state.user = me;
        updateUserInterface();
        showToast(`Switched account to ${c.u} (${me.role})`, 'success');
        await loadInitialData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    }
  });

  // Add Student Form
  document.getElementById('formAddStudent').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('inputStudentName').value.trim(),
      email: document.getElementById('inputStudentEmail').value.trim(),
      program: document.getElementById('inputStudentProgram').value.trim(),
      year_level: document.getElementById('inputStudentYear').value.trim(),
    };
    try {
      await api.createStudent(payload);
      closeModal('modalAddStudent');
      showToast('Student registered successfully.', 'success');
      await loadStudentsData();
      await loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Add Subject Form
  document.getElementById('formAddSubject').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      code: document.getElementById('inputSubjectCode').value.trim(),
      name: document.getElementById('inputSubjectName').value.trim(),
      units: parseInt(document.getElementById('inputSubjectUnits').value, 10),
    };
    try {
      await api.createSubject(payload);
      closeModal('modalAddSubject');
      showToast('Subject created successfully.', 'success');
      await loadSubjectsData();
      await loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Add Grade Form
  document.getElementById('formAddGrade').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      student: document.getElementById('inputGradeStudent').value,
      subject: document.getElementById('inputGradeSubject').value,
      score: document.getElementById('inputGradeScore').value,
    };
    try {
      await api.createGrade(payload);
      closeModal('modalAddGrade');
      showToast('Grade recorded successfully.', 'success');
      await loadGradesData();
      await loadDashboardData();
      await loadStudentsData(); // updates student GPAs
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Real-time search filters
  document.getElementById('searchStudents').addEventListener('input', debounce(loadStudentsData, 300));
  document.getElementById('filterStudentProgram').addEventListener('change', loadStudentsData);
  document.getElementById('searchSubjects').addEventListener('input', debounce(loadSubjectsData, 300));
  document.getElementById('filterGradeStudent').addEventListener('input', debounce(loadGradesData, 300));
  document.getElementById('filterGradeSubject').addEventListener('input', debounce(loadGradesData, 300));
}

// Delete Record Handlers
async function deleteStudentRecord(id) {
  if (!confirm(`Are you sure you want to delete student ${id}?`)) return;
  try {
    await api.deleteStudent(id);
    showToast(`Student ${id} removed.`, 'info');
    await loadStudentsData();
    await loadDashboardData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteSubjectRecord(id) {
  if (!confirm('Are you sure you want to remove this subject?')) return;
  try {
    await api.deleteSubject(id);
    showToast('Subject removed.', 'info');
    await loadSubjectsData();
    await loadDashboardData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteGradeRecord(id) {
  if (!confirm('Are you sure you want to delete this grade record?')) return;
  try {
    await api.deleteGrade(id);
    showToast('Grade record deleted.', 'info');
    await loadGradesData();
    await loadDashboardData();
    await loadStudentsData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Quick Login Chip Helper
function quickFillLogin(username, password) {
  document.getElementById('loginUsername').value = username;
  document.getElementById('loginPassword').value = password;
  document.getElementById('formLogin').dispatchEvent(new Event('submit'));
}

function openLoginModal() {
  document.getElementById('formLogin').reset();
  openModal('modalLogin');
}

// Utility debounce
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Expose globals for onclick handlers
window.viewStudentTranscript = viewStudentTranscript;
window.deleteStudentRecord = deleteStudentRecord;
window.deleteSubjectRecord = deleteSubjectRecord;
window.deleteGradeRecord = deleteGradeRecord;
window.quickFillLogin = quickFillLogin;

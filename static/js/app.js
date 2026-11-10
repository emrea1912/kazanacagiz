// Kazanacağız - Akıllı Ders & Soru Takip Sistemi Front-End Application

let currentUser = null;
let currentExamList = [];
let dueQuestions = [];
let currentDueIndex = 0;
let currentQuestionView = 'photo'; // 'photo' or 'digital'
let selectedUploadFile = null;

// Initialize on Load
document.addEventListener("DOMContentLoaded", async () => {
  setupClipboardPaste();
  setupDropZone();
  await loadExams();
  await checkAuthAndLoad();

  if (window.lucide) {
    lucide.createIcons();
  }
});

// Helper for authorized fetch
async function authFetch(url, options = {}) {
  const token = localStorage.getItem("kazanacagiz_token");
  options.headers = options.headers || {};
  if (token) {
    options.headers["Authorization"] = `Bearer ${token}`;
  }
  return fetch(url, options);
}

// --- AUTH & USER MANAGEMENT ---
async function checkAuthAndLoad() {
  const token = localStorage.getItem("kazanacagiz_token");
  if (!token) {
    // Show Login Modal
    openAuthModal();
    return;
  }

  try {
    const res = await authFetch("/api/auth/me");
    if (res.ok) {
      currentUser = await res.json();
      closeAuthModal();
      updateUserUI();
      await loadNotifications();
      navigate('due');
    } else {
      localStorage.removeItem("kazanacagiz_token");
      openAuthModal();
    }
  } catch (err) {
    console.error("Auth check error:", err);
    openAuthModal();
  }
}

function openAuthModal() {
  document.getElementById("authModal")?.classList.remove("hidden");
  populateRegisterExams();
}

function closeAuthModal() {
  document.getElementById("authModal")?.classList.add("hidden");
}

function switchAuthTab(tab) {
  const loginForm = document.getElementById("loginForm");
  const regForm = document.getElementById("registerForm");
  const tabLoginBtn = document.getElementById("authTabLoginBtn");
  const tabRegBtn = document.getElementById("authTabRegisterBtn");

  if (tab === 'login') {
    loginForm?.classList.remove("hidden");
    regForm?.classList.add("hidden");
    tabLoginBtn.className = "flex-1 py-2 rounded-xl bg-white text-brand-600 shadow-sm transition";
    tabRegBtn.className = "flex-1 py-2 rounded-xl text-slate-600 hover:text-slate-900 transition";
  } else {
    loginForm?.classList.add("hidden");
    regForm?.classList.remove("hidden");
    tabRegBtn.className = "flex-1 py-2 rounded-xl bg-white text-brand-600 shadow-sm transition";
    tabLoginBtn.className = "flex-1 py-2 rounded-xl text-slate-600 hover:text-slate-900 transition";
  }
}

function fillDemo(user, pass) {
  const u = document.getElementById("loginUsername");
  const p = document.getElementById("loginPassword");
  if (u && p) {
    u.value = user;
    p.value = pass;
  }
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("loginUsername").value;
  const password = document.getElementById("loginPassword").value;

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem("kazanacagiz_token", data.token);
      currentUser = data.user;
      closeAuthModal();
      await loadCurrentUser();
      await loadExams();
      navigate('due');
    } else {
      alert(data.detail || "Giriş başarısız!");
    }
  } catch (err) {
    alert("Sunucuya bağlanılamadı.");
  }
}

async function handleRegisterSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("regUsername").value;
  const password = document.getElementById("regPassword").value;
  const examId = parseInt(document.getElementById("regExamSelect").value || "1");

  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, selected_exam_id: examId })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem("kazanacagiz_token", data.token);
      currentUser = data.user;
      alert("Hesabınız oluşturuldu! Hoş geldiniz 🎉");
      closeAuthModal();
      await loadCurrentUser();
      await loadExams();
      navigate('due');
    } else {
      alert(data.detail || "Kayıt başarısız!");
    }
  } catch (err) {
    alert("Sunucuya bağlanılamadı.");
  }
}

async function logoutUser() {
  if (confirm("Çıkış yapmak istediğinize emin misiniz?")) {
    try {
      await authFetch("/api/auth/logout", { method: "POST" });
    } catch (e) {}
    localStorage.removeItem("kazanacagiz_token");
    currentUser = null;
    location.reload();
  }
}

function toggleUserDropdown() {
  document.getElementById("userDropdown")?.classList.toggle("hidden");
}

async function loadCurrentUser() {
  try {
    const res = await authFetch("/api/auth/me");
    if (res.ok) {
      currentUser = await res.json();
      updateUserUI();
    }
  } catch (err) {
    console.error("User load error:", err);
  }
}

function updateUserUI() {
  if (!currentUser) return;

  // Header Exam Name
  const examNameEl = document.getElementById("headerExamName");
  if (examNameEl) {
    examNameEl.textContent = currentUser.selected_exam_name || "Sınav Seçiniz";
  }

  // Profile Avatar & Dropdown
  const avatar = document.getElementById("userAvatarText");
  const dUsername = document.getElementById("dropdownUsername");
  const dRole = document.getElementById("dropdownRole");
  if (avatar) avatar.textContent = currentUser.username.substring(0, 1).toUpperCase();
  if (dUsername) dUsername.textContent = currentUser.username;
  if (dRole) dRole.textContent = currentUser.role === 'admin' ? 'Yönetici (Admin)' : (currentUser.is_premium ? 'Premium Üye' : 'Ücretsiz Öğrenci');

  // Premium Badge
  const premBtn = document.getElementById("premiumBadgeBtn");
  const premText = document.getElementById("premiumBadgeText");
  if (currentUser.is_premium) {
    premBtn.className = "flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-gradient-to-r from-amber-500 to-yellow-400 text-slate-900 shadow-md shadow-amber-500/20";
    premText.textContent = "PREMIUM ⭐";
    document.getElementById("uploadLimitBanner")?.classList.add("hidden");
  } else {
    premBtn.className = "flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200";
    premText.textContent = "Premium'a Geç";
    document.getElementById("uploadLimitBanner")?.classList.remove("hidden");
  }

  // Admin Tab Visibility
  const adminTab = document.getElementById("adminTabBtn");
  if (currentUser.role === "admin") {
    adminTab?.classList.remove("hidden");
    loadAdminData();
    loadAdminLicenseKeys();
  } else {
    adminTab?.classList.add("hidden");
  }
}

// --- PREMIUM PURCHASE & KEY REDEEM MODAL ---
function openPremiumModal() {
  document.getElementById("premiumModal")?.classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

function closePremiumModal() {
  document.getElementById("premiumModal")?.classList.add("hidden");
}

function switchPremiumTab(tab) {
  const keySec = document.getElementById("premiumKeySection");
  const cardSec = document.getElementById("premiumCardSection");
  const btnKey = document.getElementById("premTabKeyBtn");
  const btnCard = document.getElementById("premTabCardBtn");

  if (tab === 'key') {
    keySec?.classList.remove("hidden");
    cardSec?.classList.add("hidden");
    btnKey.className = "flex-1 py-2 rounded-xl bg-white text-brand-600 shadow-sm transition";
    btnCard.className = "flex-1 py-2 rounded-xl text-slate-600 hover:text-slate-900 transition";
  } else {
    keySec?.classList.add("hidden");
    cardSec?.classList.remove("hidden");
    btnCard.className = "flex-1 py-2 rounded-xl bg-white text-brand-600 shadow-sm transition";
    btnKey.className = "flex-1 py-2 rounded-xl text-slate-600 hover:text-slate-900 transition";
  }
}

async function submitLicenseKey() {
  const input = document.getElementById("licenseKeyInput");
  const key = input?.value?.trim();
  if (!key) {
    alert("Lütfen bir lisans anahtarı giriniz!");
    return;
  }

  try {
    const res = await authFetch("/api/premium/redeem-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key_code: key })
    });
    const data = await res.json();
    if (res.ok) {
      alert(data.message);
      closePremiumModal();
      await loadCurrentUser();
    } else {
      alert(`⚠️ ${data.detail || "Geçersiz lisans anahtarı!"}`);
    }
  } catch (err) {
    alert("Bağlantı hatası");
  }
}

async function handlePaymentSubmit(e) {
  e.preventDefault();
  const cardHolder = document.getElementById("cardHolder").value;
  const cardNumber = document.getElementById("cardNumber").value;
  const cardExpiry = document.getElementById("cardExpiry").value;
  const cardCvv = document.getElementById("cardCvv").value;
  const plan = document.querySelector('input[name="planRadio"]:checked')?.value || 'monthly';

  try {
    const res = await authFetch("/api/premium/simulate-payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plan,
        card_holder: cardHolder,
        card_number: cardNumber,
        expiry: cardExpiry,
        cvv: cardCvv
      })
    });
    const data = await res.json();
    if (res.ok) {
      alert(`🎉 ${data.message}`);
      closePremiumModal();
      await loadCurrentUser();
    } else {
      alert(data.detail || "Ödeme başarısız!");
    }
  } catch (err) {
    alert("Ödeme servisine bağlanırken hata oluştu.");
  }
}

// --- NAVIGATION & TABS ---
function navigate(tabName) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-item-btn, .mobile-nav-btn").forEach(el => el.classList.remove("active"));

  const targetTab = document.getElementById(`tab-${tabName}`);
  if (targetTab) {
    targetTab.classList.remove("hidden");
  }

  document.querySelectorAll(`[data-tab="${tabName}"]`).forEach(btn => btn.classList.add("active"));

  if (tabName === 'due') loadDueQuestions();
  if (tabName === 'community') loadCommunityPool();
  if (tabName === 'archive') loadArchive();
  if (tabName === 'admin') {
    loadAdminData();
    loadAdminLicenseKeys();
  }

  if (window.lucide) lucide.createIcons();
}

// --- EXAM MANAGEMENT & "DİĞER" ---
async function loadExams() {
  try {
    const res = await authFetch("/api/exams");
    if (res.ok) {
      currentExamList = await res.json();
      renderExamList();
      populateRegisterExams();
    }
  } catch (err) {
    console.error("Exams fetch error:", err);
  }
}

function populateRegisterExams() {
  const sel = document.getElementById("regExamSelect");
  if (!sel || currentExamList.length === 0) return;
  sel.innerHTML = currentExamList.filter(e => e.is_approved).map(e => `
    <option value="${e.id}">${e.name}</option>
  `).join("");
}

function renderExamList() {
  const container = document.getElementById("examListContainer");
  if (!container) return;

  container.innerHTML = currentExamList.map(exam => {
    const isSelected = currentUser && currentUser.selected_exam_id === exam.id;
    const isPending = !exam.is_approved;

    return `
      <div onclick="selectExam(${exam.id})" class="p-3 rounded-2xl border ${isSelected ? 'border-brand-600 bg-brand-50/70 font-black text-brand-700' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'} cursor-pointer flex items-center justify-between transition">
        <div class="flex items-center gap-2">
          <i data-lucide="${isSelected ? 'check-circle-2' : 'circle'}" class="w-4 h-4 ${isSelected ? 'text-brand-600' : 'text-slate-600'}"></i>
          <span class="text-xs sm:text-sm">${exam.name}</span>
          ${isPending ? '<span class="text-[10px] font-bold text-amber-600 bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded">Senin Özel Sınavın (Onayda)</span>' : ''}
        </div>
        ${isSelected ? '<span class="text-[10px] bg-brand-600 text-white font-bold px-2 py-0.5 rounded-full">Aktif</span>' : ''}
      </div>
    `;
  }).join("");

  if (window.lucide) lucide.createIcons();
}

async function selectExam(examId) {
  if (!currentUser) return;
  try {
    const res = await authFetch("/api/auth/update-exam", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ exam_id: examId })
    });
    if (res.ok) {
      await loadCurrentUser();
      closeExamModal();
      loadDueQuestions();
      loadCommunityPool();
      loadArchive();
    }
  } catch (err) {
    alert("Sınav seçimi güncellenemedi.");
  }
}

function openExamModal() {
  renderExamList();
  document.getElementById("examModal")?.classList.remove("hidden");
}

function closeExamModal() {
  document.getElementById("examModal")?.classList.add("hidden");
}

async function submitCustomExam() {
  const input = document.getElementById("customExamInput");
  const name = input?.value?.trim();
  if (!name) {
    alert("Lütfen sınav adını yazınız!");
    return;
  }

  try {
    const res = await authFetch("/api/exams/custom", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name })
    });
    const data = await res.json();
    if (res.ok) {
      input.value = "";
      alert(data.message);
      await loadCurrentUser();
      await loadExams();
      closeExamModal();
    } else {
      alert(data.detail || "Hata oluştu");
    }
  } catch (err) {
    alert("Bağlantı hatası");
  }
}

// --- ADMIN ACTIONS & LICENSE KEY MANAGEMENT ---
async function loadAdminData() {
  if (!currentUser || currentUser.role !== "admin") return;
  try {
    const res = await authFetch("/api/admin/pending-exams");
    if (res.ok) {
      const pendingExams = await res.json();
      document.getElementById("adminPendingCount").textContent = pendingExams.length;
      const listEl = document.getElementById("adminPendingExamsList");
      if (pendingExams.length === 0) {
        listEl.innerHTML = `<p class="text-xs text-slate-600 py-4 text-center">Şu an onay bekleyen sınav bulunmuyor.</p>`;
      } else {
        listEl.innerHTML = pendingExams.map(e => `
          <div class="py-3 flex items-center justify-between">
            <div>
              <p class="font-bold text-sm text-slate-800">${e.name}</p>
              <p class="text-[11px] text-slate-600">Ekleyen Kullanıcı: <strong class="text-slate-700">${e.creator_username || 'Kullanıcı'}</strong></p>
            </div>
            <button onclick="approveExam(${e.id})" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1 shadow-sm">
              <i data-lucide="check" class="w-3.5 h-3.5"></i>
              Onayla & Genele Aç
            </button>
          </div>
        `).join("");
      }
      if (window.lucide) lucide.createIcons();
    }
  } catch (err) {
    console.error("Admin data error:", err);
  }
}

async function approveExam(examId) {
  try {
    const res = await authFetch(`/api/admin/approve-exam/${examId}`, { method: "POST" });
    if (res.ok) {
      alert("Sınav onaylandı ve artık tüm kullanıcılara açıldı!");
      loadAdminData();
      loadExams();
    }
  } catch (err) {
    alert("Onaylanırken hata oluştu.");
  }
}

async function loadAdminLicenseKeys() {
  if (!currentUser || currentUser.role !== "admin") return;
  try {
    const res = await authFetch("/api/admin/license-keys");
    if (res.ok) {
      const keys = await res.json();
      const listEl = document.getElementById("adminLicenseKeysList");
      if (keys.length === 0) {
        listEl.innerHTML = `<p class="text-xs text-slate-600 py-3 text-center">Henüz lisans anahtarı üretilmemiş.</p>`;
      } else {
        listEl.innerHTML = keys.map(k => `
          <div class="py-2.5 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <code class="font-bold text-brand-700 text-xs bg-slate-100 px-2 py-0.5 rounded">${k.key_code}</code>
              <span class="text-[10px] text-slate-600">${k.duration_days} Günlük</span>
            </div>
            <div>
              ${k.is_used ? `
                <span class="text-[10px] font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">Kullanıldı (${k.used_by_username || 'Kullanıcı'})</span>
              ` : `
                <span class="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Kullanılabilir</span>
              `}
            </div>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("License key load error:", err);
  }
}

async function adminGenerateLicenseKey() {
  const days = parseInt(document.getElementById("adminKeyDuration").value || "30");
  try {
    const res = await authFetch("/api/admin/generate-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ duration_days: days })
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Yeni Lisans Anahtarı Üretildi:\n\n${data.key_code} (${data.duration_days} Günlük)`);
      loadAdminLicenseKeys();
    }
  } catch (err) {
    alert("Anahtar üretilemedi.");
  }
}

// --- IMAGE UPLOAD & CLIPBOARD (CTRL+V) & DRAG-DROP ---
function setupClipboardPaste() {
  window.addEventListener("paste", (e) => {
    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (const item of items) {
      if (item.type.indexOf("image") !== -1) {
        const file = item.getAsFile();
        handleSelectedImage(file);
        navigate('upload');
        break;
      }
    }
  });
}

function setupDropZone() {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleSelectedImage(e.target.files[0]);
    }
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-brand-500", "bg-indigo-50/40");
  });

  dropZone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-brand-500", "bg-indigo-50/40");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-brand-500", "bg-indigo-50/40");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectedImage(e.dataTransfer.files[0]);
    }
  });
}

function handleSelectedImage(file) {
  if (!file) return;
  selectedUploadFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    const preview = document.getElementById("imagePreview");
    const previewContainer = document.getElementById("imagePreviewContainer");
    const prompt = document.getElementById("dropZonePrompt");

    if (preview && previewContainer && prompt) {
      preview.src = e.target.result;
      previewContainer.classList.remove("hidden");
      prompt.classList.add("hidden");
    }
  };
  reader.readAsDataURL(file);
}

function clearSelectedImage(e) {
  if (e) e.stopPropagation();
  selectedUploadFile = null;
  document.getElementById("fileInput").value = "";
  document.getElementById("imagePreview").src = "";
  document.getElementById("imagePreviewContainer")?.classList.add("hidden");
  document.getElementById("dropZonePrompt")?.classList.remove("hidden");
}

function selectCorrectAnswer(choice) {
  document.getElementById("selectedCorrectAnswer").value = choice;
  document.querySelectorAll(".ans-btn").forEach(btn => {
    if (btn.dataset.ans === choice) {
      btn.classList.add("selected");
    } else {
      btn.classList.remove("selected");
    }
  });
}

async function submitNewQuestion() {
  if (!selectedUploadFile) {
    alert("Lütfen sorunun fotoğrafını yükleyin veya Ctrl+V ile yapıştırın!");
    return;
  }

  const correctAns = document.getElementById("selectedCorrectAnswer").value;
  if (!correctAns) {
    alert("⚠️ HATA: Sorunun DOĞRU CEVABINI (A, B, C, D veya E) seçmediniz!\n\nDoğru cevap girilmeden soru kaydedilemez.");
    return;
  }

  const subject = document.getElementById("inputSubject").value;
  const topic = document.getElementById("inputTopic").value;

  const formData = new FormData();
  formData.append("image", selectedUploadFile);
  formData.append("correct_answer", correctAns);
  formData.append("subject", subject);
  formData.append("topic", topic);

  const btn = document.getElementById("uploadSubmitBtn");
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Yapay Zekâ Analiz Ediyor & Kaydediliyor...</span>`;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await authFetch("/api/questions/upload", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      alert(`🎉 ${data.message}`);
      clearSelectedImage();
      document.getElementById("inputSubject").value = "";
      document.getElementById("inputTopic").value = "";
      selectCorrectAnswer("");
      navigate('due');
    } else {
      alert(data.detail || "Kayıt sırasında bir hata oluştu.");
    }
  } catch (err) {
    alert("Sunucuya bağlanırken hata meydana geldi.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4"></i><span>Soruyu Kaydet & Aralıklı Tekrara Ekle</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

// --- SPACED REPETITION & QUESTION SOLVING ---
async function loadDueQuestions() {
  if (!currentUser) return;
  try {
    const res = await authFetch("/api/questions/due");
    if (res.ok) {
      dueQuestions = await res.json();
      currentDueIndex = 0;
      updateDueBadges(dueQuestions.length);
      renderCurrentDueQuestion();
    }
  } catch (err) {
    console.error("Due questions fetch error:", err);
  }
}

function updateDueBadges(count) {
  const badge = document.getElementById("dueBadge");
  const desktopBadge = document.getElementById("desktopDueCount");
  const mobileBadge = document.getElementById("mobileDueBadge");

  if (badge) badge.textContent = `${count} Soru Bekliyor`;

  if (count > 0) {
    desktopBadge?.classList.remove("hidden");
    if (desktopBadge) desktopBadge.textContent = count;
    mobileBadge?.classList.remove("hidden");
  } else {
    desktopBadge?.classList.add("hidden");
    mobileBadge?.classList.add("hidden");
  }
}

function renderCurrentDueQuestion() {
  const container = document.getElementById("dueContainer");
  if (!container) return;

  if (dueQuestions.length === 0 || currentDueIndex >= dueQuestions.length) {
    container.innerHTML = `
      <div class="bg-white rounded-3xl p-10 text-center border border-slate-200/80 shadow-sm max-w-xl mx-auto space-y-4">
        <div class="w-16 h-16 mx-auto rounded-3xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
          <i data-lucide="check-check" class="w-8 h-8"></i>
        </div>
        <h3 class="text-xl font-black text-slate-800">Tebrikler! Bugünkü Tekrarlarını Tamamladın 🎉</h3>
        <p class="text-xs sm:text-sm text-slate-600">Bugün için vadesi gelen tüm soruları başarıyla çözdün. Bilgilerin hafızana kazındı!</p>
        <div class="pt-2">
          <button onclick="navigate('upload')" class="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-2xl text-xs font-bold transition inline-flex items-center gap-2 shadow-md shadow-brand-500/20">
            <i data-lucide="plus" class="w-4 h-4"></i>
            Yeni Soru Ekle
          </button>
        </div>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const q = dueQuestions[currentDueIndex];

  container.innerHTML = `
    <div class="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden max-w-3xl mx-auto">
      
      <!-- Card Header: Subject, Topic & View Switcher -->
      <div class="p-4 sm:p-5 bg-slate-50/70 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <span class="text-[11px] font-bold uppercase tracking-wider bg-indigo-100 text-brand-700 px-2.5 py-1 rounded-lg">${q.subject || 'Genel'}</span>
          <span class="text-xs font-semibold text-slate-700">${q.topic || 'Tekrar Sorusu'}</span>
        </div>

        <!-- DUAL VIEW SWITCHER: Orijinal Fotoğraf vs Dijital Kart -->
        <div class="flex items-center bg-slate-200/60 p-1 rounded-xl text-xs font-bold">
          <button onclick="switchQuestionView('photo')" id="viewBtnPhoto" class="view-toggle-btn px-3 py-1 rounded-lg transition ${currentQuestionView === 'photo' ? 'active' : 'text-slate-600'}">
            <i data-lucide="image" class="w-3.5 h-3.5 inline mr-1"></i> Fotoğraf
          </button>
          <button onclick="switchQuestionView('digital')" id="viewBtnDigital" class="view-toggle-btn px-3 py-1 rounded-lg transition ${currentQuestionView === 'digital' ? 'active' : 'text-slate-600'}">
            <i data-lucide="file-text" class="w-3.5 h-3.5 inline mr-1"></i> Dijital Kart
          </button>
        </div>
      </div>

      <!-- Question View (Orijinal Fotoğraf) -->
      <div id="viewAreaPhoto" class="${currentQuestionView === 'photo' ? 'block' : 'hidden'} p-4 sm:p-6 bg-slate-900/5 text-center">
        <img src="${q.image_url}" alt="Soru Fotoğrafı" class="max-h-[460px] mx-auto rounded-2xl object-contain shadow-md border border-slate-200">
      </div>

      <!-- Question View (Dijital Kart) -->
      <div id="viewAreaDigital" class="${currentQuestionView === 'digital' ? 'block' : 'hidden'} p-6 sm:p-8 space-y-4 bg-white">
        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-slate-800 text-sm sm:text-base font-medium leading-relaxed">
          ${q.digital_question_text || 'Soru metni dijitalleştirilemedi, fotoğraf görünümünden inceleyebilirsiniz.'}
        </div>
        <div class="space-y-2 pt-2">
          ${q.option_a ? `<div class="p-3 rounded-xl border border-slate-200 text-xs sm:text-sm font-medium flex gap-2"><strong class="text-brand-600 font-bold">A)</strong> ${q.option_a}</div>` : ''}
          ${q.option_b ? `<div class="p-3 rounded-xl border border-slate-200 text-xs sm:text-sm font-medium flex gap-2"><strong class="text-brand-600 font-bold">B)</strong> ${q.option_b}</div>` : ''}
          ${q.option_c ? `<div class="p-3 rounded-xl border border-slate-200 text-xs sm:text-sm font-medium flex gap-2"><strong class="text-brand-600 font-bold">C)</strong> ${q.option_c}</div>` : ''}
          ${q.option_d ? `<div class="p-3 rounded-xl border border-slate-200 text-xs sm:text-sm font-medium flex gap-2"><strong class="text-brand-600 font-bold">D)</strong> ${q.option_d}</div>` : ''}
          ${q.option_e ? `<div class="p-3 rounded-xl border border-slate-200 text-xs sm:text-sm font-medium flex gap-2"><strong class="text-brand-600 font-bold">E)</strong> ${q.option_e}</div>` : ''}
        </div>
      </div>

      <!-- ANSWER SECTION -->
      <div class="p-4 sm:p-6 border-t border-slate-100 bg-white space-y-4">
        
        <!-- Answer Selection Options (A, B, C, D, E) -->
        <div id="solveOptionSection">
          <p class="text-xs font-bold text-slate-700 mb-2">Cevabını İşaretle:</p>
          <div class="grid grid-cols-5 gap-2">
            <button onclick="pickSolveChoice('A')" class="solve-choice-btn py-3 rounded-xl border-2 font-black text-sm transition text-slate-700 border-slate-200 hover:border-brand-500" data-opt="A">A</button>
            <button onclick="pickSolveChoice('B')" class="solve-choice-btn py-3 rounded-xl border-2 font-black text-sm transition text-slate-700 border-slate-200 hover:border-brand-500" data-opt="B">B</button>
            <button onclick="pickSolveChoice('C')" class="solve-choice-btn py-3 rounded-xl border-2 font-black text-sm transition text-slate-700 border-slate-200 hover:border-brand-500" data-opt="C">C</button>
            <button onclick="pickSolveChoice('D')" class="solve-choice-btn py-3 rounded-xl border-2 font-black text-sm transition text-slate-700 border-slate-200 hover:border-brand-500" data-opt="D">D</button>
            <button onclick="pickSolveChoice('E')" class="solve-choice-btn py-3 rounded-xl border-2 font-black text-sm transition text-slate-700 border-slate-200 hover:border-brand-500" data-opt="E">E</button>
          </div>
          <input type="hidden" id="selectedSolveChoice" value="">

          <button onclick="submitAnswerForCurrent(${q.id})" class="w-full mt-4 py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-2xl font-black text-sm shadow-md transition">
            Cevabı Onayla
          </button>
        </div>

        <!-- ANSWER RESULT FEEDBACK AREA (LARGE BOLD FEEDBACK) -->
        <div id="feedbackResultArea" class="hidden space-y-4 animate-feedback">
          <div id="feedbackBanner" class="p-6 rounded-2xl text-center space-y-2">
            <!-- Injected by checkAnswer -->
          </div>

          <!-- Post-Answer Actions: AI Explain & Next Question -->
          <div class="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <button onclick="askAiForExplanation(${q.id})" class="w-full sm:flex-1 py-3 bg-indigo-50 hover:bg-indigo-100 text-brand-700 border border-brand-200 rounded-2xl text-xs font-bold transition flex items-center justify-center gap-2">
              <i data-lucide="sparkles" class="w-4 h-4"></i>
              Yapay Zekâya Danış (Çözümü Gör)
            </button>
            <button onclick="nextDueQuestion()" class="w-full sm:flex-1 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl text-xs font-bold transition flex items-center justify-center gap-2">
              <span>Sıradaki Tekrara Geç</span>
              <i data-lucide="arrow-right" class="w-4 h-4"></i>
            </button>
          </div>
        </div>

      </div>

    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

function switchQuestionView(viewType) {
  currentQuestionView = viewType;
  const photoArea = document.getElementById("viewAreaPhoto");
  const digitalArea = document.getElementById("viewAreaDigital");
  const btnPhoto = document.getElementById("viewBtnPhoto");
  const btnDigital = document.getElementById("viewBtnDigital");

  if (viewType === 'photo') {
    photoArea?.classList.remove("hidden");
    digitalArea?.classList.add("hidden");
    btnPhoto?.classList.add("active");
    btnDigital?.classList.remove("active");
  } else {
    photoArea?.classList.add("hidden");
    digitalArea?.classList.remove("hidden");
    btnPhoto?.classList.remove("active");
    btnDigital?.classList.add("active");
  }
}

function pickSolveChoice(opt) {
  document.getElementById("selectedSolveChoice").value = opt;
  document.querySelectorAll(".solve-choice-btn").forEach(btn => {
    if (btn.dataset.opt === opt) {
      btn.className = "solve-choice-btn py-3 rounded-xl border-2 font-black text-sm transition bg-brand-600 border-brand-700 text-white shadow-md";
    } else {
      btn.className = "solve-choice-btn py-3 rounded-xl border-2 font-black text-sm transition text-slate-700 border-slate-200 hover:border-brand-500 bg-white";
    }
  });
}

async function submitAnswerForCurrent(questionId) {
  const chosen = document.getElementById("selectedSolveChoice").value;
  if (!chosen) {
    alert("Lütfen bir şık işaretleyiniz!");
    return;
  }

  try {
    const res = await authFetch("/api/questions/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questionId, given_answer: chosen })
    });
    const result = await res.json();
    if (res.ok) {
      showAnswerFeedback(result);
    } else {
      alert(result.detail || "Cevap işlenemedi.");
    }
  } catch (err) {
    alert("Sunucuya bağlanılamadı.");
  }
}

function showAnswerFeedback(result) {
  document.getElementById("solveOptionSection")?.classList.add("hidden");
  const feedbackArea = document.getElementById("feedbackResultArea");
  const banner = document.getElementById("feedbackBanner");

  if (!feedbackArea || !banner) return;
  feedbackArea.classList.remove("hidden");

  if (result.is_correct) {
    banner.className = "p-6 rounded-3xl text-center space-y-2 bg-emerald-50 border-2 border-emerald-500 text-emerald-900";
    banner.innerHTML = `
      <div class="text-4xl sm:text-5xl font-black text-emerald-600 tracking-tight flex items-center justify-center gap-2">
        <i data-lucide="check-circle" class="w-10 h-10"></i>
        <span>DOĞRU!</span>
      </div>
      <p class="text-sm font-bold text-emerald-800">Harika iş! Doğru cevap: ${result.correct_answer}</p>
      <p class="text-xs text-emerald-700">Bu soru Aralıklı Tekrar algoritmasına göre <strong>1 hafta (7 gün) sonra</strong> tekrar karşına gelecektir.</p>
      ${result.mastered ? `
        <div class="mt-3 p-3 bg-amber-100 border border-amber-300 rounded-2xl text-amber-900 text-xs font-black flex items-center justify-center gap-2">
          <i data-lucide="trophy" class="w-4 h-4 text-amber-600"></i>
          3 Hafta Üst Üste Bildin! Bu Konuda Artık Ustasın!
        </div>
      ` : ''}
    `;
  } else {
    banner.className = "p-6 rounded-3xl text-center space-y-2 bg-rose-50 border-2 border-rose-500 text-rose-900";
    banner.innerHTML = `
      <div class="text-4xl sm:text-5xl font-black text-rose-600 tracking-tight flex items-center justify-center gap-2">
        <i data-lucide="x-circle" class="w-10 h-10"></i>
        <span>YANLIŞ!</span>
      </div>
      <p class="text-sm font-bold text-rose-800">Senin Cevabın: <strong>${result.given_answer}</strong> | Doğru Cevap: <strong>${result.correct_answer}</strong></p>
      <p class="text-xs text-rose-700">Unutmayı önlemek ve bilgiyi pekiştirmek için bu soru <strong>ERTESİ GÜN</strong> tekrar karşına çıkarılacaktır!</p>
    `;
  }

  if (window.lucide) lucide.createIcons();
}

function nextDueQuestion() {
  currentDueIndex++;
  renderCurrentDueQuestion();
}

// --- AI EXPLANATION MODAL ---
async function askAiForExplanation(questionId) {
  const modal = document.getElementById("aiModal");
  const content = document.getElementById("aiContent");
  if (!modal || !content) return;

  modal.classList.remove("hidden");
  content.innerHTML = `
    <div class="p-8 text-center space-y-3">
      <div class="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p class="text-xs font-bold text-slate-600">Yapay Zekâ sorunun detaylı çözümünü hazırlıyor...</p>
    </div>
  `;

  try {
    const res = await authFetch("/api/questions/ai-explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questionId })
    });
    const data = await res.json();
    if (res.ok) {
      const formatted = data.explanation
        .replace(/### (.*)/g, '<h3 class="text-base font-black text-slate-900 mt-2 mb-1">$1</h3>')
        .replace(/#### (.*)/g, '<h4 class="text-xs font-black text-brand-700 mt-2 mb-1 uppercase tracking-wider">$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '<p class="text-xs text-slate-700 my-1 leading-relaxed">')
        .replace(/\* (.*)/g, '<li class="text-xs text-slate-600 ml-4 list-disc">$1</li>');

      content.innerHTML = `<div class="space-y-2">${formatted}</div>`;
    } else {
      content.innerHTML = `<p class="text-xs text-rose-500">Çözüm alınamadı.</p>`;
    }
  } catch (err) {
    content.innerHTML = `<p class="text-xs text-rose-500">Bağlantı hatası.</p>`;
  }
}

function closeAiModal() {
  document.getElementById("aiModal")?.classList.add("hidden");
}

// --- COMMUNITY POOL (MODE 2 - WRONG QUESTIONS FROM SAME EXAM) ---
async function loadCommunityPool() {
  if (!currentUser) return;
  const examTitle = document.getElementById("communityExamTitle");
  if (examTitle) examTitle.textContent = currentUser.selected_exam_name || "Sınav";

  const container = document.getElementById("communityContainer");
  if (!container) return;

  container.innerHTML = `
    <div class="p-12 text-center text-slate-600">
      <div class="w-8 h-8 border-3 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
      <p class="text-xs">Sınavına özel zor sorular getiriliyor...</p>
    </div>
  `;

  try {
    const res = await authFetch("/api/questions/community-pool");
    if (res.ok) {
      const list = await res.json();
      if (list.length === 0) {
        container.innerHTML = `
          <div class="bg-white p-8 rounded-3xl text-center border border-slate-200 max-w-md mx-auto space-y-2">
            <i data-lucide="inbox" class="w-10 h-10 text-slate-600 mx-auto"></i>
            <h4 class="font-bold text-sm text-slate-700">Henüz Topluluk Sorusu Yok</h4>
            <p class="text-xs text-slate-600">Senin sınavında (${currentUser.selected_exam_name}) diğer öğrencilerin yanlış yaptığı yeni soru eklendiğinde burada listelenecek.</p>
          </div>
        `;
      } else {
        container.innerHTML = `
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            ${list.map(q => `
              <div class="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden flex flex-col hover:border-brand-500 transition">
                <div class="p-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                  <span class="text-[10px] font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded">${q.subject || 'Genel'}</span>
                  <span class="text-[11px] font-semibold text-slate-600">${q.topic || 'Zor Soru'}</span>
                </div>
                <div class="p-3 bg-slate-100 flex-1 flex items-center justify-center">
                  <img src="${q.image_url}" alt="Soru" class="max-h-48 object-contain rounded-xl">
                </div>
                <div class="p-3 bg-white">
                  <button onclick="askAiForExplanation(${q.id})" class="w-full py-2 bg-indigo-50 hover:bg-indigo-100 text-brand-700 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5">
                    <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                    Çözümü İncele & Pratik Yap
                  </button>
                </div>
              </div>
            `).join("")}
          </div>
        `;
      }
      if (window.lucide) lucide.createIcons();
    }
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-rose-500 text-center">Topluluk soruları yüklenemedi.</p>`;
  }
}

// --- ARCHIVE & STATS ---
async function loadArchive() {
  if (!currentUser) return;
  try {
    const res = await authFetch("/api/questions/all");
    if (res.ok) {
      const all = await res.json();
      document.getElementById("statTotal").textContent = all.length;
      document.getElementById("statExam").textContent = currentUser.selected_exam_name || "-";
      
      const dueCount = all.filter(q => q.next_review_date <= new Date().toISOString().split("T")[0]).length;
      document.getElementById("statDue").textContent = dueCount;

      const masteredCount = all.filter(q => q.mastered).length;
      document.getElementById("statMastered").textContent = masteredCount;

      const listEl = document.getElementById("allQuestionsList");
      if (all.length === 0) {
        listEl.innerHTML = `<p class="col-span-full text-xs text-slate-600 text-center py-8">Henüz yüklediğin bir soru bulunmuyor.</p>`;
      } else {
        listEl.innerHTML = all.map(q => `
          <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm p-3 space-y-2">
            <div class="flex items-center justify-between text-[11px]">
              <span class="font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded">${q.subject}</span>
              <span class="text-slate-600">${q.next_review_date}</span>
            </div>
            <img src="${q.image_url}" alt="Soru" class="w-full h-36 object-contain rounded-xl bg-slate-50">
            <div class="flex items-center justify-between pt-1">
              <span class="text-[11px] font-bold ${q.mastered ? 'text-emerald-600' : 'text-slate-600'}">
                ${q.mastered ? '🏆 Usta (3 Hafta)' : `Tekrar: ${q.consecutive_correct}/3`}
              </span>
              <button onclick="askAiForExplanation(${q.id})" class="text-brand-600 text-[11px] font-bold hover:underline">
                Çözüm & Analiz
              </button>
            </div>
          </div>
        `).join("");
      }
      if (window.lucide) lucide.createIcons();
    }
  } catch (err) {
    console.error("Archive fetch error:", err);
  }
}

// --- NOTIFICATIONS (10:00 & 15:00 REMINDERS) ---
async function loadNotifications() {
  if (!currentUser) return;
  try {
    const res = await authFetch("/api/notifications");
    if (res.ok) {
      const notifs = await res.json();
      const list = document.getElementById("notifList");
      const badge = document.getElementById("notifBadge");

      if (notifs.length > 0) {
        badge?.classList.remove("hidden");
        list.innerHTML = notifs.map(n => `
          <div class="py-2.5 space-y-0.5">
            <div class="flex items-center justify-between">
              <span class="text-[10px] font-bold uppercase tracking-wider text-brand-600">${n.reminder_type === 'morning_10' ? 'Sabah 10:00 Hatırlatması' : 'Öğleden Sonra 15:00'}</span>
              <span class="text-[10px] text-slate-600">${n.reminder_date}</span>
            </div>
            <p class="text-xs text-slate-700 font-medium">${n.message}</p>
          </div>
        `).join("");
      } else {
        badge?.classList.add("hidden");
        list.innerHTML = `<p class="text-xs text-slate-600 py-4 text-center">Günün planlanmış hatırlatması bulunmuyor.</p>`;
      }
    }
  } catch (err) {
    console.error("Notif load error:", err);
  }
}

function toggleNotifications() {
  const dropdown = document.getElementById("notifDropdown");
  dropdown?.classList.toggle("hidden");
  if (!dropdown?.classList.contains("hidden")) {
    loadNotifications();
  }
}

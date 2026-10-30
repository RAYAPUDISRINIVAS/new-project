document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  const form = document.getElementById("prediction-form");
  const submit = document.getElementById("submit-prediction");
  if (form && submit) {
    form.addEventListener("submit", () => {
      if (form.checkValidity()) {
        submit.disabled = true;
        submit.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Working…';
      }
    });
  }
});

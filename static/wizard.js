let step = 0;
const steps = document.querySelectorAll(".step");

function showStep(n) {
  steps.forEach(s => s.classList.remove("active"));
  steps[n].classList.add("active");
}

function next() {
  if (step < steps.length - 1) {
    step++;
    showStep(step);
  }
}

function prev() {
  if (step > 0) {
    step--;
    showStep(step);
  }
}

window.onload = () => showStep(step);

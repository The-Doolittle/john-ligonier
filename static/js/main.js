function initCarousel(carousel) {
  const track = carousel.querySelector(".carousel__track");
  const controls = carousel.querySelector(".carousel__controls");
  if (!track || !controls) return;

  controls.hidden = false;
  controls.addEventListener("click", (event) => {
    const button = event.target.closest("[data-direction]");
    if (!button) return;

    const step = track.clientWidth * Number(button.dataset.direction);
    const atEnd = track.scrollLeft + track.clientWidth >= track.scrollWidth - 1;
    const atStart = track.scrollLeft <= 0;

    if (step > 0 && atEnd) {
      track.scrollTo({ left: 0 });
    } else if (step < 0 && atStart) {
      track.scrollTo({ left: track.scrollWidth });
    } else {
      track.scrollBy({ left: step });
    }
  });
}

document.querySelectorAll(".carousel").forEach(initCarousel);

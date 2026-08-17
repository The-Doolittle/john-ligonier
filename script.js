// script.js
let slideIndex = 0;

function showSlides(n) {
    const slides = document.querySelectorAll('.carousel-slide');
    if (slides.length === 0) return; // Only run if there is a carousel on the page
    
    if (n >= slides.length) { slideIndex = 0; }
    if (n < 0) { slideIndex = slides.length - 1; }
    
    slides.forEach(slide => slide.classList.remove('active'));
    slides[slideIndex].classList.add('active');
}

function changeSlide(n) {
    slideIndex += n;
    showSlides(slideIndex);
}

document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.querySelector('main');
    
    // Gentle fade-in effect for the main content
    if (mainContent) {
        mainContent.style.transition = 'opacity 1.5s ease-in-out';
        setTimeout(() => {
            mainContent.style.opacity = '1';
        }, 100);
    }

    // Highlight the active navigation link based on current URL
    const currentLocation = location.href;
    const navLinks = document.querySelectorAll('nav a');
    
    for (let i = 0; i < navLinks.length; i++) {
        if (navLinks[i].href === currentLocation) {
            navLinks[i].className = "active";
        }
    }

    // Initialize carousel if it exists on the page
    showSlides(slideIndex);
});
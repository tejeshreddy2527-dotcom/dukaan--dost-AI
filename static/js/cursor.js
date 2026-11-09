/**
 * Dukaan Dost AI - Premium Cursor, 3D Perspective Tilt & Parallax Engine
 * Designed for futuristic cyber-kirana interaction.
 * Respects touch devices and prefers-reduced-motion.
 */

(function () {
  'use strict';

  // Check for touch device or prefers-reduced-motion
  const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (isTouchDevice || prefersReducedMotion) {
    return; // Clean graceful exit on mobile or reduced motion
  }

  // 1. Cursor Following Glow Dot
  const glow = document.createElement('div');
  glow.className = 'cursor-glow-follower';
  glow.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 320px;
    height: 320px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, rgba(16, 185, 129, 0.05) 45%, rgba(0,0,0,0) 70%);
    pointer-events: none;
    transform: translate(-50%, -50%);
    z-index: 9998;
    transition: opacity 0.3s ease;
    mix-blend-mode: screen;
  `;
  document.body.appendChild(glow);

  let mouseX = window.innerWidth / 2;
  let mouseY = window.innerHeight / 2;
  let currentX = mouseX;
  let currentY = mouseY;

  window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  }, { passive: true });

  function renderCursorGlow() {
    currentX += (mouseX - currentX) * 0.12;
    currentY += (mouseY - currentY) * 0.12;
    glow.style.left = `${currentX}px`;
    glow.style.top = `${currentY}px`;
    requestAnimationFrame(renderCursorGlow);
  }
  requestAnimationFrame(renderCursorGlow);

  // 2. 3D Perspective Tilt on Interactive Cards
  function setupTiltEffects() {
    const cards = document.querySelectorAll('.tilt-card, .stat-card, .glass-card, .action-card');
    cards.forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const cardX = e.clientX - rect.left;
        const cardY = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((cardY - centerY) / centerY) * -7; // max 7 deg
        const rotateY = ((cardX - centerX) / centerX) * 7;

        card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateZ(6px)`;
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)';
      });
    });
  }

  // 3. Magnetic Buttons Effect
  function setupMagneticButtons() {
    const magneticBtns = document.querySelectorAll('.magnetic-btn, .btn-primary, .btn-mint');
    magneticBtns.forEach(btn => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        btn.style.transform = `translate(${x * 0.22}px, ${y * 0.22}px)`;
      });

      btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'translate(0px, 0px)';
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    setupTiltEffects();
    setupMagneticButtons();
  });

  // Export utility for dynamic content
  window.refreshCursorEffects = () => {
    setupTiltEffects();
    setupMagneticButtons();
  };
})();

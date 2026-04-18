/**
 * Lendlyfin — Mobile nav & UX enhancements
 * Injected into every page. Handles hamburger menu, scroll effects, and
 * smooth link transitions. Zero dependencies.
 */
(function () {
  'use strict';

  /* ── 1. BUILD MOBILE NAV ───────────────────────────── */
  function buildMobileNav() {
    const nav = document.querySelector('nav.nav');
    if (!nav) return;

    // Create hamburger button
    const burger = document.createElement('button');
    burger.className = 'nav-hamburger';
    burger.setAttribute('aria-label', 'Toggle menu');
    burger.setAttribute('aria-expanded', 'false');
    burger.innerHTML = '<span></span><span></span><span></span>';
    nav.appendChild(burger);

    // Build mobile menu by mirroring desktop nav links
    const desktopLinks = nav.querySelectorAll('.nav-links a');
    const ctaLink      = nav.querySelector('.nav-cta');

    const mobileMenu = document.createElement('div');
    mobileMenu.className = 'nav-mobile-menu';

    desktopLinks.forEach(function (a) {
      const copy = document.createElement('a');
      copy.href      = a.href;
      copy.textContent = a.textContent;
      if (a.classList.contains('active')) copy.classList.add('active');
      mobileMenu.appendChild(copy);
    });

    // Add the CTA as a prominent bottom button
    if (ctaLink) {
      const ctaCopy = document.createElement('a');
      ctaCopy.href      = ctaLink.href;
      ctaCopy.textContent = ctaLink.textContent;
      ctaCopy.className = 'nav-mobile-cta';
      mobileMenu.appendChild(ctaCopy);
    }

    nav.appendChild(mobileMenu);

    /* ── Toggle ── */
    function openMenu() {
      nav.classList.add('nav-open');
      burger.setAttribute('aria-expanded', 'true');
      document.addEventListener('click', outsideClick);
    }

    function closeMenu() {
      nav.classList.remove('nav-open');
      burger.setAttribute('aria-expanded', 'false');
      document.removeEventListener('click', outsideClick);
    }

    function outsideClick(e) {
      if (!nav.contains(e.target)) closeMenu();
    }

    burger.addEventListener('click', function (e) {
      e.stopPropagation();
      nav.classList.contains('nav-open') ? closeMenu() : openMenu();
    });

    // Close when a mobile link is tapped
    mobileMenu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', closeMenu);
    });

    // Close on Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeMenu();
    });
  }

  /* ── 2. NAV SCROLL SHADOW ──────────────────────────── */
  function initNavShadow() {
    const nav = document.querySelector('nav.nav');
    if (!nav) return;
    var scrolled = false;
    window.addEventListener('scroll', function () {
      var now = window.scrollY > 8;
      if (now !== scrolled) {
        scrolled = now;
        nav.style.boxShadow = scrolled
          ? '0 4px 24px rgba(0,0,0,0.45)'
          : '';
        nav.style.borderBottomColor = scrolled
          ? 'rgba(255,255,255,0.1)'
          : '';
      }
    }, { passive: true });
  }

  /* ── 3. SMOOTH PAGE TRANSITIONS ───────────────────── */
  function initPageTransitions() {
    // Fade out on internal link click before navigating
    document.addEventListener('click', function (e) {
      var a = e.target.closest('a');
      if (!a) return;
      var href = a.getAttribute('href');
      if (!href) return;
      // Only internal relative links, not anchors or external
      if (
        href.startsWith('#') ||
        href.startsWith('http') ||
        href.startsWith('mailto') ||
        href.startsWith('tel') ||
        a.target === '_blank'
      ) return;

      e.preventDefault();
      document.body.style.transition = 'opacity 0.18s ease';
      document.body.style.opacity    = '0';
      setTimeout(function () {
        window.location.href = href;
      }, 180);
    });
  }

  /* ── 4. SCROLL-IN ANIMATIONS ───────────────────────── */
  function initScrollAnimations() {
    if (!('IntersectionObserver' in window)) return;

    var style = document.createElement('style');
    style.textContent = [
      '.scroll-hidden { opacity: 0; transform: translateY(22px); transition: opacity 0.5s ease, transform 0.5s cubic-bezier(0.34,1.1,0.64,1); }',
      '.scroll-visible { opacity: 1 !important; transform: none !important; }'
    ].join('\n');
    document.head.appendChild(style);

    var targets = document.querySelectorAll(
      '.feature-card, .benefit-card, .how-step, .tier-card, .when-card, ' +
      '.info-card, .next-card, .step, .next-step'
    );

    targets.forEach(function (el, i) {
      el.classList.add('scroll-hidden');
      el.style.transitionDelay = (i % 4) * 60 + 'ms';
    });

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('scroll-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    targets.forEach(function (el) { observer.observe(el); });
  }

  /* ── 5. WRAP RATE TICKER TABLE FOR MOBILE SCROLL ───── */
  function initTableWrap() {
    var tables = document.querySelectorAll('.data-table');
    tables.forEach(function (t) {
      if (t.parentElement.classList.contains('data-table-wrap')) return;
      var wrap = document.createElement('div');
      wrap.className = 'data-table-wrap';
      t.parentNode.insertBefore(wrap, t);
      wrap.appendChild(t);
    });
  }

  /* ── INIT ───────────────────────────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    buildMobileNav();
    initNavShadow();
    initPageTransitions();
    initScrollAnimations();
    initTableWrap();
  }
})();

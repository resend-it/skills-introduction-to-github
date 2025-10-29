const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const header = document.querySelector('.site-header');
const navToggle = document.querySelector('.nav-toggle');
const mobileMenu = document.querySelector('.mobile-menu');
const primaryNav = document.querySelector('.primary-nav ul');
const heroSection = document.querySelector('.hero');
const heroParallax = document.querySelector('.hero-parallax');
const themeToggle = document.querySelector('.theme-toggle');
const themeIcon = document.querySelector('.theme-icon');
const yearEl = document.getElementById('year');

const setYear = () => {
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }
};

setYear();

// Populate mobile navigation
if (mobileMenu && primaryNav) {
  const navLinks = Array.from(primaryNav.querySelectorAll('a'))
    .map((link) => `<li><a href="${link.getAttribute('href')}">${link.textContent}</a></li>`)
    .join('');
  mobileMenu.innerHTML = `<ul class="mobile-nav-list">${navLinks}</ul><a class="btn btn-primary" href="#pricing">Get Started</a>`;
}

const closeMobileMenu = () => {
  if (!mobileMenu) return;
  mobileMenu.classList.remove('is-open');
  if (navToggle) {
    navToggle.setAttribute('aria-expanded', 'false');
    navToggle.classList.remove('is-active');
  }
};

if (navToggle && mobileMenu) {
  navToggle.addEventListener('click', () => {
    const isOpen = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!isOpen));
    navToggle.classList.toggle('is-active');
    mobileMenu.classList.toggle('is-open');
  });

  mobileMenu.addEventListener('click', (event) => {
    if (event.target instanceof HTMLAnchorElement) {
      closeMobileMenu();
    }
  });
}

// Smooth scrolling with offset
const scrollToHash = (hash) => {
  const target = document.querySelector(hash);
  if (!target) return;
  const headerHeight = header ? header.offsetHeight : 0;
  const top = target.getBoundingClientRect().top + window.scrollY - headerHeight + 1;
  window.scrollTo({
    top,
    behavior: prefersReducedMotion ? 'auto' : 'smooth',
  });
};

document.addEventListener('click', (event) => {
  const target = event.target instanceof Element ? event.target.closest('a[href^="#"]') : null;
  if (target && target.getAttribute('href')) {
    const hash = target.getAttribute('href');
    if (hash && hash.length > 1) {
      event.preventDefault();
      scrollToHash(hash);
    }
  }
});

// Theme toggle
const applyTheme = (theme) => {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('luminaflow-theme', theme);
  if (themeIcon) {
    themeIcon.textContent = theme === 'dark' ? '🌙' : '☀️';
  }
};

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(nextTheme);
  });

  const initialTheme = document.documentElement.getAttribute('data-theme');
  applyTheme(initialTheme || 'light');
}

// Scroll animations
const animatedElements = document.querySelectorAll('[data-animate]');
if (animatedElements.length) {
  if (prefersReducedMotion) {
    animatedElements.forEach((el) => el.classList.add('is-visible'));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const delay = el.getAttribute('data-animate-delay');
          if (delay) {
            el.style.transitionDelay = `${parseInt(delay, 10)}ms`;
          }
          el.classList.add('is-visible');
          observer.unobserve(el);
        }
      });
    }, {
      threshold: 0.2,
      rootMargin: '0px 0px -10% 0px',
    });

    animatedElements.forEach((el) => observer.observe(el));
  }
}

// Counter animations
const counterElements = document.querySelectorAll('.stat-value');
if (counterElements.length) {
  const animateCounter = (el) => {
    const target = Number(el.dataset.target || 0);
    const duration = 1600;
    const start = prefersReducedMotion ? target : 0;
    const startTime = performance.now();

    const step = (currentTime) => {
      const progress = Math.min((currentTime - startTime) / duration, 1);
      const eased = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
      const value = Math.floor(start + (target - start) * eased);
      el.textContent = value.toLocaleString();
      if (progress < 1 && !prefersReducedMotion) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target.toLocaleString();
      }
    };

    if (prefersReducedMotion) {
      el.textContent = target.toLocaleString();
    } else {
      requestAnimationFrame(step);
    }
  };

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.6 });

  counterElements.forEach((el) => counterObserver.observe(el));
}

// Pricing toggle
const billingButtons = document.querySelectorAll('.toggle-option');
const pricingCards = document.querySelectorAll('.pricing-card');
const cycleSuffix = document.querySelectorAll('.pricing-card .cycle');

const updatePricing = (billing) => {
  billingButtons.forEach((btn) => {
    const isActive = btn.dataset.billing === billing;
    btn.classList.toggle('is-active', isActive);
    btn.setAttribute('aria-pressed', String(isActive));
  });

  pricingCards.forEach((card) => {
    const amountEl = card.querySelector('.amount');
    const cta = card.querySelector('.plan-cta');
    if (!amountEl || !cta) return;
    const price = amountEl.dataset[billing];
    if (price) {
      amountEl.textContent = price;
    }
    const linkAttr = `${billing}Link`;
    const href = cta.dataset[linkAttr];
    if (href) {
      cta.setAttribute('href', href);
    }
  });

  cycleSuffix.forEach((suffix) => {
    suffix.textContent = billing === 'yearly' ? '/mo billed yearly' : '/mo';
  });
};

if (billingButtons.length) {
  billingButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      if (btn.classList.contains('is-active')) return;
      updatePricing(btn.dataset.billing);
    });
  });
  updatePricing('monthly');
}

// FAQ accordion
const accordionTriggers = Array.from(document.querySelectorAll('.accordion-trigger'));
let openAccordionId = null;

const setAccordionState = (trigger, expanded) => {
  const panelId = trigger.getAttribute('aria-controls');
  const panel = panelId ? document.getElementById(panelId) : null;
  trigger.setAttribute('aria-expanded', String(expanded));
  if (!panel) return;
  panel.setAttribute('aria-hidden', String(!expanded));
  if (expanded) {
    panel.style.maxHeight = `${panel.scrollHeight}px`;
    openAccordionId = trigger.id;
  } else {
    panel.style.maxHeight = '0px';
    if (openAccordionId === trigger.id) {
      openAccordionId = null;
    }
  }
};

accordionTriggers.forEach((trigger) => {
  setAccordionState(trigger, false);
  trigger.addEventListener('click', () => {
    const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
    accordionTriggers.forEach((other) => {
      if (other !== trigger) {
        setAccordionState(other, false);
      }
    });
    setAccordionState(trigger, !isExpanded);
  });

  trigger.addEventListener('keydown', (event) => {
    const index = accordionTriggers.indexOf(trigger);
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      const next = accordionTriggers[(index + 1) % accordionTriggers.length];
      next.focus();
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      const prev = accordionTriggers[(index - 1 + accordionTriggers.length) % accordionTriggers.length];
      prev.focus();
    } else if (event.key === 'Home') {
      event.preventDefault();
      accordionTriggers[0].focus();
    } else if (event.key === 'End') {
      event.preventDefault();
      accordionTriggers[accordionTriggers.length - 1].focus();
    }
  });
});

// Lightbox
const lightbox = document.querySelector('.lightbox');
const lightboxImage = document.querySelector('.lightbox-image');
const lightboxCaption = document.querySelector('.lightbox-caption');
const lightboxClose = document.querySelector('.lightbox-close');
let lastFocusedElement = null;

const openLightbox = (img) => {
  if (!lightbox || !lightboxImage || !lightboxCaption) return;
  lastFocusedElement = document.activeElement;
  lightboxImage.src = img.src;
  lightboxImage.alt = img.alt;
  lightboxCaption.textContent = img.dataset.lightbox || '';
  lightbox.setAttribute('aria-hidden', 'false');
  lightboxClose?.focus();
  document.body.style.overflow = 'hidden';
};

const hideLightbox = () => {
  if (!lightbox) return;
  lightbox.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
  if (lightboxImage) {
    lightboxImage.src = '';
    lightboxImage.alt = '';
  }
  if (lastFocusedElement instanceof HTMLElement) {
    lastFocusedElement.focus();
  }
};

if (lightbox) {
  lightbox.addEventListener('click', (event) => {
    if (event.target === lightbox) {
      hideLightbox();
    }
  });
}

lightboxClose?.addEventListener('click', hideLightbox);
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && lightbox?.getAttribute('aria-hidden') === 'false') {
    hideLightbox();
  }
});

const galleryImages = document.querySelectorAll('[data-lightbox]');
galleryImages.forEach((img) => {
  img.addEventListener('click', () => openLightbox(img));
  img.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openLightbox(img);
    }
  });
  img.setAttribute('tabindex', '0');
});

// Contact form validation and submission
const contactForm = document.getElementById('contact-form');
if (contactForm) {
  const statusEl = contactForm.querySelector('.form-status');
  const fields = contactForm.querySelectorAll('input, textarea');

  const setFieldError = (field, message) => {
    const container = field.closest('.form-field');
    if (!container) return;
    const errorEl = container.querySelector('.field-error');
    if (errorEl) {
      errorEl.textContent = message;
    }
  };

  const validateField = (field) => {
    if (field.validity.valid) {
      setFieldError(field, '');
      return true;
    }
    if (field.validity.valueMissing) {
      setFieldError(field, 'This field is required.');
    } else if (field.validity.typeMismatch) {
      setFieldError(field, 'Please enter a valid value.');
    } else {
      setFieldError(field, 'Please correct this field.');
    }
    return false;
  };

  fields.forEach((field) => {
    field.addEventListener('input', () => validateField(field));
  });

  contactForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    let isValid = true;
    fields.forEach((field) => {
      if (!validateField(field)) {
        isValid = false;
      }
    });
    if (!isValid) return;

    const formData = {
      name: contactForm.name.value.trim(),
      email: contactForm.email.value.trim(),
      message: contactForm.message.value.trim(),
    };

    if (statusEl) {
      statusEl.textContent = 'Sending…';
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1500);
    let success = false;

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      success = response.ok;
    } catch (error) {
      clearTimeout(timeout);
      await new Promise((resolve) => setTimeout(resolve, 600));
      success = Math.random() > 0.3;
    }

    if (statusEl) {
      if (success) {
        statusEl.textContent = 'Message sent! We will reach out shortly. (Demo response)';
        contactForm.reset();
        fields.forEach((field) => setFieldError(field, ''));
      } else {
        statusEl.textContent = 'Something went wrong. Please try again later. (Demo response)';
      }
    }
  });
}

// Hero parallax
const updateParallax = () => {
  if (!heroSection || !heroParallax || prefersReducedMotion) return;
  if (window.innerWidth < 768) {
    heroParallax.style.transform = 'translate3d(0, 0, 0)';
    return;
  }
  const rect = heroSection.getBoundingClientRect();
  const offset = rect.top * -0.12;
  heroParallax.style.transform = `translate3d(0, ${offset}px, 0)`;
};

if (!prefersReducedMotion && heroParallax) {
  updateParallax();
  window.addEventListener('scroll', updateParallax, { passive: true });
  window.addEventListener('resize', updateParallax);
}

// Focus trap for mobile nav when open
if (mobileMenu && navToggle) {
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Tab') return;
    if (!mobileMenu.classList.contains('is-open')) return;
    const focusableSelectors = 'a[href], button:not([disabled]), [tabindex="0"]';
    const focusable = mobileMenu.querySelectorAll(focusableSelectors);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });
}

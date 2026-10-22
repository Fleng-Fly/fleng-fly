import { getCourse, listCourses, logout, setAccessToken } from './api.js';
import { describeApiError } from './errors.js';
import { el } from './layout.js';

const $ = (id) => document.getElementById(id);
let lastNavFocus;
let catalogPromise;

// Trusted static navigation markup, shared by Dashboard and Lessons.
// User and catalog data are assigned with textContent, never interpolated here.
const templateHtml = `    <svg class="dashboard-icons" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <symbol id="icon-grid" viewBox="0 0 24 24">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </symbol>
      <symbol id="icon-book" viewBox="0 0 24 24">
        <path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v17H6.5A2.5 2.5 0 0 0 4 21V4.5Z" />
        <path d="M4 21a2.5 2.5 0 0 1 2.5-2.5H20M8 7h8M8 11h6" />
      </symbol>
      <symbol id="icon-layers" viewBox="0 0 24 24">
        <path d="m12 2 9 5-9 5-9-5 9-5ZM3 12l9 5 9-5M3 17l9 5 9-5" />
      </symbol>
      <symbol id="icon-chart" viewBox="0 0 24 24">
        <path d="M4 20V5M4 20h16M8 16l4-5 3 2 5-7" />
      </symbol>
      <symbol id="icon-trophy" viewBox="0 0 24 24">
        <path
          d="M7 3h10v7a5 5 0 0 1-10 0V3ZM7 5H4v3a4 4 0 0 0 4 4m9-7h3v3a4 4 0 0 1-4 4M12 15v4m-4 2h8"
        />
      </symbol>
      <symbol id="icon-settings" viewBox="0 0 24 24">
        <path
          d="M10 2h4l.6 2.4 2 1.1 2.3-.8 2 3.4-1.7 1.7v2.4l1.7 1.7-2 3.4-2.3-.8-2 1.1L14 20h-4l-.6-2.4-2-1.1-2.3.8-2-3.4 1.7-1.7V9.8L3.1 8.1l2-3.4 2.3.8 2-1.1L10 2Z"
        />
        <circle cx="12" cy="11" r="2.5" />
      </symbol>
      <symbol id="icon-search" viewBox="0 0 24 24">
        <circle cx="10.8" cy="10.8" r="6.8" />
        <path d="m16 16 5 5" />
      </symbol>
      <symbol id="icon-bell" viewBox="0 0 24 24">
        <path d="M6 9a6 6 0 0 1 12 0v4l2 3H4l2-3V9ZM10 20h4" />
      </symbol>
      <symbol id="icon-menu" viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18" /></symbol>
      <symbol id="icon-close" viewBox="0 0 24 24"><path d="M5 5l14 14M19 5 5 19" /></symbol>
      <symbol id="icon-arrow" viewBox="0 0 24 24"><path d="M4 12h16m-7-7 7 7-7 7" /></symbol>
      <symbol id="icon-exit" viewBox="0 0 24 24">
        <path d="M10 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h5M14 7l5 5-5 5m5-5H8" />
      </symbol>
    </svg>
    <div id="nav-backdrop" class="dashboard-backdrop" hidden></div>
    <div class="dashboard-shell">
      <aside id="dashboard-sidebar" class="dashboard-sidebar" aria-label="Main navigation">
        <div class="sidebar-top">
          <a class="dashboard-brand" href="/index.html" aria-label="Fleng home"
            ><span class="dashboard-brand-mark">F</span><span>FLENG</span></a
          >
          <button
            id="nav-close"
            class="dashboard-icon-button nav-close"
            type="button"
            aria-label="Close navigation"
          >
            <svg><use href="#icon-close" /></svg>
          </button>
        </div>
        <p class="sidebar-caption">WORKSPACE</p>
        <nav class="sidebar-nav" aria-label="Dashboard sections">
          <a class="sidebar-link active" href="/dashboard.html" aria-current="page"
            ><svg><use href="#icon-grid" /></svg><span>Dashboard</span></a
          >
          <span
            class="sidebar-link sidebar-unavailable"
            aria-disabled="true"
            title="Leaderboard is not available yet"
            ><svg><use href="#icon-trophy" /></svg
            ><span>Leaderboard <small>Coming soon</small></span></span
          >
          <a class="sidebar-link" href="/courses.html"
            ><svg><use href="#icon-book" /></svg><span>Lessons</span></a
          >
          <a id="sidebar-course-link" class="sidebar-link" href="/courses.html"
            ><svg><use href="#icon-layers" /></svg><span>Course</span></a
          >
          <a class="sidebar-link" href="/settings.html"
            ><svg><use href="#icon-settings" /></svg><span>Settings</span></a
          >
        </nav>
        <div class="sidebar-foot">
          <span class="sidebar-foot-mark">✦</span>
          <p>Keep learning.<br /><strong>Your journey is yours.</strong></p>
        </div>
      </aside>
      <div id="dashboard-main-wrap" class="dashboard-main-wrap">
        <header class="dashboard-topbar">
          <button
            id="nav-open"
            class="dashboard-icon-button nav-open"
            type="button"
            aria-label="Open navigation"
            aria-controls="dashboard-sidebar"
            aria-expanded="false"
          >
            <svg><use href="#icon-menu" /></svg>
          </button>
          <form id="dashboard-search" class="dashboard-search" role="search">
            <label class="sr-only" for="search-query">Search courses and lessons</label>
            <svg><use href="#icon-search" /></svg>
            <input
              id="search-query"
              type="search"
              placeholder="Search courses and lessons"
              autocomplete="off"
              minlength="2"
            />
            <button type="submit" aria-label="Search">Search</button>
          </form>
          <div class="dashboard-top-actions">
            <button
              class="dashboard-icon-button notification-button"
              type="button"
              disabled
              title="Notifications are not available yet"
              aria-label="Notifications are not available yet"
            >
              <svg><use href="#icon-bell" /></svg>
            </button>
            <div class="profile-control">
              <button
                id="profile-toggle"
                class="profile-toggle"
                type="button"
                aria-expanded="false"
                aria-controls="profile-menu"
              >
                <span id="profile-avatar" class="profile-avatar" aria-hidden="true">F</span
                ><span id="profile-short-name" class="profile-name">Account</span
                ><span aria-hidden="true">⌄</span>
              </button>
              <div id="profile-menu" class="profile-menu" aria-hidden="true" inert>
                <a href="/settings.html"
                  ><svg><use href="#icon-settings" /></svg>Account settings</a
                >
                <button id="profile-logout" type="button">
                  <svg><use href="#icon-exit" /></svg>Log out
                </button>
                <p id="logout-error" class="dashboard-menu-error" role="alert" hidden></p>
              </div>
            </div>
          </div>
        </header>
      </div>
    </div>
          <section
            id="search-results"
            class="search-results dashboard-card"
            aria-label="Search results"
            hidden
          >
            <div class="section-heading">
              <h2>Search results</h2>
              <button id="search-close" class="dashboard-text-button" type="button">Close</button>
            </div>
            <div id="search-results-body" role="status" aria-live="polite"></div>
          </section>`;

export function setWorkspaceUser(user) {
  const name = (user.displayName || 'Learner').trim();
  $('profile-short-name').textContent = name;
  $('profile-avatar').textContent = name.charAt(0).toLocaleUpperCase() || 'F';
}

export function mountWorkspace(active) {
  const template = document.createElement('template');
  template.innerHTML = templateHtml;
  const content = template.content;
  const main = document.querySelector('main');
  main.prepend(content.querySelector('#search-results'));
  content.querySelector('#dashboard-main-wrap').append(main);
  for (const link of content.querySelectorAll('.sidebar-link[href]')) {
    const selected = active === 'lessons'
      ? link.getAttribute('href') === '/courses.html' && link.id !== 'sidebar-course-link'
      : link.getAttribute('href') === '/dashboard.html';
    link.classList.toggle('active', selected);
    if (selected) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  document.body.prepend(content);
  bindNavigation();
  bindSearch();
}

function button(label, action, className = 'dashboard-text-button') {
  const control = el('button', className, label);
  control.type = 'button';
  control.addEventListener('click', action);
  return control;
}

function message(target, title, detail, retry) {
  target.replaceChildren();
  const heading = el('strong', undefined, title);
  target.append(heading);
  if (detail) target.append(el('p', 'dashboard-muted', detail));
  if (retry) target.append(button('Try again', retry));
}

function setNavOpen(open) {
  const sidebar = $('dashboard-sidebar');
  const focusWasInside = sidebar.contains(document.activeElement);
  if (open) lastNavFocus = document.activeElement;
  sidebar.classList.toggle('is-open', open);
  sidebar.inert = window.matchMedia('(max-width: 900px)').matches && !open;
  $('dashboard-main-wrap').inert = open;
  $('nav-backdrop').hidden = !open;
  $('nav-open').setAttribute('aria-expanded', String(open));
  document.body.classList.toggle('drawer-open', open);
  if (open) $('nav-close').focus();
  else if (lastNavFocus && focusWasInside) lastNavFocus.focus();
}

function setProfileOpen(open) {
  const focusWasInside = $('profile-menu').contains(document.activeElement);
  $('profile-menu').classList.toggle('is-open', open);
  $('profile-menu').inert = !open;
  $('profile-menu').setAttribute('aria-hidden', String(!open));
  $('profile-toggle').setAttribute('aria-expanded', String(open));
  if (open) $('profile-menu').querySelector('a').focus();
  else if (focusWasInside) $('profile-toggle').focus();
}

function bindNavigation() {
  $('nav-open').addEventListener('click', () => setNavOpen(true));
  $('nav-close').addEventListener('click', () => setNavOpen(false));
  $('nav-backdrop').addEventListener('click', () => setNavOpen(false));
  $('profile-toggle').addEventListener('click', () => {
    setProfileOpen(!$('profile-menu').classList.contains('is-open'));
  });
  document.addEventListener('pointerdown', (event) => {
    if (
      $('profile-menu').classList.contains('is-open') &&
      !event.target.closest('.profile-control')
    ) {
      setProfileOpen(false);
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      if ($('profile-menu').classList.contains('is-open')) setProfileOpen(false);
      if ($('dashboard-sidebar').classList.contains('is-open')) setNavOpen(false);
    }
    if (event.key !== 'Tab' || !$('dashboard-sidebar').classList.contains('is-open')) return;
    const focusable = [...$('dashboard-sidebar').querySelectorAll('a, button')];
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
  window.matchMedia('(min-width: 901px)').addEventListener('change', (event) => {
    if (event.matches) setNavOpen(false);
    $('dashboard-sidebar').inert =
      !event.matches && !$('dashboard-sidebar').classList.contains('is-open');
  });
  $('dashboard-sidebar').inert = window.matchMedia('(max-width: 900px)').matches;

  $('profile-logout').addEventListener('click', async () => {
    const control = $('profile-logout');
    const errorBox = $('logout-error');
    control.disabled = true;
    errorBox.hidden = true;
    try {
      await logout();
      setAccessToken(null);
      window.location.assign('/index.html');
    } catch (error) {
      errorBox.textContent = describeApiError(error);
      errorBox.hidden = false;
      control.disabled = false;
    }
  });
}

async function catalog() {
  if (!catalogPromise) {
    catalogPromise = listCourses()
      .then((courses) => Promise.all(courses.map((course) => getCourse(course.slug))))
      .catch((error) => {
        catalogPromise = null;
        throw error;
      });
  }
  return catalogPromise;
}

async function runSearch(event) {
  event.preventDefault();
  const query = $('search-query').value.trim().toLocaleLowerCase();
  const panel = $('search-results');
  const body = $('search-results-body');
  panel.hidden = false;
  if (query.length < 2) {
    message(body, 'Enter at least two characters.', 'Search covers published courses and lessons.');
    return;
  }
  message(body, 'Searching…', 'Search covers published courses and lessons.');
  try {
    const courses = await catalog();
    if (panel.hidden || query !== $('search-query').value.trim().toLocaleLowerCase()) return;
    const matches = [];
    for (const course of courses) {
      if (
        `${course.title} ${course.description} ${course.level}`.toLocaleLowerCase().includes(query)
      ) {
        matches.push({
          title: course.title,
          label: `Course · ${course.level}`,
          href: `/course.html?slug=${encodeURIComponent(course.slug)}`,
        });
      }
      for (const lesson of course.lessons) {
        if (`${lesson.title} ${lesson.summary}`.toLocaleLowerCase().includes(query)) {
          matches.push({
            title: lesson.title,
            label: `Lesson · ${course.title}`,
            href: `/lesson.html?slug=${encodeURIComponent(lesson.slug)}`,
          });
        }
      }
    }
    body.replaceChildren();
    if (matches.length === 0) {
      message(
        body,
        'No matching courses or lessons.',
        'Try another term. Word and topic search is not available yet.',
      );
      return;
    }
    const list = el('ul', 'search-list');
    for (const match of matches) {
      const link = el('a', undefined, match.title);
      link.href = match.href;
      const item = el('li');
      item.append(link, el('small', undefined, match.label));
      list.append(item);
    }
    body.append(
      list,
      el('p', 'dashboard-muted search-note', 'Word and topic search is not available yet.'),
    );
  } catch (error) {
    message(body, 'Search is unavailable.', describeApiError(error), () => {
      $('dashboard-search').requestSubmit();
    });
  }
}

function bindSearch() {
  $('dashboard-search').addEventListener('submit', runSearch);
  $('search-close').addEventListener('click', () => {
    $('search-results').hidden = true;
    $('search-query').focus();
  });
}

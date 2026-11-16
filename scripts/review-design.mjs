// Isolated visual/interaction review. No production API, accounts or database.
// Uses installed Chrome and Node's WebSocket; no browser dependency or build step.
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { resolve, extname, relative } from 'node:path';
import assert from 'node:assert/strict';

const out = resolve('reports/design-review');
await mkdir(out, { recursive: true });
const user = { id: 'visual-review', displayName: 'Review Learner', email: 'review@example.invalid', englishLevel: 'A1', language: 'en', level: 1, xp: 120 };
const words = [
  ['environment', 'навколишнє середовище'], ['journey', 'подорож'], ['opportunity', 'можливість'], ['knowledge', 'знання'], ['confidence', 'впевненість'],
].map(([word, translation], i) => ({ id: `word-${i}`, wordId: `word-${i}`, word, translation, example: `Practise the word ${word}.`, learned: false, dueAt: '2026-01-01T00:00:00Z', courseId: 'course', courseTitle: 'English Basics', level: 'A1' }));
const lesson = { id: 'lesson', slug: 'review-lesson', title: 'Present Simple', summary: 'Talk about everyday habits.', theory: 'Use the present simple for habits.\n\n- I work every day.\n- She works every day.', position: 1, estimatedMinutes: 15, courseId: 'course', courseSlug: 'review-course', courseTitle: 'English Basics', level: 'A1', exercises: [{ id: 'exercise', type: 'single_choice', prompt: 'She ___ to school every day.', options: [{ id: '1', text: 'go' }, { id: '2', text: 'goes' }, { id: '3', text: 'going' }], position: 1, points: 10 }] };
const course = { id: 'course', slug: 'review-course', title: 'English Basics', description: 'Build confidence with everyday English.', level: 'A1', lessonsCount: 1, lessonsTotal: 1, lessons: [lesson] };
const progress = { lessonId: 'lesson', startedAt: '2026-01-01T00:00:00Z', completed: false, exercisesTotal: 1, exercisesCompleted: 0, xpEarned: 0, exercises: [{ exerciseId: 'exercise', attempts: 0, completed: false }] };
let session;
const requests = [];
const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname.startsWith('/api/v1/')) {
    requests.push({ path: url.pathname, method: req.method });
    const p = url.pathname.slice(7); let result;
    if (p === '/users/me') result = user;
    else if (p === '/auth/refresh') result = { accessToken: 'isolated-fixture' };
    else if (p === '/ai/status') result = { enabled: false };
    else if (p === '/courses') result = [course];
    else if (p.endsWith('/progress') && p.startsWith('/courses/')) result = { courseId: 'course', lessonsTotal: 1, lessonsStarted: 1, lessonsCompleted: 0, lessons: [{ lessonId: 'lesson', slug: lesson.slug, status: 'in_progress' }] };
    else if (p.startsWith('/courses/')) result = course;
    else if (p.endsWith('/progress') || p.endsWith('/start')) result = progress;
    else if (p.startsWith('/lessons/')) result = lesson;
    else if (p === '/progress/me') result = { courses: [{ ...course, lessonsStarted: 1, lessonsCompleted: 0 }], xp: 120, lessonsCompleted: 0 };
    else if (p === '/streaks/me') result = { currentStreak: 3, longestStreak: 5, activeToday: true };
    else if (p === '/vocabulary/stats') result = { total: words.length, learned: 0, due: words.length };
    else if (p.includes('/flashcards/sessions')) {
      if (req.method === 'POST' && p.endsWith('/sessions')) {
        let body = ''; for await (const chunk of req) body += chunk;
        const input = JSON.parse(body); session = { sessionId: 'review-session', source: input.source, status: 'active', testReady: false, total: 2, cards: words.slice(0,2) };
      }
      session ??= { sessionId: 'review-session', source: 'course_words', status: 'active', testReady: false, total: 2, cards: words.slice(0,2) };
      if (p.endsWith('/complete')) session = { ...session, testReady: true, status: 'completed' };
      result = session;
    } else if (p === '/vocabulary' || p === '/vocabulary/course-words') result = words;
    else if (p === '/leaderboard') result = { total: 3, entries: ['Review Learner', 'Second Learner', 'Third Learner'].map((displayName, i) => ({ rank: i + 1, displayName, xp: 120 - i * 20, lessonsCompleted: 3 - i, streak: 3, isCurrentUser: !i })), currentUser: { rank: 1 } };
    else { res.writeHead(404); res.end(JSON.stringify({ message: 'Unknown fixture route', path: p })); return; }
    res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(result)); return;
  }
  try {
    const file = resolve('frontend', '.' + decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname));
    if (relative(resolve('frontend'), file).startsWith('..')) throw new Error('Invalid path');
    res.setHeader('Content-Type', ({ '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.ttf': 'font/ttf' })[extname(file)] || 'application/octet-stream');
    res.end(await readFile(file));
  } catch { res.writeHead(404); res.end(); }
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${server.address().port}`;
const profile = resolve(out, `chrome-${Date.now()}`);
const chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], { windowsHide: true, stdio: 'ignore' });
const delay = ms => new Promise(r => setTimeout(r, ms));
let ws;
try {
  let port;
  for (let i=0;i<100;i++) { try { port = (await readFile(resolve(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]; break; } catch { await delay(100); } }
  assert.ok(port, 'Chrome DevTools started');
  const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  ws = new WebSocket(targets.find(t => t.type === 'page').webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r, { once:true }));
  let id=0; const pending = new Map(); const errors=[];
  ws.addEventListener('message', event => { const m=JSON.parse(event.data); if (m.id) { const task=pending.get(m.id); pending.delete(m.id); m.error ? task.reject(new Error(m.error.message)) : task.resolve(m.result); } else if(m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails); });
  const send = (method, params={}) => new Promise((resolve,reject) => { const n=++id; pending.set(n,{resolve,reject}); ws.send(JSON.stringify({id:n,method,params})); });
  const evaluate = async expression => { const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true}); if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value; };
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setEmulatedMedia', { features:[{name:'prefers-reduced-motion',value:'reduce'}] });
  const sizes = [];
  const size = async width => send('Emulation.setDeviceMetricsOverride',{width,height:1024,deviceScaleFactor:1,mobile:false});
  const capture = async name => {
    await evaluate('document.fonts.ready'); await delay(150);
    const dimensions=await evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight})');
    assert.ok(dimensions.scroll <= dimensions.width, `${name}: no horizontal overflow (${dimensions.scroll}/${dimensions.width})`);
    sizes.push({name,...dimensions});
    const {data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
    await writeFile(resolve(out,`${name}.png`),Buffer.from(data,'base64'));
  };
  const go = async path => { await send('Page.navigate',{url:origin+path}); await delay(650); };
  const click = async selector => { assert.ok(await evaluate(`!!document.querySelector(${JSON.stringify(selector)})`),selector); await evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`); await delay(100); };
  const clickText = async text => { assert.ok(await evaluate(`(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.includes(${JSON.stringify(text)}));if(!b)return false;b.click();return true})()`),text); await delay(150); };
  await size(1280);
  for(const [name,path] of [['team','/team.html'],['dashboard','/dashboard.html'],['settings','/settings.html'],['login','/login.html'],['signup','/register.html'],['leaderboard','/leaderboard.html'],['my-words','/vocabulary.html'],['course-words','/course-words.html'],['lesson-theory','/lesson.html?slug=review-lesson'],['lesson-practice','/lesson.html?slug=review-lesson&tab=practice'],['lesson-test','/lesson.html?slug=review-lesson&tab=test'],['lesson-vocabulary','/lesson.html?slug=review-lesson&tab=vocabulary'],['course','/course.html?slug=review-course']]) {
    await go(path); await capture(name);
  }
  assert.equal(requests.filter(r=>r.path==='/api/v1/courses/review-course/progress').length,1,'Course uses one batch snapshot');
  assert.equal(requests.filter(r=>r.path==='/api/v1/lessons/review-lesson/progress').length,4,'No per-lesson reads from course page');
  await go('/practice.html?session=review-session&mode=choice'); await capture('cards-workspace');
  await click('#focus-toggle'); await capture('cards-focus'); await click('#focus-toggle');
  await click('.flashcard-turn'); await capture('cards-revealed'); await clickText('Next word'); await click('.flashcard-turn'); await clickText('Test my memory');
  await capture('multiple-choice');
  assert.ok(await evaluate("document.querySelector('.study-answer-tray .lesson-button-primary').disabled"),'Check disabled before selection');
  await click('.word-choice'); await clickText('Check Answer'); await capture('choice-feedback'); await clickText('Next word'); await clickText('Skip'); await clickText('See my results'); await capture('summary');
  await go('/practice.html?session=review-session&mode=letters'); await click('.flashcard-turn'); await clickText('Next word'); await click('.flashcard-turn'); await clickText('Test my memory'); await capture('missing-letters');
  await go('/practice.html?session=review-session&mode=write'); await click('.flashcard-turn'); await clickText('Next word'); await click('.flashcard-turn'); await clickText('Test my memory'); await capture('write-word');
  await size(390);
  for(const [name,path] of [['team','/team.html'],['dashboard','/dashboard.html'],['settings','/settings.html'],['login','/login.html'],['course-words','/course-words.html'],['lesson-test','/lesson.html?slug=review-lesson&tab=test'],['cards','/practice.html?session=review-session']]) { await go(path); await capture(`${name}-390`); }
  assert.deepEqual(errors,[],'No browser runtime exceptions');
  await writeFile(resolve(out,'review.json'),JSON.stringify({ fixture:true, sizes,requests,errors },null,2));
  console.log(`PASS: ${sizes.length} browser captures; interactions, overflow, runtime and batch-request checks. ${out}`);
} finally { ws?.close(); chrome.kill(); server.close(); }

import { mountHeader } from './layout.js';
import { redirectIfSignedIn } from './session.js';

// Signed-in learners land on the dashboard; visitors see the landing page.
if (!(await redirectIfSignedIn())) mountHeader('home', null);

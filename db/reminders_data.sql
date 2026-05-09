-- ============================================================
-- REMINDER APP — REMINDER CONTENT
-- ============================================================
-- HOW TO ADD MORE REMINDERS:
--   1. Add a new INSERT block below following the same pattern.
--   2. Re-run this file against the database, OR insert individually.
--   3. The backend picks one at random from active=TRUE rows.
-- ============================================================

-- ── CATEGORIES ───────────────────────────────────────────────
INSERT INTO categories (name, description, color) VALUES
    ('Productivity',  'Work habits, focus, and deep work',         '#F59E0B'),
    ('Mindset',       'Mental models and thinking frameworks',     '#6366F1'),
    ('Health',        'Physical and mental wellbeing',             '#10B981'),
    ('Relationships', 'Communication and connection with others',  '#EC4899'),
    ('Finance',       'Money, investment, and financial habits',   '#14B8A6'),
    ('Philosophy',    'Existential and stoic reflections',         '#8B5CF6'),
    ('Learning',      'Study, growth, and skill acquisition',      '#F97316')
ON CONFLICT (name) DO NOTHING;

-- ── REMINDERS ────────────────────────────────────────────────
-- Format: (category_id, title, body, author, tags, priority)
-- category_id: 1=Productivity 2=Mindset 3=Health 4=Relationships 5=Finance 6=Philosophy 7=Learning

INSERT INTO reminders (category_id, title, body, author, tags, priority) VALUES

-- ── Productivity ─────────────────────────────────────────────
(1, 'Eat the frog',
 'Do the most difficult, most-dreaded task first thing in the morning. '
 'Everything else will feel easy by comparison.',
 'Brian Tracy', ARRAY['focus','morning'], 3),

(1, 'Time-block your calendar',
 'Unscheduled time gets consumed by other people''s priorities. '
 'Block deep-work sessions as if they were meetings you cannot cancel.',
 NULL, ARRAY['calendar','deep-work'], 3),

(1, 'Single-tasking over multi-tasking',
 'Every context switch costs 20–30 minutes of recovery time. '
 'Close every tab not related to your current task.',
 NULL, ARRAY['focus','flow'], 2),

(1, 'The two-minute rule',
 'If a task will take less than two minutes, do it now. '
 'Deferring small tasks creates invisible overhead in your mind.',
 'David Allen', ARRAY['gtd','tasks'], 2),

(1, 'Weekly review — today',
 'Spend 30 minutes reviewing what you accomplished this week, '
 'what is outstanding, and what your top three priorities are for next week.',
 NULL, ARRAY['review','planning'], 3),

(1, 'Protect your peak hours',
 'Identify the two to three hours per day when your cognition is sharpest. '
 'Guard them ruthlessly — no meetings, no email, no distractions.',
 NULL, ARRAY['energy','focus'], 3),

(1, 'Done is better than perfect (first draft)',
 'Ship the 80% version. Iteration improves; perfectionism paralysis never ships.',
 NULL, ARRAY['shipping','perfectionism'], 2),

-- ── Mindset ──────────────────────────────────────────────────
(2, 'You are the average of your environment',
 'Audit your inputs this week: what you read, who you talk to, what media you consume. '
 'Each one is silently shaping your thinking.',
 NULL, ARRAY['environment','habits'], 2),

(2, 'Inversion thinking',
 'To achieve a goal, ask: what would guarantee I fail? '
 'Then avoid those things with as much energy as you pursue success.',
 'Charlie Munger', ARRAY['mental-models','strategy'], 3),

(2, 'Response, not reaction',
 'Between stimulus and response there is space. '
 'In that space is your power to choose. In your response lies growth.',
 'Viktor Frankl', ARRAY['stoicism','self-control'], 3),

(2, 'Embrace the discomfort signal',
 'Discomfort is a directional signal, not a stop sign. '
 'It points toward growth. Lean into it deliberately.',
 NULL, ARRAY['growth','resilience'], 2),

(2, 'First-principles thinking',
 'Break the problem down to its fundamental truths, '
 'then reason up from there. Do not default to analogy.',
 'Elon Musk', ARRAY['mental-models','reasoning'], 3),

-- ── Health ───────────────────────────────────────────────────
(3, 'Sleep is non-negotiable',
 'A sleep-deprived brain has the same decision-making impairment as a drunk one. '
 'Protect 7–9 hours as a performance requirement, not a luxury.',
 'Matthew Walker', ARRAY['sleep','performance'], 3),

(3, 'Hydration check',
 'You are likely mildly dehydrated right now. '
 'Drink a full glass of water before your next meal. '
 'Even 2% dehydration reduces cognitive performance noticeably.',
 NULL, ARRAY['hydration','health'], 1),

(3, 'Walk — the underrated tool',
 'A 20-minute walk reduces cortisol, boosts BDNF, and clears decision fatigue. '
 'Schedule one walk today without your phone.',
 NULL, ARRAY['exercise','mental-health'], 2),

(3, 'Digital sunset',
 'Stop all screens 60 minutes before sleep. '
 'Blue light suppresses melatonin for up to three hours after exposure.',
 NULL, ARRAY['sleep','habits'], 2),

(3, 'Track what you eat for one week',
 'You cannot manage what you do not measure. '
 'Log your food for one week — not to diet, but to see reality clearly.',
 NULL, ARRAY['nutrition','awareness'], 2),

-- ── Relationships ─────────────────────────────────────────────
(4, 'Reach out to one person this week',
 'Relationships decay from neglect. '
 'Send a genuine message to one person you have not spoken to in 30+ days.',
 NULL, ARRAY['connection','outreach'], 2),

(4, 'Listen without preparing your reply',
 'Most people listen to respond. '
 'In your next meaningful conversation, listen only to understand.',
 NULL, ARRAY['communication','empathy'], 3),

(4, 'Express gratitude directly',
 'Think of someone who has positively impacted your life. '
 'Tell them specifically what they did and why it mattered. Today.',
 NULL, ARRAY['gratitude','communication'], 2),

(4, 'Set one boundary clearly',
 'Unclear boundaries create resentment. '
 'Identify one relationship where a boundary is needed and state it calmly and directly.',
 NULL, ARRAY['boundaries','communication'], 2),

-- ── Finance ───────────────────────────────────────────────────
(5, 'Review your subscriptions',
 'List every recurring charge this week. '
 'Cancel anything you have not actively used in the past 30 days.',
 NULL, ARRAY['expenses','audit'], 2),

(5, 'Pay yourself first',
 'Before spending anything, transfer your savings amount. '
 'Willpower is finite; automation is permanent.',
 'George Clason', ARRAY['savings','automation'], 3),

(5, 'Net worth — monthly snapshot',
 'Calculate your net worth today: assets minus liabilities. '
 'Tracking it monthly turns an abstraction into a scoreboard.',
 NULL, ARRAY['networth','tracking'], 2),

(5, 'The 24-hour rule',
 'For any non-essential purchase over ₹2,000, wait 24 hours. '
 'Most impulse desires evaporate. The real ones stay.',
 NULL, ARRAY['spending','impulse'], 2),

-- ── Philosophy ────────────────────────────────────────────────
(6, 'Memento mori',
 'You will die. Everyone you love will die. '
 'This is not morbid — it is clarifying. '
 'What does it make irrelevant? What does it make urgent?',
 'Marcus Aurelius', ARRAY['stoicism','mortality'], 3),

(6, 'Amor fati — love of fate',
 'Do not merely accept what happens — embrace it. '
 'Every obstacle, every setback, is material for growth. '
 'Ask: how can I use this?',
 'Friedrich Nietzsche', ARRAY['stoicism','resilience'], 3),

(6, 'The view from above',
 'Zoom out. Imagine looking at your city from space. '
 'Most of what you are stressed about today will be invisible in ten years.',
 'Marcus Aurelius', ARRAY['stoicism','perspective'], 2),

(6, 'Dichotomy of control',
 'Some things are in your control: your thoughts, your actions, your response. '
 'Most things are not. Focus exclusively on the former.',
 'Epictetus', ARRAY['stoicism','control'], 3),

-- ── Learning ──────────────────────────────────────────────────
(7, 'The Feynman technique',
 'Explain the concept you are learning as if teaching a child. '
 'Where your explanation breaks down, your understanding has a gap. Go fill it.',
 'Richard Feynman', ARRAY['learning','understanding'], 3),

(7, 'Spaced repetition',
 'Review material at increasing intervals: 1 day, 3 days, 1 week, 2 weeks. '
 'This exploits the forgetting curve to build durable memory.',
 NULL, ARRAY['memory','studying'], 2),

(7, 'Read with a pen',
 'Passive reading is mostly forgetting. '
 'Write one sentence per page summarizing what you just read. '
 'Your future self will thank you.',
 NULL, ARRAY['reading','retention'], 2),

(7, 'Teach it to someone',
 'After learning something new, explain it to another person — or even to yourself out loud. '
 'Teaching forces compression, which forces understanding.',
 NULL, ARRAY['teaching','learning'], 3),

(7, 'Thirty minutes of deliberate practice daily',
 'Talent is mostly accumulated deliberate practice. '
 'Thirty focused minutes every day beats three-hour sporadic sessions.',
 'Anders Ericsson', ARRAY['practice','consistency'], 3);

-- ── VERIFY SEED ──────────────────────────────────────────────
-- SELECT c.name AS category, COUNT(r.id) AS reminder_count
-- FROM categories c LEFT JOIN reminders r ON r.category_id = c.id
-- GROUP BY c.name ORDER BY c.name;

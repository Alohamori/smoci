let spoiler_rule;

const remove_spoiler_rule = () => {
  const sheet = document.styleSheets[2],
        rules = Array.from(sheet.cssRules);

  const i = rules.findIndex(r => r.selectorText == '.spoiler');
  spoiler_rule = rules[i].cssText;
  sheet.removeRule(i);
};

const qs = s => document.querySelector(s);
const qsa = s => document.querySelectorAll(s);
const hide = s => { if (e = qs(s)) e.style.display = 'none'; }
const show = (s, d) => { if (e = qs(s)) e.style.display = d || 'block'; }
const clamp = (lo, x, hi) => Math.max(Math.min(x, hi), lo);

const ls_toggle = key =>
  localStorage[key] ? localStorage.removeItem(key) : localStorage[key] = 1;

const toggle_spoilers = () => {
  if (ls_toggle('show_spoilers')) remove_spoiler_rule();
  else document.styleSheets[2].insertRule(spoiler_rule);
  qs('summary').click();
};

const toggle_notes = table => {
  (ls_toggle(`hide_${table}_notes`) ? hide : show)('.column-descriptions');
  qs('summary').click();
};

window.addEventListener('DOMContentLoaded', () => {
  if (localStorage['show_spoilers']) remove_spoiler_rule();
  if (qs('details') && localStorage[`hide_${qs('h1').innerText}_notes`])
      hide('.column-descriptions');

  qsa('a[href*="matches/"]').forEach(a => {
    if (a.innerText.indexOf(':') > -1)
      [a.innerText, a.title] = a.innerText.split(': ');
  });

  qsa('.clues div').forEach(c => {
    c.style.fontSize = `${clamp(80, 16 / c.innerText.length * 100, 100)}%`;
  });

  qsa('abbr').forEach(e => {
    const code = e.parentNode.parentNode.children[6].innerText.split(':')[0];
    e.onclick = () => window.open(`http://198.199.89.207/${code}`);
  });
});

function populate_sub(e) {
  const opt = e.options[e.selectedIndex];
  const foreign = opt.getAttribute('data-foreign');
  const sub = `#sub${e.name}`;
  if (!foreign) {
    return hide(sub);
  }

  const [ftab, ...fcols] = foreign.split(',');
  const subsel = qs(`${sub} select`);
  subsel.innerHTML = '<option>- subcolumn -</option>' + fcols.map(c => `<option>${c}</option>`).join('');
  show(sub, 'inline-block');
}

function update_main(e, targ) {
  const main = e.form[targ];
  const opt = main.options[main.selectedIndex];
  opt.value = opt.innerText + (e.value[0] != '-' ? `.${e.value}` : '');
}

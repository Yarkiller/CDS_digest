(function () {
  const root = document.documentElement;
  const themeKey = 'digest-cds-c2-theme';
  const questKey = 'digest-cds-c2-quest-dismissed';

  const savedTheme = localStorage.getItem(themeKey);
  if (savedTheme) root.setAttribute('data-theme', savedTheme);

  document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      if (next === 'dark') {
        root.removeAttribute('data-theme');
        localStorage.setItem(themeKey, 'dark');
        btn.textContent = '☀';
        btn.setAttribute('aria-label', 'Светлая тема');
      } else {
        root.setAttribute('data-theme', 'light');
        localStorage.setItem(themeKey, 'light');
        btn.textContent = '☽';
        btn.setAttribute('aria-label', 'Тёмная тема');
      }
    });
    if (root.getAttribute('data-theme') === 'light') btn.textContent = '☽';
  });

  const quest = document.getElementById('quest-banner');
  if (quest && localStorage.getItem(questKey) === '1') quest.classList.add('hidden');

  document.querySelectorAll('[data-quest-dismiss]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (quest) quest.classList.add('hidden');
      localStorage.setItem(questKey, '1');
    });
  });
})();

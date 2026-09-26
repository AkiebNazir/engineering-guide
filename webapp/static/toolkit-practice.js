'use strict';

function toolkitPracticeStrip() {
  const items = modItemsSync('toolkit');
  if (!items || !items.length) return '';
  return `
    <section class="aps">
      <header class="aps-head">
        <h2>Coding Practice: Python & Golang</h2>
        <p>Master these DevOps and Tool-Kit technologies with exactly 5 hands-on, runnable examples in both Python and Go for every single topic.</p>
      </header>
      <div class="aps-grid">
        ${items.map(t => `
          <a class="aps-card" href="#/tool-kit/${encodeURIComponent(t.id)}">
            <span class="aps-card-name">${esc(t.title)}</span>
            <span class="aps-card-counts">
              <span><b>${t.examplesCount || 10}</b> examples total</span>
              <span><b>Python / Go</b></span>
            </span>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          </a>`).join('')}
      </div>
    </section>`;
}

function renderToolkitExamples(examples) {
  if (!examples || !examples.length) return '';
  
  let html = '<h2>Examples &amp; Exercises</h2><div class="tk-examples-container">';
  
  const py = examples.filter(e => e.lang === 'python');
  const go = examples.filter(e => e.lang === 'go');
  
  const buildSection = (langTitle, list, icon) => {
    if (!list.length) return '';
    let sec = `<div class="tk-lang-section">
      <h3 class="tk-lang-title">${icon} ${langTitle}</h3>`;
    
    list.forEach((ex, idx) => {
      const name = ex.id.replace(/^[0-9]+_/, '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      const readme = ex.files.find(f => f.name === 'README.md');
      const codes = ex.files.filter(f => f.name !== 'README.md');
      
      sec += `<details class="tk-example">
        <summary>Ex ${idx + 1}: ${esc(name)}</summary>
        <div class="tk-example-content">`;
        
      if (readme) {
        sec += `<div class="prose">${renderMarkdown(readme.content)}</div>`;
      }
      
      codes.forEach(f => {
        let langClass = 'bash';
        if (f.name.endsWith('.py')) langClass = 'python';
        if (f.name.endsWith('.go')) langClass = 'go';
        if (f.name.endsWith('.yml') || f.name.endsWith('.yaml')) langClass = 'yaml';
        if (f.name === 'Dockerfile') langClass = 'dockerfile';
        
        sec += `
          <div class="tk-file">
            <span class="tk-file-name">${esc(f.name)}</span>
            <div class="code-copy code-block code-ready tk-file-content" data-lang="${langClass}">
              <pre class="cm-s-default"><code class="language-${langClass}">${esc(f.content)}</code></pre>
            </div>
          </div>`;
      });
      
      sec += `</div></details>`;
    });
    
    sec += '</div>';
    return sec;
  };
  
  const pyIcon = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.01 2.385c-4.992 0-4.832 2.158-4.832 2.158v2.338h4.945v.693H7.073S2.235 7.42 2.235 12c0 4.58 4.195 4.707 4.195 4.707h2.44v-2.88s-.03-2.923 2.924-2.923h3.582s2.613-.042 2.613-2.67V5.093s.163-2.708-6.02-2.708zm-2.585 1.63a1.11 1.11 0 1 1 0 2.22 1.11 1.11 0 0 1 0-2.22zm12.33 5.278c0-4.58-4.195-4.707-4.195-4.707h-2.44v2.88s.03 2.923-2.924 2.923h-3.582s-2.613.042-2.613 2.67v3.134s-.163 2.708 6.02 2.708c4.992 0 4.832-2.158 4.832-2.158v-2.338h-4.945v-.693h5.05s4.838.154 4.838-4.42zM14.54 20c.613 0 1.11-.497 1.11-1.11s-.497-1.11-1.11-1.11-1.11.497-1.11 1.11.497 1.11 1.11 1.11z"/></svg>';
  const goIcon = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M11.838 12.348c-.682.014-1.378-.32-1.644-1.026-.263-.7-.008-1.472.632-1.84.457-.267 1.05-.282 1.543-.075l-.265.922c-.172-.086-.39-.06-.522.062-.178.167-.145.428.066.52.197.086.442.027.568-.15l.89.444c-.267.584-.814.93-1.455 1.04-.378.062-.77.062-1.144-.06zM15.42 10.3c.097 1.185-.754 2.257-1.922 2.42-1.173.16-2.302-.638-2.527-1.802-.224-1.163.518-2.33 1.667-2.617 1.155-.29 2.417.394 2.736 1.542l-.994.275c-.13-.48-.67-.788-1.15-.653-.482.138-.804.66-.723 1.157.082.493.57.848 1.066.77.498-.075.86-.532.813-1.03l-.963.023v-.905h1.996zM18.845 12.305c-.864.088-1.666-.514-1.82-1.372-.152-.857.397-1.722 1.246-1.956.848-.235 1.776.242 2.096 1.08.063.167.108.347.126.528l-1.002.13c-.02-.274-.188-.524-.45-.605-.262-.08-.564.015-.717.234-.15.22-.116.54.08.718.194.18.514.205.738.053l.635.803c-.51.4-1.188.547-1.808.47z"/></svg>';
  
  html += buildSection('Python Examples', py, pyIcon);
  html += buildSection('Golang Examples', go, goIcon);
  
  html += '</div>';
  return html;
}

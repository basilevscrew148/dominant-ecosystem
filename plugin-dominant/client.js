window.__ModuleLoader__.load({
  id: '@local/dominant',
  factory(require) {
    const React = require('react');
    const { useEffect, useState } = React;
    const h = React.createElement;
    function DominantBadge() {
      const [goal, setGoal] = useState('');
      useEffect(() => {
        let alive = true;
        const tick = () => fetch('/plugin/dominant/state').then(r => r.json())
          .then(s => { if (alive) setGoal(s.goal || ''); }).catch(() => {});
        tick();
        const id = setInterval(tick, 10000);
        return () => { alive = false; clearInterval(id); };
      }, []);
      if (!goal) return null;
      return h('div', { style: { fontSize: '12px', color: 'var(--dsw-alias-text-secondary, #666)', padding: '2px 10px', maxWidth: 360, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }, 'Доминанта: ' + goal);
    }
    return {
      inject: ['slots'],
      apply(ctx) {
        ctx.slots.inject('conversation.composer.dock', () => ctx.slots.register({
          name: 'conversation.composer.dock', id: 'dominant', order: 20,
        }, DominantBadge));
      },
    };
  },
});

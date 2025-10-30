import { useState } from 'react';

export default function App() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');

  async function ask() {
    const r = await fetch('/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query})
    });
    const j = await r.json();
    setAnswer(j.answer);
  }

  return (
    <div style={{padding: 20}}>
      <h2>Env Research Agent</h2>
      <textarea value={query} onChange={e=>setQuery(e.target.value)} rows={5} style={{width: '100%'}}/>
      <button onClick={ask}>Ask</button>
      <pre>{answer}</pre>
    </div>
  );
}

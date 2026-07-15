import React, { useState, useEffect, useRef, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import {
  Folder, FileCode, Wand2, Upload, MessageSquare,
  FileText, CheckCircle, RefreshCw, FilePlus, FolderPlus,
  Save, Search, Cpu, FlaskConical, Sparkles, ArrowDown, Loader2, Trash2
} from 'lucide-react';
import './index.css';

// ── Agent pipeline definition ─────────────────────────────────────────────────
const PIPELINE = [
  { id: 'discovery',  label: 'Discovery Agent',   icon: Search,       color: '#60a5fa' },
  { id: 'planner',    label: 'NLP Planner',        icon: Sparkles,     color: '#a78bfa' },
  { id: 'conversion', label: 'Conversion Agent',   icon: Cpu,          color: '#34d399' },
  { id: 'qa',         label: 'QA Validator',       icon: FlaskConical, color: '#fbbf24' },
];

const STATUS_STYLES = {
  idle:     { ring: '#374151', bg: 'rgba(31,41,55,0.6)',   glow: 'none',                 pulse: false },
  thinking: { ring: '#3b82f6', bg: 'rgba(30,58,95,0.9)',   glow: '0 0 14px #3b82f660',  pulse: true  },
  done:     { ring: '#10b981', bg: 'rgba(6,78,59,0.8)',    glow: '0 0 10px #10b98150',  pulse: false },
  error:    { ring: '#ef4444', bg: 'rgba(69,10,10,0.8)',   glow: '0 0 10px #ef444450',  pulse: false },
};

// ── Thought step definitions — map LLM output patterns → human-readable steps ─
const THOUGHT_STEPS = [
  { id: 'analyze',    regex: /analyz|task require|understand|reviewing/i,        icon: '🔍', label: 'Phân tích cấu trúc module VB6' },
  { id: 'challenges', regex: /challeng|complex|difficult|obstacle|tightly coup/i, icon: '⚠️', label: 'Đánh giá độ phức tạp & rủi ro' },
  { id: 'design',     regex: /design|architect|migration strat|migration design/i,icon: '📐', label: 'Thiết kế kiến trúc C# MVC target' },
  { id: 'model',      regex: /model|viewmodel|data structure|validation/i,        icon: '📊', label: 'Định nghĩa Models & validation rules' },
  { id: 'controller', regex: /controller/i,                                       icon: '⚙️', label: 'Tạo Controller & HTTP action methods' },
  { id: 'view',       regex: /razor|\.cshtml|view\b|ui layer/i,                   icon: '🎨', label: 'Thiết kế Razor Views (UI layer)' },
  { id: 'service',    regex: /service|interface|cobol/i,                          icon: '🔌', label: 'Xây dựng COBOL service interface' },
  { id: 'output',     regex: /generated files|json output|final output|```json/i, icon: '📦', label: 'Tổng hợp & xuất output files' },
];

function detectNewSteps(text, existingIds) {
  return THOUGHT_STEPS
    .filter(s => !existingIds.has(s.id) && s.regex.test(text))
    .map(s => s.id);
}

// ── AgentNode (bottom-left overlay version — larger) ─────────────────────────
function AgentNode({ agent, state = {}, isLast }) {
  const Icon = agent.icon;
  const status = state.status || 'idle';
  const style  = STATUS_STYLES[status] || STATUS_STYLES.idle;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}>
      <div style={{
        background: style.bg,
        border: `1.5px solid ${style.ring}`,
        borderRadius: 10,
        padding: '9px 12px',
        boxShadow: style.glow,
        transition: 'all 0.3s ease',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {style.pulse && (
          <div style={{
            position: 'absolute', inset: 0,
            background: `linear-gradient(90deg, transparent, ${agent.color}20, transparent)`,
            animation: 'shimmer 1.5s infinite',
            pointerEvents: 'none',
          }} />
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Status dot */}
          <div style={{
            width: 9, height: 9, borderRadius: '50%',
            background: style.ring, flexShrink: 0,
            animation: style.pulse ? 'pulse 1.2s ease-in-out infinite' : 'none',
            boxShadow: style.pulse ? `0 0 8px ${style.ring}` : 'none',
          }} />

          <Icon size={14} style={{ color: agent.color, flexShrink: 0 }} />

          <span style={{ fontSize: 12.5, fontWeight: 600, color: '#e5e7eb', flex: 1 }}>
            {agent.label}
          </span>

          <span style={{
            fontSize: 10, fontWeight: 700, color: style.ring,
            background: `${style.ring}18`, borderRadius: 4,
            padding: '1px 5px', textTransform: 'uppercase', letterSpacing: '0.04em',
          }}>
            {status === 'thinking' ? 'active' : status === 'done' ? 'done' : status === 'error' ? 'error' : 'idle'}
          </span>
        </div>

        {state.thought && (
          <div style={{
            marginTop: 5, paddingLeft: 17,
            fontSize: 10.5, color: '#9ca3af',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            lineHeight: 1.4,
          }}>
            {state.thought}
          </div>
        )}
      </div>

      {!isLast && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '2px 0' }}>
          <div style={{ width: 1, height: 6, background: '#374151' }} />
          <div style={{ position: 'absolute', marginTop: 6 }}>
            <ArrowDown size={9} style={{ color: '#4b5563' }} />
          </div>
        </div>
      )}
    </div>
  );
}

// ── Agent Pipeline Overlay (fixed bottom-left) ────────────────────────────────
function AgentPipelineOverlay({ agentStates }) {
  return (
    <div style={{
      position: 'fixed', bottom: 16, left: 16,
      width: 270, zIndex: 200,
      background: 'rgba(10, 12, 16, 0.93)',
      backdropFilter: 'blur(16px)',
      border: '1px solid #2d333b',
      borderRadius: 14,
      padding: '12px 12px 10px',
      boxShadow: '0 8px 40px rgba(0,0,0,0.6)',
    }}>
      <div style={{
        fontSize: 10, fontWeight: 700, letterSpacing: '0.1em',
        color: '#6b7280', textTransform: 'uppercase',
        display: 'flex', alignItems: 'center', gap: 5,
        marginBottom: 10, paddingBottom: 8,
        borderBottom: '1px solid #1f2937',
      }}>
        <Wand2 size={10} style={{ color: '#a78bfa' }} />
        Agent Pipeline
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {PIPELINE.map((agent, i) => (
          <AgentNode
            key={agent.id}
            agent={agent}
            state={agentStates[agent.id]}
            isLast={i === PIPELINE.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

// ── Thinking Steps Card (shown in chat instead of raw LLM text) ───────────────
function ThinkingStepsCard({ stepIds }) {
  const steps = stepIds.map(id => THOUGHT_STEPS.find(s => s.id === id)).filter(Boolean);
  const lastIdx = steps.length - 1;

  return (
    <div>
      <div style={{
        fontSize: 10, color: '#a78bfa', fontWeight: 700,
        marginBottom: 8, display: 'flex', alignItems: 'center', gap: 5,
      }}>
        <span style={{ animation: 'pulse 1.5s infinite' }}>🤖</span>
        AGENT THINKING
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {steps.length === 0 && (
          <div style={{ fontSize: 11, color: '#6b7280', display: 'flex', alignItems: 'center', gap: 6 }}>
            <Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} />
            Đang khởi tạo...
          </div>
        )}
        {steps.map((step, idx) => {
          const isActive = idx === lastIdx;
          return (
            <div key={step.id} style={{
              display: 'flex', alignItems: 'center', gap: 8,
              opacity: isActive ? 1 : 0.6,
              animation: isActive ? 'fadeIn 0.3s ease' : 'none',
            }}>
              <span style={{ fontSize: 13, flexShrink: 0 }}>{step.icon}</span>
              <span style={{
                fontSize: 11.5, flex: 1, lineHeight: 1.4,
                color: isActive ? '#e5e7eb' : '#9ca3af',
                fontWeight: isActive ? 500 : 400,
              }}>
                {step.label}
              </span>
              {isActive
                ? <div style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: '#a78bfa',
                    animation: 'pulse 1s infinite', flexShrink: 0,
                  }} />
                : <span style={{ fontSize: 11, color: '#10b981', flexShrink: 0 }}>✓</span>
              }
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
function App() {
  const [fileTree,     setFileTree]     = useState([]);
  const [activeFile,   setActiveFile]   = useState(null);
  const [fileContent,  setFileContent]  = useState('// Select a file to view code');
  const [messages,     setMessages]     = useState([{ sender: 'system', text: 'System Orchestrator: Ready.' }]);
  const [plan,         setPlan]         = useState('');
  const [feedback,     setFeedback]     = useState('');
  const [isDragging,   setIsDragging]   = useState(false);
  const [chatInput,    setChatInput]    = useState('');
  const [streamSource, setStreamSource] = useState(null);
  const [saveStatus,   setSaveStatus]   = useState('idle');
  const [agentStates,  setAgentStates]  = useState(
    Object.fromEntries(PIPELINE.map(a => [a.id, { status: 'idle', thought: '' }]))
  );
  const chatEndRef        = useRef(null);
  const thinkingBufferRef = useRef('');        // Silent accumulator — no re-renders per char
  const detectedStepsRef  = useRef(new Set()); // Track which steps already shown

  // ── Workspace ───────────────────────────────────────────────────────────────
  const loadWorkspace = useCallback(async () => {
    try {
      const res = await fetch('/api/workspace/files');
      setFileTree(await res.json());
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { loadWorkspace(); }, [loadWorkspace]);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // ── SSE / Orchestrator ──────────────────────────────────────────────────────
  const startOrchestrator = (promptText) => {
    if (streamSource) streamSource.close();

    // Reset thinking state for new run
    thinkingBufferRef.current = '';
    detectedStepsRef.current  = new Set();

    setMessages(prev => [...prev, { sender: 'user', text: promptText }]);

    const source = new EventSource(`/api/agent/stream?prompt=${encodeURIComponent(promptText)}`);
    setStreamSource(source);

    source.onmessage = (e) => {
      const data = JSON.parse(e.data);

      switch (data.type) {
        case 'info':
          setMessages(prev => [...prev, { sender: 'system', text: data.message }]);
          break;

        case 'review_required':
          setPlan(data.plan);
          setActiveFile('Implementation Plan');
          break;

        case 'module_status':
          // Reset thinking buffer per module
          if (data.status === 'converting') {
            thinkingBufferRef.current = '';
            detectedStepsRef.current  = new Set();
          }
          setMessages(prev => [...prev, {
            sender: 'system',
            text: `Module ${data.module}: ${data.status}${data.retry_count > 0 ? ` (retry ${data.retry_count})` : ''}`,
          }]);
          break;

        case 'text_delta': {
          // Accumulate silently, detect steps, update thinking card
          thinkingBufferRef.current += data.content;
          const newStepIds = detectNewSteps(thinkingBufferRef.current, detectedStepsRef.current);

          if (newStepIds.length > 0) {
            newStepIds.forEach(id => detectedStepsRef.current.add(id));
            const allStepIds = Array.from(detectedStepsRef.current);

            setMessages(prev => {
              const last = prev[prev.length - 1];
              if (last?.sender === 'agent_thinking') {
                return [...prev.slice(0, -1), { ...last, steps: allStepIds }];
              }
              return [...prev, { sender: 'agent_thinking', steps: allStepIds }];
            });
          } else {
            // Ensure at least an empty thinking card exists
            setMessages(prev => {
              const last = prev[prev.length - 1];
              if (!last || last.sender !== 'agent_thinking') {
                return [...prev, { sender: 'agent_thinking', steps: [] }];
              }
              return prev;
            });
          }
          break;
        }

        case 'agent_update':
          setAgentStates(prev => ({
            ...prev,
            [data.agent]: { status: data.status, thought: data.thought || '' },
          }));
          break;

        case 'qa_start':
          setMessages(prev => [...prev, { sender: 'system', text: `🔬 QA đang kiểm tra ${data.module}...` }]);
          break;

        case 'qa_pass':
          setMessages(prev => [...prev, { sender: 'system', text: `✅ QA passed — ${data.module}` }]);
          break;

        case 'qa_fail':
          setMessages(prev => [...prev, {
            sender: 'system',
            text: `❌ QA failed — ${data.module}: ${(data.errors || []).join('; ')}`,
          }]);
          break;

        case 'file_created':
          setMessages(prev => [...prev, {
            sender: 'system',
            text: `📄 ${data.path}`,
            isFile: true,
            filePath: data.path,
          }]);
          loadWorkspace();
          break;

        case 'file_update':
          loadWorkspace();
          break;

        case 'report_created':
          setMessages(prev => [...prev, {
            sender: 'system',
            text:   `${data.module}`,
            isReport: true,
            reportPath: data.path,
            module: data.module,
          }]);
          loadWorkspace();
          break;

        case 'done':
          setMessages(prev => [...prev, { sender: 'system', text: '🎉 Migration hoàn thành!' }]);
          loadWorkspace();
          source.close();
          break;

        default:
          break;
      }
    };

    source.onerror = () => source.close();
  };

  useEffect(() => () => { if (streamSource) streamSource.close(); }, [streamSource]);

  // ── File utils ──────────────────────────────────────────────────────────────
  const getLanguage = (path) => {
    if (!path) return 'plaintext';
    const ext = path.split('.').pop().toLowerCase();
    if (['frm','bas','cls'].includes(ext)) return 'vb';
    if (['cbl','cpy'].includes(ext)) return 'cobol';
    if (ext === 'cs') return 'csharp';
    if (ext === 'json') return 'json';
    if (ext === 'md') return 'markdown';
    return 'plaintext';
  };

  const openFile = async (path) => {
    setActiveFile(path);
    setSaveStatus('idle');
    try {
      const res = await fetch(`/api/workspace/file?path=${encodeURIComponent(path)}`);
      setFileContent(await res.text());
    } catch (e) { console.error(e); }
  };

  const saveFile = useCallback(async () => {
    if (!activeFile || activeFile === 'Implementation Plan') return;
    setSaveStatus('saving');
    try {
      const res = await fetch('/api/workspace/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: activeFile, content: fileContent }),
      });
      setSaveStatus(res.ok ? 'saved' : 'error');
    } catch { setSaveStatus('error'); }
    setTimeout(() => setSaveStatus('idle'), 2000);
  }, [activeFile, fileContent]);

  useEffect(() => {
    const h = (e) => { if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveFile(); } };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [saveFile]);

  // ── Upload / Drag ───────────────────────────────────────────────────────────
  const uploadFile = async (file) => {
    // Only clear /new/ output — keep source files
    setMessages(prev => [...prev, { sender: 'system', text: `📂 Adding ${file.name} to source...` }]);
    const fd = new FormData(); fd.append('file', file);
    const res = await fetch('/api/ingest/upload', { method: 'POST', body: fd });
    setMessages(prev => [...prev, {
      sender: 'system',
      text: res.ok ? `✅ ${file.name} added. Enter NLP prompt to migrate.` : '❌ Upload failed.',
    }]);
    if (res.ok) loadWorkspace();
  };

  const clearOutput = async () => {
    await fetch('/api/workspace/reset', { method: 'POST' });
    setMessages(prev => [...prev, { sender: 'system', text: '🧹 Output cleared (source files kept).' }]);
    loadWorkspace();
  };

  const clearAll = async () => {
    if (!window.confirm('Xóa toàn bộ workspace kể cả source files?')) return;
    await fetch('/api/workspace/reset-all', { method: 'POST' });
    setMessages([{ sender: 'system', text: '🗑️ Workspace cleared completely.' }]);
    setActiveFile(null); setFileContent('// Select a file to view code');
    loadWorkspace();
  };

  const handleUpload    = (e) => { const f = e.target.files?.[0]; if (f) uploadFile(f); };
  const handleDragOver  = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = ()  => setIsDragging(false);
  const handleDrop      = (e) => { e.preventDefault(); setIsDragging(false); const f = e.dataTransfer.files?.[0]; if (f) uploadFile(f); };

  // ── Plan review ─────────────────────────────────────────────────────────────
  const handleVerify = async () => {
    setActiveFile(null);
    await fetch('/api/agent/verify', { method: 'POST' });
    setMessages(prev => [...prev, { sender: 'user', text: 'Plan approved. Migration running...' }]);
  };

  const handleFeedback = async () => {
    if (!feedback) return;
    setActiveFile(null);
    await fetch('/api/agent/feedback', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback }),
    });
    setMessages(prev => [...prev, { sender: 'user', text: `Feedback: ${feedback}` }]);
    setFeedback('');
  };

  // ── Create item ─────────────────────────────────────────────────────────────
  const handleCreateItem = async (type) => {
    const name = prompt(`Tên ${type} mới:`);
    if (!name) return;
    const res = await fetch('/api/workspace/create', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: name, type }),
    });
    if (res.ok) loadWorkspace(); else alert(`Không thể tạo ${type}`);
  };

  // ── File tree render ────────────────────────────────────────────────────────
  const renderTree = (nodes) => nodes.map(node => (
    <div key={node.path} style={{ marginLeft: 10 }}>
      <div
        onClick={() => node.type === 'file' && openFile(node.path)}
        style={{
          display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer',
          padding: '3px 7px', borderRadius: 5, fontSize: 12,
          color: activeFile === node.path ? '#e6edf3' : '#8b949e',
          background: activeFile === node.path ? '#21262d' : 'transparent',
          transition: 'all 0.12s',
        }}
        onMouseEnter={e => { if (activeFile !== node.path) e.currentTarget.style.background = '#161b22'; }}
        onMouseLeave={e => { if (activeFile !== node.path) e.currentTarget.style.background = 'transparent'; }}
      >
        {node.type === 'folder'
          ? <Folder size={12} style={{ color: '#60a5fa', flexShrink: 0 }} />
          : <FileCode size={12} style={{ color: '#6b7280', flexShrink: 0 }} />}
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{node.name}</span>
      </div>
      {node.children && renderTree(node.children)}
    </div>
  ));

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @keyframes pulse   { 0%,100%{opacity:1} 50%{opacity:0.35} }
        @keyframes shimmer { 0%{transform:translateX(-100%)} 100%{transform:translateX(200%)} }
        @keyframes fadeIn  { from{opacity:0;transform:translateY(5px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin    { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', system-ui, sans-serif; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
        input, textarea { font-family: inherit; }
      `}</style>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          height: '100vh', width: '100%', display: 'flex', overflow: 'hidden',
          background: '#0d1117', color: '#e6edf3',
          fontFamily: "'Inter', system-ui, sans-serif",
          position: 'relative',
        }}
      >
        {/* Drag overlay */}
        {isDragging && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 300,
            background: 'rgba(29,78,216,0.2)', border: '3px dashed #3b82f6',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            pointerEvents: 'none',
          }}>
            <div style={{
              background: '#0d1117', borderRadius: 14, padding: '28px 48px',
              border: '1px solid #3b82f6', display: 'flex', flexDirection: 'column',
              alignItems: 'center', gap: 10,
            }}>
              <Upload size={28} style={{ color: '#60a5fa', animation: 'pulse 1s infinite' }} />
              <span style={{ fontSize: 14, fontWeight: 600 }}>Thả file vào đây</span>
            </div>
          </div>
        )}

        {/* Agent Pipeline — fixed bottom-left overlay */}
        <AgentPipelineOverlay agentStates={agentStates} />

        {/* ════ LEFT PANE: File Tree only ════ */}
        <div style={{
          width: 220, background: '#111318', borderRight: '1px solid #1f2937',
          display: 'flex', flexDirection: 'column', flexShrink: 0,
        }}>
          <div style={{
            padding: '10px 12px 8px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            borderBottom: '1px solid #1f2937',
          }}>
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: '0.1em',
              color: '#6b7280', textTransform: 'uppercase',
              display: 'flex', alignItems: 'center', gap: 5,
            }}>
              <Folder size={10} /> Workspace
            </span>
            <div style={{ display: 'flex', gap: 6 }}>
              {[{ icon: FilePlus, type: 'file' }, { icon: FolderPlus, type: 'folder' }].map(({ icon: Icon, type }) => (
                <button key={type} onClick={() => handleCreateItem(type)} title={`New ${type}`}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280', padding: 2, display: 'flex' }}
                  onMouseEnter={e => e.currentTarget.style.color = '#e5e7eb'}
                  onMouseLeave={e => e.currentTarget.style.color = '#6b7280'}
                ><Icon size={13} /></button>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '6px 4px 120px' }}>
            {/* 120px bottom padding to avoid overlap with agent pipeline overlay */}
            {fileTree.length === 0
              ? <div style={{ fontSize: 11, color: '#4b5563', padding: '10px 12px', fontStyle: 'italic' }}>
                  Chưa có file. Upload để bắt đầu.
                </div>
              : renderTree(fileTree)}
          </div>
        </div>

        {/* ════ MIDDLE PANE: Editor / Plan ════ */}
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          background: '#0d1117', minWidth: 0,
        }}>
          {/* Tab bar */}
          <div style={{
            height: 40, background: '#161b22', borderBottom: '1px solid #21262d',
            display: 'flex', alignItems: 'center', padding: '0 12px', gap: 8, flexShrink: 0,
          }}>
            {plan && (
              <button onClick={() => setActiveFile('Implementation Plan')} style={{
                fontSize: 11, padding: '4px 10px', borderRadius: 6, cursor: 'pointer',
                border: `1px solid ${activeFile === 'Implementation Plan' ? '#7c3aed60' : '#30363d'}`,
                background: activeFile === 'Implementation Plan' ? '#2d1b6960' : '#21262d',
                color: activeFile === 'Implementation Plan' ? '#a78bfa' : '#8b949e',
                display: 'flex', alignItems: 'center', gap: 5, transition: 'all 0.15s',
              }}>
                <FileText size={11} /> Implementation Plan
              </button>
            )}

            {activeFile && activeFile !== 'Implementation Plan' && (
              <span style={{
                fontSize: 11, padding: '4px 10px', borderRadius: 6,
                border: '1px solid #30363d', background: '#161b22', color: '#e6edf3',
                maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {activeFile}
              </span>
            )}

            {activeFile && activeFile !== 'Implementation Plan' && (
              <button onClick={saveFile} title="Save (Ctrl+S)" style={{
                marginLeft: 'auto', fontSize: 11, padding: '4px 10px', borderRadius: 6,
                cursor: saveStatus === 'saving' ? 'wait' : 'pointer',
                border: `1px solid ${saveStatus === 'saved' ? '#16653480' : saveStatus === 'error' ? '#7f1d1d80' : '#30363d'}`,
                background: saveStatus === 'saved' ? '#14532d' : saveStatus === 'error' ? '#450a0a' : '#21262d',
                color: saveStatus === 'saved' ? '#86efac' : saveStatus === 'error' ? '#fca5a5' : '#8b949e',
                display: 'flex', alignItems: 'center', gap: 5, transition: 'all 0.15s',
              }}>
                {saveStatus === 'saving'
                  ? <Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} />
                  : <Save size={11} />}
                {saveStatus === 'saved' ? 'Saved!' : saveStatus === 'error' ? 'Error!' : saveStatus === 'saving' ? 'Saving...' : 'Save'}
              </button>
            )}
          </div>

          {/* Content */}
          <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
            {activeFile === 'Implementation Plan' ? (
              <div style={{
                position: 'absolute', inset: 0, overflowY: 'auto',
                padding: '32px 40px', background: '#0d1117',
                display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 860, margin: '0 auto',
              }}>
                <div style={{ borderBottom: '1px solid #21262d', paddingBottom: 16 }}>
                  <h1 style={{ fontSize: 22, fontWeight: 700, color: '#a78bfa', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <FileText size={22} /> Migration Implementation Plan
                  </h1>
                  <p style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>Generated by Orchestrator. Review and verify to run.</p>
                </div>

                <div style={{
                  background: '#161b22', border: '1px solid #21262d', borderRadius: 10,
                  padding: 20, fontFamily: 'monospace', fontSize: 12.5, lineHeight: 1.7,
                  whiteSpace: 'pre-wrap', color: '#c9d1d9',
                }}>
                  {plan}
                </div>

                <div style={{
                  background: '#161b22', border: '1px solid #30363d', borderRadius: 10,
                  padding: 20, display: 'flex', flexDirection: 'column', gap: 12,
                }}>
                  <h3 style={{ fontSize: 14, color: '#e6edf3', fontWeight: 600 }}>Review Checkpoint</h3>
                  <input
                    value={feedback} onChange={e => setFeedback(e.target.value)}
                    placeholder="Feedback để refine plan... (để trống nếu OK)"
                    style={{
                      background: '#0d1117', border: '1px solid #30363d', borderRadius: 8,
                      padding: '10px 14px', fontSize: 12.5, color: '#e6edf3', outline: 'none', width: '100%',
                    }}
                    onFocus={e => e.target.style.borderColor = '#7c3aed'}
                    onBlur={e => e.target.style.borderColor = '#30363d'}
                  />
                  <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                    <button onClick={handleFeedback} style={{
                      padding: '8px 18px', borderRadius: 8, border: '1px solid #30363d',
                      background: '#21262d', color: '#c9d1d9', fontSize: 12, cursor: 'pointer',
                      display: 'flex', alignItems: 'center', gap: 6,
                    }}>
                      <RefreshCw size={12} /> Refine Plan
                    </button>
                    <button onClick={handleVerify} style={{
                      padding: '8px 20px', borderRadius: 8, border: '1px solid #166534',
                      background: '#14532d', color: '#86efac', fontSize: 12,
                      fontWeight: 600, cursor: 'pointer',
                      display: 'flex', alignItems: 'center', gap: 6,
                      boxShadow: '0 0 16px #14532d50',
                    }}>
                      <CheckCircle size={12} /> Verify & Execute
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <Editor
                height="100%"
                theme="vs-dark"
                language={getLanguage(activeFile)}
                value={fileContent}
                onChange={(v) => setFileContent(v || '')}
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  lineHeight: 1.65,
                  scrollBeyondLastLine: false,
                  renderLineHighlight: 'gutter',
                  padding: { top: 8 },
                }}
              />
            )}
          </div>
        </div>

        {/* ════ RIGHT PANE: Agent Chat ════ */}
        <div style={{
          width: 360, background: '#111318', display: 'flex',
          flexDirection: 'column', borderLeft: '1px solid #1f2937', flexShrink: 0,
        }}>
          {/* Header */}
          <div style={{
            height: 40, background: '#161b22', borderBottom: '1px solid #21262d',
            display: 'flex', alignItems: 'center', padding: '0 14px', flexShrink: 0,
          }}>
            <Wand2 size={15} style={{ color: '#a78bfa', marginRight: 7, animation: 'pulse 2s infinite' }} />
            <span style={{ fontWeight: 600, fontSize: 13 }}>Agent Chat</span>
          </div>

          {/* Upload + Clear buttons */}
          <div style={{ padding: '10px 12px 0', background: '#0d1117', flexShrink: 0 }}>
            <div style={{ display: 'flex', gap: 6 }}>
              <label style={{
                flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                gap: 7, padding: '8px 0', background: '#1d4ed8', borderRadius: 8,
                cursor: 'pointer', fontSize: 12.5, fontWeight: 500,
                border: '1px solid #1e40af', transition: 'background 0.15s',
              }}
                onMouseEnter={e => e.currentTarget.style.background = '#1e40af'}
                onMouseLeave={e => e.currentTarget.style.background = '#1d4ed8'}
              >
                <Upload size={14} />
                Upload file / zip
                <input type="file" style={{ display: 'none' }} onChange={handleUpload} />
              </label>

              {/* Clear output only */}
              <button
                onClick={clearOutput}
                title="Xóa output /new/ (giữ source)"
                style={{
                  padding: '8px 10px', borderRadius: 8, border: '1px solid #374151',
                  background: '#1f2937', color: '#9ca3af', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 4, fontSize: 11,
                  transition: 'all 0.15s', flexShrink: 0,
                }}
                onMouseEnter={e => { e.currentTarget.style.background = '#374151'; e.currentTarget.style.color = '#e5e7eb'; }}
                onMouseLeave={e => { e.currentTarget.style.background = '#1f2937'; e.currentTarget.style.color = '#9ca3af'; }}
              >
                <RefreshCw size={12} />
                Clear
              </button>

              {/* Full clear */}
              <button
                onClick={clearAll}
                title="Xóa toàn bộ workspace"
                style={{
                  padding: '8px 10px', borderRadius: 8, border: '1px solid #7f1d1d',
                  background: '#1c0a0a', color: '#f87171', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', transition: 'all 0.15s', flexShrink: 0,
                }}
                onMouseEnter={e => { e.currentTarget.style.background = '#450a0a'; }}
                onMouseLeave={e => { e.currentTarget.style.background = '#1c0a0a'; }}
              >
                <Trash2 size={13} />
              </button>
            </div>
            <div style={{ fontSize: 10, color: '#4b5563', textAlign: 'center', margin: '5px 0 6px' }}>
              Kéo thả file • Upload thêm không xóa source cũ
            </div>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1, overflowY: 'auto', padding: '8px 10px',
            display: 'flex', flexDirection: 'column', gap: 6,
            background: '#0a0c10',
          }}>
            {messages.map((m, i) => (
              <div
                key={i}
                onClick={() => {
                  if (m.isFile)   openFile(m.filePath);
                  if (m.isReport) window.open(`/api/workspace/report?path=${encodeURIComponent(m.reportPath)}`, '_blank');
                }}
                style={{
                  padding: '9px 12px', borderRadius: 10, fontSize: 12,
                  lineHeight: 1.5, maxWidth: '92%',
                  animation: 'fadeIn 0.2s ease',
                  alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                  cursor: (m.isFile || m.isReport) ? 'pointer' : 'default',
                  background:
                    m.sender === 'user'           ? 'rgba(29,78,216,0.3)'   :
                    m.sender === 'agent_thinking' ? 'rgba(91,33,182,0.15)'  :
                    m.isReport                    ? 'rgba(139,92,246,0.15)' :
                    m.isFile                      ? 'rgba(16,185,129,0.1)'  :
                                                    '#161b22',
                  border:
                    m.sender === 'user'           ? '1px solid rgba(59,130,246,0.3)'  :
                    m.sender === 'agent_thinking' ? '1px solid rgba(139,92,246,0.2)'  :
                    m.isReport                    ? '1px solid rgba(139,92,246,0.4)'  :
                    m.isFile                      ? '1px solid rgba(16,185,129,0.3)'  :
                                                    '1px solid #21262d',
                  color:
                    m.sender === 'user'           ? '#bfdbfe' :
                    m.sender === 'agent_thinking' ? '#ddd6fe' :
                    m.isFile                      ? '#6ee7b7' :
                                                    '#c9d1d9',
                  transition: m.isFile ? 'background 0.15s' : 'none',
                }}
                onMouseEnter={e => { if (m.isFile) e.currentTarget.style.background = 'rgba(16,185,129,0.18)'; }}
                onMouseLeave={e => { if (m.isFile) e.currentTarget.style.background = 'rgba(16,185,129,0.1)'; }}
              >
                {m.sender === 'agent_thinking' ? (
                  <ThinkingStepsCard stepIds={m.steps || []} />
                ) : m.isReport ? (
                  <div>
                    <div style={{ fontSize: 9.5, color: '#a78bfa', fontWeight: 700, marginBottom: 5, display: 'flex', alignItems: 'center', gap: 5 }}>
                      📊 MIGRATION REPORT READY
                    </div>
                    <div style={{ fontWeight: 600, fontSize: 12.5, color: '#e9d5ff', marginBottom: 3 }}>
                      {m.module}
                    </div>
                    <div style={{ fontSize: 10, color: '#6b21a8', fontFamily: 'monospace', marginBottom: 8 }}>
                      {m.reportPath}
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                      <div
                        onClick={(e) => {
                          e.stopPropagation();
                          window.open(`/api/workspace/report?path=${encodeURIComponent(m.reportPath)}`, '_blank');
                        }}
                        style={{
                          display: 'inline-flex', alignItems: 'center', gap: 5,
                          background: 'linear-gradient(135deg,#7c3aed,#4f46e5)', color: '#fff',
                          fontSize: 11, fontWeight: 700, padding: '5px 12px', borderRadius: 7,
                          boxShadow: '0 0 12px rgba(124,58,237,0.4)', cursor: 'pointer'
                        }}
                      >
                        🚀 Open Report →
                      </div>
                      <div
                        onClick={(e) => {
                          e.stopPropagation();
                          window.open(`/api/workspace/download?module=${encodeURIComponent(m.module)}`, '_self');
                        }}
                        style={{
                          display: 'inline-flex', alignItems: 'center', gap: 5,
                          background: '#1f2937', color: '#e5e7eb', border: '1px solid #374151',
                          fontSize: 11, fontWeight: 700, padding: '5px 12px', borderRadius: 7,
                          cursor: 'pointer'
                        }}
                      >
                        📦 Download ZIP
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    {m.isFile && (
                      <div style={{ fontSize: 9.5, color: '#34d399', fontWeight: 700, marginBottom: 3 }}>
                        📄 FILE CREATED — click to open
                      </div>
                    )}
                    <span style={{ wordBreak: 'break-word' }}>{m.text}</span>
                  </>
                )}
              </div>


            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div style={{
            padding: '10px 12px', borderTop: '1px solid #1f2937',
            background: '#111318', flexShrink: 0,
          }}>
            <form onSubmit={e => {
              e.preventDefault();
              if (chatInput.trim()) { startOrchestrator(chatInput.trim()); setChatInput(''); }
            }} style={{ position: 'relative' }}>
              <input
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Nhập lệnh NLP migration..."
                style={{
                  width: '100%', background: '#0a0c10', border: '1px solid #21262d',
                  borderRadius: 20, padding: '10px 40px 10px 16px', fontSize: 12.5,
                  color: '#e6edf3', outline: 'none',
                }}
                onFocus={e => e.target.style.borderColor = '#4b5563'}
                onBlur={e => e.target.style.borderColor = '#21262d'}
              />
              <button type="submit" style={{
                position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280',
                padding: 4, display: 'flex',
              }}
                onMouseEnter={e => e.currentTarget.style.color = '#e6edf3'}
                onMouseLeave={e => e.currentTarget.style.color = '#6b7280'}
              >
                <MessageSquare size={15} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;

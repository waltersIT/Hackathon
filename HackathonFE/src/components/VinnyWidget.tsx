// VinnyWidget = the chat panelUI
// Currently only mock, fake chats, when backend is ready swap fakeChat() for a real fetch() to `/api/query` 
import React, { useEffect, useRef, useState } from "react";

import vinny from "../assets/vinny.png";
import vinnyFinal from "../assets/vinnyFinal.gif";

// A single chat message 
type Msg = { role: "user" | "assistant"; content: string };

/* Session storage helpers

 use sessionStorage to define sessionid that survives refresh in the tab being used
 use localStorage to keep messages/draft keyed by that sessionid
 
 In reuslt, should closing and opening widget keep messages and drafts in chat; new browser sessions start completely fresh and no chat history saved

 */

function ensureSessionId(): string {
  const KEY = "vinny_session_id";
  let sid = sessionStorage.getItem(KEY);
  if (!sid) {
    sid = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    sessionStorage.setItem(KEY, sid);
  }
  return sid;
}
function chatKeyFor(pathname: string, sessionId: string) {
  return `vinny_chat::${sessionId}::${pathname}`;
}
function draftKeyFor(pathname: string, sessionId: string) {
  return `vinny_draft::${sessionId}::${pathname}`;
}


async function realChat(user: string) {
  
  const currentAddress = window.location.href;//parse the url
  const backendPort = import.meta.env.VITE_BACKEND_PORT;
  console.log(backendPort);
  const res = await fetch(`http://localhost:${backendPort}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      question: user,
      url: currentAddress
    }),
  });
  if (!res.ok) {
    throw new Error("Failed to fetch response from backend");
  }
  return await res.json(); // should be { answer: "...", sources: [...] }

}


// export default function VinnyWidget({
//   onClose,
// }: {
//   // used when user clicks the close button '-' on modal
//   onClose?: () => void;
// }) {
export default function VinnyWidget({ onClose, stateClassName }: { onClose?: () => void; stateClassName?: string }) {


  //const [history, setHistory] = useState<Msg[]>([]);
  //const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);
  // ids for tabs session and current route
  const SESSION_ID = ensureSessionId();
  const STORAGE_KEY = chatKeyFor(location.pathname, SESSION_ID);
  const DRAFT_KEY = draftKeyFor(location.pathname, SESSION_ID);

  const [history, setHistory] = useState<Msg[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as Msg[]) : [];
    } catch { return []; }
  });
  const [input, setInput] = useState<string>(() => {
    try { return localStorage.getItem(DRAFT_KEY) || ""; } catch { return ""; }
  });

    // keep history in localStorage
  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(history)); } catch {}
  }, [history, STORAGE_KEY]);

  // draft what user type
  useEffect(() => {
    try {
      if (input) localStorage.setItem(DRAFT_KEY, input);
      else localStorage.removeItem(DRAFT_KEY);
    } catch {}
  }, [input, DRAFT_KEY]);


  // Always be present to latest message, or did we want auto scroll on opening modal?
  useEffect(() => {
    boxRef.current?.scrollTo({ top: 9e6, behavior: "auto" });
  }, [history]);

  /** Helper to format text with proper line breaks and markdown */
  function formatMessage(content: string) {
    const lines = content.split('\n');
    const parts: React.ReactNode[] = [];
    let keyCounter = 0;

    lines.forEach((line, i) => {
      // Check if this is a header (###, ##, #)
      const headerMatch = line.match(/^(#{1,3})\s+(.+)$/);
      if (headerMatch) {
        const level = headerMatch[1].length;
        const text = parseInlineContent(headerMatch[2]);
        const Tag = level === 1 ? 'h1' : level === 2 ? 'h2' : 'h3';
        parts.push(
          <Tag key={`header-${keyCounter++}`} className="vinny-markdown-header">
            {text}
          </Tag>
        );
        return;
      }

      // Check if this is a table separator line
      if (/^\|[\s-:]+\|/.test(line)) {
        parts.push(<hr key={`hr-${keyCounter++}`} className="vinny-table-separator" />);
        return;
      }

      // Check if this is a table row
      if (/^\|.+\|$/.test(line)) {
        const cells = line.split('|').filter(cell => cell.trim() !== '');
        parts.push(
          <div key={`table-row-${keyCounter++}`} className="vinny-table-row">
            {cells.map((cell, cellIdx) => (
              <span key={`cell-${cellIdx}`} className="vinny-table-cell">
                {parseInlineContent(cell.trim())}
              </span>
            ))}
          </div>
        );
        return;
      }

      // Regular text with inline formatting
      const formattedLine = parseInlineContent(line);

      parts.push(
        <span key={`line-${i}`}>
          {formattedLine}
        </span>
      );

      // Add line breaks
      if (i < lines.length - 1) {
        if (line === '') {
          parts.push(<br key={`br-${keyCounter++}`} />);
          parts.push(<br key={`br-${keyCounter++}`} />);
        } else {
          parts.push(<br key={`br-${keyCounter++}`} />);
        }
      }
    });

    return <>{parts}</>;
  }

  /** Helper to parse inline content (bold, italic) */
  function parseInlineContent(text: string): React.ReactNode[] {
    const parts: React.ReactNode[] = [];
    let keyCounter = 0;

    // Parse bold (**text**) and italic (*text*) using a single pass
    const inlineRegex = /(\*\*)(.+?)\1|(?<!\*)\*(?!\*)(.+?)\*/g;
    let lastIndex = 0;
    let match;

    while ((match = inlineRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      
      // Handle the match
      if (match[0].startsWith('**') && match[0].endsWith('**')) {
        // Bold text
        parts.push(<strong key={`bold-${keyCounter++}`}>{match[2]}</strong>);
      } else {
        // Italic text
        const italicText = match[3];
        parts.push(<em key={`italic-${keyCounter++}`}>{italicText}</em>);
      }
      
      lastIndex = match.index + match[0].length;
    }

    // Add remaining text after last match
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : [text];
  }

  /** send the user message and reply */
  async function ask() {
  const q = input.trim();
  if (!q) return;

  setInput("");
  setBusy(true);
  setHistory((h) => [...h, { role: "user", content: q }]);

  try {
    console.log(q);
    const data = await realChat(q);

    const cites = (data.sources || [])
      .slice(0, 2)
      .map((s: any) => `• ${s.title}`)
      .join("\n");

    setHistory((h) => [
      ...h,
      {
        role: "assistant",
        content: data.answer + (cites ? `\n\nSources:\n${cites}` : ""),//might take this out and have it just organically list the sources in the response
      },
    ]);
  } catch (err) {
    setHistory((h) => [
      ...h,
      { role: "assistant", content: "Error reaching Vinny." },
    ]);
  } finally {
    setBusy(false);
  }
}


  return (
    // old code if needed <div className="vinny-card" role="dialog"               aria-label="Vinny AI chat">
      <div className={`vinny-card ${stateClassName ?? ""}`} role="dialog" aria-label="Vinny AI chat">
      {/* header / logo/ title / minimize button */}
      <div className="vinny-header">
        <div className="vinny-id">
            <img 
                src={busy ? vinnyFinal : vinny}
                alt="Vinny chatbot"
                className={`vinny-logo ${busy ? "busy" : ""}`}
            />
          <strong>Vinny AI</strong>
        </div>
        <div className="vinny-header-right">
          {/*Not needed but maybe in the future? Connectivity tag? <span className="vinny-pill">Yo Mama</span> */}
          <button
            className="vinny-refresh"
                        onClick={() => { setHistory([]); localStorage.removeItem(STORAGE_KEY); localStorage.removeItem(DRAFT_KEY); }}
            title="Clear chat"
            aria-label="Clear chat"
          >
            ⟲
          </button>
          <button
            className="vinny-close"
            onClick={onClose}
            title="Minimize"
            aria-label="Minimize Vinny"
          >
            –
          </button>
        </div>
      </div>

      {/* messages */}
      <div ref={boxRef} className="vinny-body">
        {history.length === 0 && (
          <div className="vinny-empty">
            Ask about this page or the KB. Try:{" "}
            <em>“What are Late Fee Settings?”</em>
          </div>
        )}
        {history.map((m, i) => (
          <div
            key={i}
            className={m.role === "user" ? "vinny-row right" : "vinny-row left"}
          >
            <div
              className={`vinny-bubble ${m.role === "user" ? "user" : "assistant"}`}
            >
              {m.role === "assistant" ? formatMessage(m.content) : m.content}
            </div>
          </div>
        ))}
      </div>

      {/* composer , input / send */}
      <div className="vinny-composer">
        <input
          className="vinny-input"
          placeholder={busy ? "Thinking…" : "Ask Vinny…"}
          disabled={busy}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
        />
        <button className="vinny-send" onClick={ask} disabled={busy}>
          Send
        </button>
      </div>
    </div>
  );
}
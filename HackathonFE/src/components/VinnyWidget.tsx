// VinnyWidget = the chat panelUI
// Currently only mock, fake chats, when backend is ready swap fakeChat() for a real fetch() to `/api/query` 
import { useEffect, useRef, useState } from "react";

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

  const res = await fetch("http://localhost:5000/api/query", {
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


export default function VinnyWidget({
  onClose,
}: {
  // used when user clicks the close button '-' on modal
  onClose?: () => void;
}) {
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


  // Always scroll to latest message
  useEffect(() => {
    boxRef.current?.scrollTo({ top: 9e6, behavior: "smooth" });
  }, [history]);

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
    <div className="vinny-card" role="dialog"               aria-label="Vinny AI chat">
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
          <span className="vinny-pill">Local</span>
          <button
            className="vinny-close"
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
              {m.content}
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
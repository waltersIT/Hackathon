// VinnyLauncher = floating buttons that toggles VinnyWidget

import React, { useEffect, useState } from "react";
import VinnyWidget from "./VinnyWidget";
import vinny from "../assets/vinny.png";

export default function VinnyLauncher() {
  const [open, setOpen] = useState<boolean>(
    () => localStorage.getItem("vinny_open") === "1"
  );

  // open/closed so refresh doesn’t reset the state
  useEffect(() => {
    localStorage.setItem("vinny_open", open ? "1" : "0");
  }, [open]);

  return (
    <>
      {open && <VinnyWidget onClose={() => setOpen(false)} />}
      <button
        className="vinny-fab"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close Vinny" : "Open Vinny"}
        title={open ? "Close Vinny" : "Open Vinny"}
      >
        <img src={vinny} className="vinny-fab-img" alt="" aria-hidden />
      </button>
    </>
  );
}
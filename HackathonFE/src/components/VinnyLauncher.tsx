// VinnyLauncher = floating buttons that toggles VinnyWidget

import { useEffect, useState } from "react";
import VinnyWidget from "./VinnyWidget";
import vinny from "../assets/vinny.png";
import vinnyFinal from "../assets/vinnyFinal.gif";

export default function VinnyLauncher() {
  // const [open, setOpen] = useState<boolean>(
  //   () => localStorage.getItem("vinny_open") === "1"
  // );
    // mount state keeping widget in the DOM during the exit animation
  const [mounted, setMounted] = useState(false);
  // open state controls the enter animatio
  const [open, setOpen] = useState(false);
  // closing state toggles the exit animation
  const [closing, setClosing] = useState(false);
  // dancing gif on hover
  const [hovered, setHovered] = useState(false);


  // open/closed so refresh doesn’t reset the state
  useEffect(() => {
        const wasOpen = localStorage.getItem("vinny_open") === "1";
    if (wasOpen) {
      setMounted(true);
      // wait to see css initial state before opening
      requestAnimationFrame(() => setOpen(true));
    }
  }, []);

  // keep same when cahnge happens
  useEffect(() => {
    localStorage.setItem("vinny_open", open ? "1" : "0");
  }, [open]);

    function handleOpen() {
    setMounted(true);
    //next frame, start the open animation
    requestAnimationFrame(() => setOpen(true));
  }

  function handleClose() {
    setClosing(true);
    setOpen(false);
    // after exit animation, unmount
    
    setTimeout(() => {
      setClosing(false);
      setMounted(false);
    }, 220);
  }

  const toggle = () => {
    if (open) handleClose();
    else handleOpen();
  };


  return (
    <>
      {/* old code if needed {open && <VinnyWidget onClose={() => setOpen(false)} />} */}
        {mounted && (
        <VinnyWidget
          onClose={handleClose}
          stateClassName={open ? "vinny-enter" : closing ? "vinny-exit" : ""}
        />
      )}
      <button
        className="vinny-fab"
        // onClick={() => setOpen((o) => !o)}
        onClick={toggle}
        aria-label={open ? "Close Vinny" : "Open Vinny"}
        title={open ? "Close Vinny" : "Open Vinny"}
      >
                <img
          src={hovered ? vinnyFinal : vinny}
          className="vinny-fab-img"
          alt=""
          aria-hidden
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
        />
      </button>
    </>
  );
}
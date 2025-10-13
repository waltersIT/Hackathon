import React from 'react'
import VinnyLauncher from './components/VinnyLauncher'
import VinnyWidget from './components/VinnyWidget'

import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  return (
    <div className="App">
      <div style={{ padding: 24 }}>
        <h2>Vinny Frontend Preview</h2>
        <p>
          Support Team for the Win!
        </p>
      </div>

      {/*launcher modal */}
      <VinnyLauncher />
    </div>
  );
}

export default App

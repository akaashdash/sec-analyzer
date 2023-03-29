import './App.css';
import React, { useState } from "react";
import { getCompany10K } from './services/API';

function App() {

  const [ticker, setTicker] = useState("");
    const [year, setYear] = useState("");

    async function handleSearch(event) {
      event.preventDefault()
      const res = await getCompany10K(ticker, year)
    }

    const fetchVisual = () => {
        window.sessionStorage.setItem('hostChoice', null);
        window.sessionStorage.setItem('locChoice', null);
        window.sessionStorage.setItem('dateChoice', null);
    }
  return (
    <div className="App">
      <h1>Search for a company</h1>
            <form className="form" onSubmit={handleSearch}>
                <input className="textIn" type="text" id="username" value={ticker} onChange={(e) => setTicker(e.target.value)} required pattern="[A-Z]+" placeholder="Company Ticker"/>
                <br/>
                <input className="textIn" type="text" id="password" value={year} onChange={(e) => setYear(e.target.value)} required pattern="^[0-9]*$" placeholder="Document Year"/>
                <br/>
                <input onClick={fetchVisual} className="submit" type="submit" value="Go!" />
            </form>
    </div>
  );
}

export default App;

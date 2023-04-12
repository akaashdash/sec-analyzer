import './App.css';
import React, { useState } from "react";
import { getCompany10K } from './services/API';

function App() {

  const [ticker, setTicker] = useState("");
  const [year, setYear] = useState("");
  const [imageSrc, setImageSrc] = useState(null);

  async function handleSearch(event) {
    event.preventDefault()
    getCompany10K(ticker, year).then(res => {
      setImageSrc(URL.createObjectURL(res));
    });
  }

  return (
    <div className="App">
      <h1>Search for a company</h1>
      <form className="form" onSubmit={handleSearch}>
        <label htmlFor="ticker">Company Ticker</label>
        <input className="textIn" type="text" id="ticker" value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} required pattern="[A-Z]+" placeholder="e.g. AAPL"/>
        <label htmlFor="year">Document Year</label>
        <input className="textIn" type="text" id="year" value={year} onChange={(e) => setYear(e.target.value)} required pattern="^[0-9]*$" placeholder="e.g. 2021"/>
        <input className="submit" type="submit" value="Go!" />
      </form>
      { imageSrc && (
        <div className="wordcloud">
          <h2 className='wordcloudheader'>Word Cloud of {ticker} Annual Report {year}</h2>
          <img src={imageSrc} alt={`Word cloud of ${ticker} Annual Report ${year}`} />
        </div>
      )}
    </div>
  );
}

export default App;

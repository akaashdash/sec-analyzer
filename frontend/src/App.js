import './App.css';
import React, { useState } from "react";
import { getCompanyVisual } from './services/API';
import { MapInteractionCSS } from 'react-map-interaction';

function App() {

  const [ticker, setTicker] = useState("");
  const [year, setYear] = useState("");
  const [wordcloudSrc, setWordcloudSrc] = useState(null);
  const [knowledgegraphSrc, setKnowledgegraphSrc] = useState(null);

  async function handleSearch(event) {
    event.preventDefault()
    getCompanyVisual(ticker, year, "wordcloud").then(res => {
      setWordcloudSrc(URL.createObjectURL(res));
    });
    getCompanyVisual(ticker, year, "knowledgegraph").then(res => {
      setKnowledgegraphSrc(URL.createObjectURL(res));
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
      { knowledgegraphSrc && (
        <div className="visualContainer">
          <div className='wordcloudContainer'>
            <h2 className='wordcloudHeader'>Word Cloud of {ticker} Annual Report {year}</h2>
            <img src={wordcloudSrc} alt={`Word cloud of ${ticker} Annual Report ${year}`} />
          </div>
          <div className='knowledgegraphContainer'>
            <h2 className='knowledgegraphHeader'>Knowledge Graph of {ticker} Annual Report {year}</h2>
            <MapInteractionCSS>
              <img src={knowledgegraphSrc} alt={`Knowledge Graph of ${ticker} Annual Report ${year}`} />
            </MapInteractionCSS>
            
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

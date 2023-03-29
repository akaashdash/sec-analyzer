import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:80",
});

async function getCompany10K(ticker, year) {
    try {
        const res = await api.get("/company", {
            params: {
                ticker: ticker,
                year: year
            }
        })
        console.log(res.data.ticker);
        return res.data
    } catch (error) {
        return error
    }
}

export { getCompany10K }
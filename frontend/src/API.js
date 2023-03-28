import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:80",
});

async function getCompany10K(ticker, year) {
    try {
        const res = await api.get("/company")
        console.log(res);
    } catch (error) {
        return error
    }
}

export { getCompany10K }

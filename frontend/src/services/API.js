import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:80",
});

async function getCompanyVisual(ticker, year, visualType) {
    // visualType is either /wordcloud or /knowledgegraph
    const endpoint = "/company/" + visualType;
    try {
        const res = await api.get(endpoint, {
            params: {
                ticker: ticker,
                year: year
            },
            responseType: 'blob'
        })
    // console.log(typeof(res.data));
        return res.data
    } catch (error) {
        return error
    }
}



export { getCompanyVisual }
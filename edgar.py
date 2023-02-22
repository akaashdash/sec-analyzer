from sec_edgar_downloader import Downloader

dl = Downloader()
dl.get("10-K", "IBM", after="2018-02-01", before="2018-02-28", amount=1)
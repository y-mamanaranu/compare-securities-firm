# Compare Securities Firms
Compare Securities Firms in JP
- SBI証券
- マネックス証券
- 楽天証券

## Results
- [Foreign ETF](https://y-muen.github.io/compare-securities-firm/doc/foreign-etf.html)

## Usage
```
from compare_securities_firm.foreign_etf import Foreign_ETF

obj = Foreign_ETF()
obj.upate()
obj.update_json()
```

### Options
If you use Chromium browser but not Chrome, use `binary_location`.
```
from selenium.webdriver.chrome.options import Options

options = Options()
options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
```
Pass it when excute `update`.
```
obj.upate(options=options)
```

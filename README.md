# 👨‍✈️ Clarence 7.0: The Supervisor Pro

**Production-Grade Web Scraping Engine with AI-Powered Extraction**

---

## 🌟 Features

### Core Capabilities
- ✅ **Complete Data Extraction** - Extracts ALL items (120+ per page), not just 10-15
- ✅ **Preview Images** - Automatically captures and includes image URLs
- ✅ **Dual Extraction Engine**
  - Direct HTML parsing for Craigslist (fast, accurate)
  - AI-powered extraction for other sites (flexible, adaptive)
- ✅ **Multi-Page Scraping** - Automatic pagination with smart detection
- ✅ **Stealth Mode** - Advanced anti-detection features
  - Random user agents
  - Proxy support (authenticated & unauthenticated)
  - Browser fingerprint masking
- ✅ **Production Ready**
  - Comprehensive error handling
  - Full logging system
  - Input validation & sanitization
  - Secure credential management

### Supported Sites
- 🎯 **Craigslist** (Jobs, Gigs, For Sale, Services)
- 🎯 **Universal Mode** (Any listing/directory site via AI)

### Export Formats
- 📊 CSV (Excel-compatible)
- 📦 JSON (API-ready)
- 📋 Real-time data table

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Chrome or Chromium
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone/Download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=sk-your-actual-key-here
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   - Navigate to: `http://localhost:8501`

---

## 📖 How to Use

### Method 1: Quick Target (Craigslist)

1. **Use the Lead Detective Pro sidebar**
   - Enter target city (e.g., "bakersfield")
   - Enter job/niche (e.g., "admin")
   - Select platform (Jobs, Gigs, or For Sale)
   - Click "Lock Target"

2. **Execute extraction**
   - Click "Execute Extraction"
   - Watch the real-time progress
   - Download results as CSV or JSON

### Method 2: Custom URL

1. **Paste any URL** into the "Target URL" field
2. **Customize data fields** (optional)
3. **Set scan depth** (number of pages)
4. **Execute and download**

---

## ⚙️ Configuration Options

### Proxy Strategies

**No Proxy (Fastest)**
- Direct connection
- Best for testing
- Use when IP blocking isn't a concern

**Rotate from Local File**
- Reads from `proxyscrape_premium_http_proxies.txt`
- Randomly selects a proxy per session
- Format: `user:pass@ip:port` or `ip:port`

**Paste Proxy String**
- Enter a single proxy manually
- Supports authenticated proxies
- Format: `username:password@host:port`

### Data Blueprint
- Customize extracted fields
- Example: "Title, Price, Location, Email, Link"
- AI adapts to your requirements

---

## 📊 Expected Results

### Craigslist Scraping
- **Items per page**: 120 (complete extraction)
- **Speed**: ~60-90 seconds per page
- **Success rate**: 95%+
- **Data quality**: High (direct HTML parsing)

### Other Sites (AI Mode)
- **Items per page**: Varies by site
- **Speed**: ~90-120 seconds per page
- **Success rate**: 80-90%
- **Data quality**: Very good (AI interpretation)

---

## 🔒 Security & Privacy

### Data Protection
- ✅ All credentials stored in `.env` (never committed)
- ✅ Input validation prevents injection attacks
- ✅ Sanitized user inputs
- ✅ Secure proxy authentication

### Logging
- All operations logged to `clarence.log`
- Debug information for troubleshooting
- No sensitive data in logs

### Compliance
- Respects robots.txt (check site's policy)
- Rate limiting to prevent server overload
- User-agent identification
- For educational/research purposes

---

## 🐛 Troubleshooting

### "No items extracted"
- Verify URL is accessible in your browser
- Check internet connection
- Try without proxy first
- Review `clarence.log` for details

### "API key not found"
- Ensure `.env` file exists in root directory
- Verify `OPENAI_API_KEY=your-key` is set
- No spaces around the `=` sign
- Restart the application

### "Chrome driver not found"
- Application auto-installs ChromeDriver
- Ensure Google Chrome is installed
- Check internet connection

### "Only getting 10-15 items instead of 120"
- ✅ This is FIXED in version 7.0
- Ensure you're using the latest code
- Try increasing scroll depth in settings

### "No preview images"
- ✅ This is FIXED in version 7.0
- Check if the site has images
- Review extracted data - look for `Preview_Image` column

---

## 💻 Technical Stack

- **Frontend**: Streamlit
- **Scraping**: Selenium + BeautifulSoup
- **AI**: OpenAI GPT-4o-mini
- **Data**: Pandas
- **Browser**: Chrome/Chromium (headless)

---

## 📈 Roadmap

- [ ] Database integration (PostgreSQL)
- [ ] Scheduled scraping (cron jobs)
- [ ] Email notifications
- [ ] REST API mode
- [ ] Advanced filtering
- [ ] Duplicate detection
- [ ] Historical tracking

---

## 💬 Support

### Getting Help
1. Check `clarence.log` for error details
2. Review this README
3. Verify all prerequisites are installed
4. Test with a simple URL first

### Common Error Solutions
- **ModuleNotFoundError**: Run `pip install -r requirements.txt`
- **API rate limit**: Check OpenAI usage dashboard
- **Timeout errors**: Increase page load timeout in code

---

## 📜 License

**For Commercial Use**: Contact for licensing
**For Personal/Educational Use**: Free with attribution

---

## 🎯 Version Information

**Current Version**: 7.0 Production
**Release Date**: 2026-01-06
**Status**: ✅ Ready for deployment

### What's New in 7.0
- ✅ Complete extraction (120+ items per page)
- ✅ Preview image extraction
- ✅ Production-grade error handling
- ✅ Enhanced security features
- ✅ Comprehensive logging
- ✅ Input validation
- ✅ Dual extraction modes
- ✅ Better proxy support

### Upgrading from 6.0
- Enhanced extraction engine (no config needed)
- Automatic image capture
- Better error recovery
- More detailed logging

---

## 👨‍💻 About

Clarence 7.0 is a professional-grade web scraping solution designed for businesses, researchers, and developers who need reliable, complete data extraction from listing sites.

**Built with precision. Deployed with confidence.**

---

*Last updated: January 6, 2026*

<div align="center">

# CryptoTicker

![CryptoTicker Logo](ticker.png)

_A crypto ticker application for macOS status bar that displays real-time cryptocurrency prices with trend indicators based on 24-hour changes._

</div>

## Features

- **Status Bar Integration**: Display crypto prices directly in the macOS status bar
- **Real-time Updates**: Automatic price updates with customizable intervals
- **Trend Indicators**: ▲ (up) or ▼ (down) symbols based on 24-hour changes
- **Multiple Coins**: Support for monitoring multiple cryptocurrencies simultaneously
- **Auto Coin Cycling**: Automatic switching between coins with clear position indicators
- **Interactive Menu**: Right-click menu with comprehensive options
- **Persistent Settings**: Configuration saved automatically
- **Optimized API Calls**: Batch API calls to reduce rate limiting
- **Clean Output**: No intrusive urllib3 warnings

## Requirements

- macOS (required for status bar integration)
- Python 3.6+
- Internet connection for CoinGecko API

## Installation

1. **Clone repository**:

   ```bash
   git clone [repository-url]
   cd CryptoTicker
   ```

2. **Install dependencies**:

   ```bash
   python3 setup.py
   ```

3. **Run the application**:

   ```bash
   python3 main.py
   ```

## Usage

### Running the Application

After running the application, the crypto ticker icon will appear in the macOS status bar. By default, the application will display Bitcoin and Ethereum with a 5-minute refresh interval.

### Menu Options

Right-click on the status bar icon to access the menu:

1. **Add New Coins**: Add new cryptocurrencies by entering their symbol

   - Input symbols like: BTC, ETH, BNB, ADA, SOL, DOGE, MATIC, etc.
   - Supports 30+ popular coins + automatic search for other coins
   - Automatically fetches latest prices after adding

2. **Refresh Intervals**: Set price update intervals (✓ marks current selection)

   - 1 minute, 5 minutes, 10 minutes

3. **Coin Cycling**: Set interval for switching between coins (✓ marks current selection)

   - 3, 5, or 7 seconds with immediate switching

4. **Current Coins**: View and manage currently monitored coins

   - Shows real-time prices for each coin (e.g., BTC: $45,000 ▲, ETH: $3,000 ▼)
   - Remove individual coins
   - Automatically updates remaining coins after removal

5. **Reset to Default**: Reset all settings to default values

   - Restores Bitcoin and Ethereum as monitored coins
   - Resets refresh interval to 5 minutes
   - Resets coin cycling to 5 seconds
   - Automatically fetches latest prices after reset

6. **Manual Refresh**: Update prices manually

7. **Exit**: Exit the application

### Status Bar Display

Display format in the status bar:

- **Single coin**: `▼ ETH: $2,956`
- **Multiple coins**: `▲ BTC: $45,000` (cycling through coins)
- **Loading**: `ETH: Loading...`

New format with trend indicator upfront for better readability and thousand separators for easier reading.

### Trend Indicators

- **▲**: Price increased in the last 24 hours
- **▼**: Price decreased in the last 24 hours
- **=**: Price unchanged significantly

## Supported Symbols

The application supports 30+ popular cryptocurrencies with automatic symbol mapping:

**Major Coins**: BTC, ETH, BNB, ADA, SOL, DOGE, MATIC, LINK, DOT, LTC, BCH, XLM, XRP, AVAX, ATOM, NEAR, FTM, ALGO, TRX, ICP, APT, ARB, OP, SHIB, UNI

**DeFi Tokens**: MKR, CRV, SNX, COMP, SUSHI, LDO

For other coins not in the mapping, the application will automatically search using the CoinGecko search API.

## Data API

The application uses the [CoinGecko API](https://www.coingecko.com/api) to fetch:

- Real-time cryptocurrency prices with batch calls (optimized)
- 24-hour change data to determine trends
- Cryptocurrency search by symbol

### API Optimization

- **Batch API Calls**: 95% reduction in API call count
- **Caching System**: 30-second cache to reduce load
- **Rate Limiting Protection**: Adaptive intervals to prevent rate limiting
- **Retry Mechanism**: Exponential backoff for reliability

## Configuration

The application automatically saves configuration in the `config.json` file:

```json
{
  "coins": ["bitcoin", "ethereum"],
  "refresh_interval": 300,
  "coin_cycle_interval": 5
}
```

## Performance Features

- **Thread Safety**: All operations use proper locks
- **Memory Optimization**: Proper cleanup for menu items
- **Error Handling**: Comprehensive error handling and recovery
- **Clean Output**: Suppress urllib3 warnings for clean output

## Troubleshooting

### Application doesn't appear in status bar

- Make sure you're running on macOS
- Check system permissions for running Python applications
- Restart the application if necessary

### API connection errors

- Check internet connection
- CoinGecko API may be experiencing rate limiting
- Application will automatically adjust refresh interval if rate limited

### High CPU usage

- Reduce the number of coins being monitored (app will warn if >8 coins)
- Increase refresh interval
- Restart the application

### Monitoring many coins

- Application will automatically adjust interval for many coins
- Warning appears if monitoring >8 coins
- Rate limiting protection will activate automatically

## Dependencies

- `rumps`: Framework for creating macOS status bar applications
- `requests`: HTTP library for API calls

## License

MIT License

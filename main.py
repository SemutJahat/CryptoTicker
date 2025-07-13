

import os
import sys
import warnings
from io import StringIO

# Suppress semua urllib3 warnings dengan multiple methods
warnings.filterwarnings('ignore', category=UserWarning, module='urllib3')
warnings.filterwarnings('ignore', message='.*urllib3.*')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Temporarily redirect stderr untuk capture urllib3 warnings
class WarningFilter:
    def __init__(self, target):
        self.target = target
        
    def write(self, message):
        if 'urllib3' not in message and 'NotOpenSSLWarning' not in message and 'warnings.warn' not in message:
            self.target.write(message)
            
    def flush(self):
        self.target.flush()

# Apply stderr filter
original_stderr = sys.stderr
sys.stderr = WarningFilter(original_stderr)

import rumps
import requests
import threading
import time
import json
from datetime import datetime, timedelta

# Restore stderr after imports
sys.stderr = original_stderr

class CryptoTicker(rumps.App):
    def __init__(self):
        super(CryptoTicker, self).__init__("Loading...")
        self.icon = None
        self.quit_button = "Exit"
        
        # Data storage
        self.coins = ["bitcoin", "ethereum"]  # Default coins
        self.refresh_interval = 90  # Increased default to 90 seconds for rate limiting
        self.price_data = {}
        self.config_file = "config.json"
        self.monitoring_active = True
        
        # Lock untuk proteksi akses bersamaan ke coins & price_data
        self.data_lock = threading.Lock()
        # Lock terpisah untuk coins dan coin index untuk mencegah race condition
        self.coins_lock = threading.Lock()
        
        # Coin cycling untuk status bar
        self.current_coin_index = 0
        self.coin_cycle_interval = 4  # 4 detik per coin
        
        # Retry settings untuk API calls
        self.max_retries = 3
        self.retry_delay = 3  # Increased delay
        
        # Rate limiting protection
        self.last_api_call = 0
        self.min_api_interval = 2.0  # Minimum 2 detik antar API calls
        self.api_call_count = 0
        self.api_call_window_start = time.time()
        self.max_calls_per_minute = 25  # Conservative limit
        
        # Caching untuk mengurangi API calls
        self.price_cache = {}
        self.cache_ttl = 30  # Cache valid untuk 30 detik
        
        # Adaptive rate limiting
        self.consecutive_rate_limits = 0
        self.base_refresh_interval = 90
        
        # Symbol to CoinGecko ID mapping untuk coins populer
        self.symbol_to_id = {
            "btc": "bitcoin",
            "eth": "ethereum", 
            "bnb": "binancecoin",
            "ada": "cardano",
            "sol": "solana",
            "doge": "dogecoin",
            "matic": "matic-network",
            "polygon": "matic-network",
            "link": "chainlink",
            "dot": "polkadot",
            "ltc": "litecoin",
            "bch": "bitcoin-cash",
            "xlm": "stellar",
            "xrp": "ripple",
            "avax": "avalanche-2",
            "atom": "cosmos",
            "near": "near",
            "ftm": "fantom",
            "algo": "algorand",
            "tron": "tron",
            "trx": "tron",
            "icp": "internet-computer",
            "apt": "aptos",
            "arb": "arbitrum",
            "op": "optimism",
            "ldo": "lido-dao",
            "shib": "shiba-inu",
            "uni": "uniswap",
            "mkr": "maker",
            "crv": "curve-dao-token",
            "snx": "synthetix-network-token",
            "comp": "compound-governance-token",
            "sushi": "sushi"
        }
        
        # Load configuration
        self.load_config()
        
        # Setup menu
        self.setup_menu()
        
        # Start price monitoring
        self.start_price_monitoring()
    
    def setup_menu(self):
        """Setup aplikasi menu"""
        # Add coins menu with custom input
        add_coins_menu = rumps.MenuItem("Add New Coins", callback=self.add_coin_dialog)
        
        # Refresh intervals submenu - updated dengan nilai lebih tinggi
        refresh_menu = rumps.MenuItem("Refresh Intervals")
        refresh_menu.add(rumps.MenuItem("1 minute", callback=lambda _: self.set_refresh_interval(60)))
        refresh_menu.add(rumps.MenuItem("90 seconds", callback=lambda _: self.set_refresh_interval(90)))
        refresh_menu.add(rumps.MenuItem("2 minutes", callback=lambda _: self.set_refresh_interval(120)))
        refresh_menu.add(rumps.MenuItem("3 minutes", callback=lambda _: self.set_refresh_interval(180)))
        refresh_menu.add(rumps.MenuItem("5 minutes", callback=lambda _: self.set_refresh_interval(300)))
        
        # Coin cycling intervals submenu
        cycling_menu = rumps.MenuItem("Coin Cycling")
        cycling_menu.add(rumps.MenuItem("2 seconds", callback=lambda _: self.set_cycle_interval(2)))
        cycling_menu.add(rumps.MenuItem("3 seconds", callback=lambda _: self.set_cycle_interval(3)))
        cycling_menu.add(rumps.MenuItem("4 seconds", callback=lambda _: self.set_cycle_interval(4)))
        cycling_menu.add(rumps.MenuItem("5 seconds", callback=lambda _: self.set_cycle_interval(5)))
        cycling_menu.add(rumps.MenuItem("6 seconds", callback=lambda _: self.set_cycle_interval(6)))
        cycling_menu.add(rumps.MenuItem("10 seconds", callback=lambda _: self.set_cycle_interval(10)))
        
        # Current coins submenu
        self.coins_menu = rumps.MenuItem("Current Coins")
        
        # Main menu
        self.menu = [
            add_coins_menu,
            refresh_menu,
            cycling_menu,
            self.coins_menu,
            rumps.separator,
            rumps.MenuItem("Remove All Coins", callback=self.remove_all_coins),
            rumps.MenuItem("Manual Refresh", callback=self.manual_refresh),
            rumps.MenuItem("Next Coin", callback=self.manual_next_coin),
            rumps.separator,
        ]
        
        self.update_coins_menu()
    
    def load_config(self):
        """Load konfigurasi dari file dengan proper error handling"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                    # Validate config structure
                    if isinstance(config, dict):
                        # Validate coins list
                        coins = config.get('coins', ["bitcoin", "ethereum"])
                        if isinstance(coins, list) and all(isinstance(coin, str) for coin in coins):
                            self.coins = coins
                        else:
                            print("Invalid coins format in config, using defaults")
                            self.coins = ["bitcoin", "ethereum"]
                        
                        # Validate refresh interval - dengan minimum 60 detik
                        refresh_interval = config.get('refresh_interval', 90)
                        if isinstance(refresh_interval, int) and refresh_interval >= 60:
                            self.refresh_interval = refresh_interval
                            self.base_refresh_interval = refresh_interval
                        else:
                            print("Invalid refresh interval in config, using default (90s)")
                            self.refresh_interval = 90
                            self.base_refresh_interval = 90
                        
                        # Validate coin cycle interval
                        cycle_interval = config.get('coin_cycle_interval', 4)
                        if isinstance(cycle_interval, int) and cycle_interval > 0:
                            self.coin_cycle_interval = cycle_interval
                        else:
                            print("Invalid cycle interval in config, using default (4s)")
                            self.coin_cycle_interval = 4
                    else:
                        print("Invalid config format, using defaults")
                        self.reset_to_defaults()
            else:
                print("Config file not found, using defaults")
                self.reset_to_defaults()
                
        except json.JSONDecodeError as e:
            print(f"Config file corrupted: {e}, using defaults")
            self.reset_to_defaults()
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """Reset ke konfigurasi default"""
        self.coins = ["bitcoin", "ethereum"]
        self.refresh_interval = 90
        self.base_refresh_interval = 90
        self.coin_cycle_interval = 4
    
    def save_config(self):
        """Simpan konfigurasi ke file dengan proper error handling"""
        try:
            # Create backup of current config if it exists
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                try:
                    with open(self.config_file, 'r') as src, open(backup_file, 'w') as dst:
                        dst.write(src.read())
                except Exception as e:
                    print(f"Warning: Could not create config backup: {e}")
            
            # Save new config
            config = {
                'coins': self.coins,
                'refresh_interval': self.refresh_interval,
                'coin_cycle_interval': self.coin_cycle_interval
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"Error saving config: {e}")
            # Try to restore from backup
            backup_file = f"{self.config_file}.backup"
            if os.path.exists(backup_file):
                try:
                    with open(backup_file, 'r') as src, open(self.config_file, 'w') as dst:
                        dst.write(src.read())
                    print("Config restored from backup")
                except Exception as restore_error:
                    print(f"Error restoring config: {restore_error}")
    
    def check_rate_limit(self):
        """Check apakah kita dalam rate limit dan tunggu jika perlu"""
        current_time = time.time()
        
        # Reset counter jika sudah lebih dari 1 menit
        if current_time - self.api_call_window_start > 60:
            self.api_call_count = 0
            self.api_call_window_start = current_time
        
        # Tunggu jika terlalu banyak calls dalam 1 menit
        if self.api_call_count >= self.max_calls_per_minute:
            sleep_time = 60 - (current_time - self.api_call_window_start)
            if sleep_time > 0:
                print(f"Rate limit protection: sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.api_call_count = 0
                self.api_call_window_start = time.time()
        
        # Tunggu interval minimum antar API calls
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.min_api_interval:
            sleep_time = self.min_api_interval - time_since_last_call
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
        self.api_call_count += 1
    
    def make_api_request(self, url, timeout=20):
        """Make API request with enhanced rate limiting and retry mechanism"""
        self.check_rate_limit()
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    # Reset consecutive rate limits on success
                    self.consecutive_rate_limits = 0
                    return response
                elif response.status_code == 429:  # Rate limit
                    self.consecutive_rate_limits += 1
                    backoff_time = self.retry_delay * (2 ** self.consecutive_rate_limits)
                    print(f"Rate limited (attempt {attempt + 1}), waiting {backoff_time}s...")
                    time.sleep(backoff_time)
                    
                    # Adaptive rate limiting - increase refresh interval
                    if self.consecutive_rate_limits >= 2:
                        self.adaptive_rate_limit_adjustment()
                        
                else:
                    print(f"API returned status {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"Request timeout on attempt {attempt + 1}")
            except requests.exceptions.ConnectionError:
                print(f"Connection error on attempt {attempt + 1}")
            except requests.exceptions.RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def adaptive_rate_limit_adjustment(self):
        """Adjust refresh interval berdasarkan rate limiting"""
        old_interval = self.refresh_interval
        # Increase interval by 50% with minimum 2 minutes
        self.refresh_interval = max(120, int(self.refresh_interval * 1.5))
        
        if self.refresh_interval != old_interval:
            print(f"Adaptive rate limiting: refresh interval increased to {self.refresh_interval}s")
            rumps.notification(
                title="CryptoTicker",
                subtitle="Rate Limit Protection",
                message=f"Refresh interval increased to {self.refresh_interval}s to prevent rate limiting"
            )
    
    def get_cached_price(self, coin_id):
        """Get price dari cache jika masih valid"""
        if coin_id in self.price_cache:
            cache_entry = self.price_cache[coin_id]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                return cache_entry['data']
        return None
    
    def set_cached_price(self, coin_id, data):
        """Set price ke cache"""
        self.price_cache[coin_id] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def get_multiple_coin_prices(self, coin_ids):
        """Batch API call untuk multiple coins - OPTIMASI UTAMA"""
        if not coin_ids:
            return {}
        
        # Check cache first
        cached_data = {}
        uncached_coins = []
        
        for coin_id in coin_ids:
            cached = self.get_cached_price(coin_id)
            if cached:
                cached_data[coin_id] = cached
            else:
                uncached_coins.append(coin_id)
        
        if not uncached_coins:
            return cached_data
        
        try:
            # OPTIMASI: Single API call untuk multiple coins
            coins_param = ','.join(uncached_coins)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins_param}&vs_currencies=usd&include_24hr_change=true"
            
            response = self.make_api_request(url)
            if not response:
                return cached_data
            
            price_data = response.json()
            
            # Validate response structure
            if not isinstance(price_data, dict):
                print("Invalid batch price response structure")
                return cached_data
            
            # Process setiap coin
            for coin_id in uncached_coins:
                if coin_id in price_data:
                    coin_data = price_data[coin_id]
                    if isinstance(coin_data, dict) and 'usd' in coin_data:
                        current_price = coin_data['usd']
                        change_24h = coin_data.get('usd_24h_change', 0)
                        
                        # Validate price
                        if isinstance(current_price, (int, float)) and current_price > 0:
                            # Gunakan 24h change sebagai trend indicator
                            trend = "up" if change_24h > 0 else "down" if change_24h < 0 else "neutral"
                            
                            coin_info = {
                                'current_price': current_price,
                                'open_price': current_price - (current_price * change_24h / 100),
                                'trend': trend,
                                'change_percent': change_24h
                            }
                            
                            # Cache the result
                            self.set_cached_price(coin_id, coin_info)
                            cached_data[coin_id] = coin_info
                        else:
                            print(f"Invalid price for {coin_id}: {current_price}")
                else:
                    print(f"No data for {coin_id} in batch response")
                    
        except Exception as e:
            print(f"Error in batch price fetch: {e}")
        
        return cached_data
    
    def get_coin_price(self, coin_id):
        """Fallback method untuk single coin - tetap ada untuk compatibility"""
        batch_data = self.get_multiple_coin_prices([coin_id])
        return batch_data.get(coin_id)
    
    def update_prices(self):
        """Update harga semua coins dengan batch API calls - OPTIMASI UTAMA"""
        with self.coins_lock:
            coins_snapshot = self.coins.copy()
        
        if not coins_snapshot:
            self.title = "No Coins"
            return
            
        try:
            # OPTIMASI: Single batch call untuk semua coins
            print(f"Fetching prices for {len(coins_snapshot)} coins in batch...")
            new_price_data = self.get_multiple_coin_prices(coins_snapshot)
            
            failed_coins = []
            for coin in coins_snapshot:
                if coin not in new_price_data:
                    failed_coins.append(coin)
            
            # Update price data dengan lock
            with self.data_lock:
                self.price_data = new_price_data
            
            # Log statistics
            success_count = len(new_price_data)
            total_count = len(coins_snapshot)
            print(f"Price update: {success_count}/{total_count} coins successful")
            
            if failed_coins:
                print(f"Failed to get prices for: {failed_coins}")
            
            self.update_status_bar()
            
        except Exception as e:
            print(f"Error updating prices: {e}")
            self.title = "Error"
    
    def update_status_bar(self):
        """Update status bar dengan harga - thread safe"""
        # Get snapshots of data dengan locks
        with self.data_lock:
            price_data_snapshot = self.price_data.copy()
        
        with self.coins_lock:
            coins_snapshot = self.coins.copy()
            current_index = self.current_coin_index
        
        if not price_data_snapshot:
            self.title = "Loading..."
            return
        
        # Jika hanya ada 1 coin, tampilkan langsung
        if len(coins_snapshot) == 1:
            coin_id = coins_snapshot[0]
            if coin_id in price_data_snapshot:
                data = price_data_snapshot[coin_id]
                coin_symbol = self.get_symbol_from_coin_id(coin_id)
                trend_symbol = "▲" if data['trend'] == "up" else "▼" if data['trend'] == "down" else "="
                
                # Format price berdasarkan nilai
                if data['current_price'] < 0.01:
                    price_str = f"${data['current_price']:.6f}"
                elif data['current_price'] < 1:
                    price_str = f"${data['current_price']:.4f}"
                elif data['current_price'] < 100:
                    price_str = f"${data['current_price']:.2f}"
                else:
                    price_str = f"${data['current_price']:.0f}"
                
                # Tampilkan persentase change jika significant
                if abs(data['change_percent']) >= 0.1:
                    change_str = f" ({data['change_percent']:+.1f}%)"
                else:
                    change_str = ""
                
                self.title = f"{coin_symbol}: {price_str} {trend_symbol}{change_str}"
            else:
                coin_symbol = self.get_symbol_from_coin_id(coins_snapshot[0])
                self.title = f"{coin_symbol}: Loading..."
            return
        
        # Untuk multiple coins, gunakan cycling dengan current index
        if len(coins_snapshot) > 1:
            # Pastikan index tidak melebihi jumlah coins (double check)
            if current_index >= len(coins_snapshot):
                # Update index dengan lock
                with self.coins_lock:
                    self.current_coin_index = 0
                    current_index = 0
            
            current_coin = coins_snapshot[current_index]
            
            # Cek apakah data coin tersedia
            if current_coin not in price_data_snapshot:
                coin_symbol = self.get_symbol_from_coin_id(current_coin)
                self.title = f"{coin_symbol}: Loading..."
                return
            
            data = price_data_snapshot[current_coin]
            coin_symbol = self.get_symbol_from_coin_id(current_coin)
            trend_symbol = "▲" if data['trend'] == "up" else "▼" if data['trend'] == "down" else "="
            
            # Format price berdasarkan nilai
            if data['current_price'] < 0.01:
                price_str = f"${data['current_price']:.6f}"
            elif data['current_price'] < 1:
                price_str = f"${data['current_price']:.4f}"
            elif data['current_price'] < 100:
                price_str = f"${data['current_price']:.2f}"
            else:
                price_str = f"${data['current_price']:.0f}"
            
            # Tampilkan dengan indikator posisi di depan - format baru: (1/4) ETH: $1234 ▲
            current_position = current_index + 1
            total_coins = len(coins_snapshot)
            self.title = f"{trend_symbol} {coin_symbol}: {price_str}"
    
    def start_price_monitoring(self):
        """Mulai monitoring harga di background dengan adaptive interval"""
        def monitor():
            while self.monitoring_active:
                try:
                    self.update_prices()
                    
                    # Adaptive refresh interval berdasarkan jumlah coins
                    current_interval = self.refresh_interval
                    with self.coins_lock:
                        coin_count = len(self.coins)
                    
                    # Increase interval jika banyak coins
                    if coin_count > 10:
                        current_interval = int(current_interval * 1.5)
                    elif coin_count > 5:
                        current_interval = int(current_interval * 1.2)
                    
                    print(f"Next refresh in {current_interval}s (monitoring {coin_count} coins)")
                    
                    # Sleep with small intervals to allow for responsive changes
                    elapsed = 0
                    while elapsed < current_interval and self.monitoring_active:
                        time.sleep(1)
                        elapsed += 1
                        
                except Exception as e:
                    print(f"Error in monitoring thread: {e}")
                    time.sleep(30)  # Wait 30 seconds before retrying on error
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
        # Initial price update dengan delay
        threading.Timer(3.0, self.update_prices).start()
        
        # Start coin cycling untuk multiple coins
        self.start_coin_cycling()
    
    def set_refresh_interval(self, interval):
        """Set refresh interval dengan minimum 60 detik"""
        if interval < 60:
            interval = 60
            rumps.notification(
                title="CryptoTicker",
                subtitle="Minimum Interval",
                message="Minimum refresh interval is 60 seconds to prevent rate limiting"
            )
        
        self.refresh_interval = interval
        self.base_refresh_interval = interval
        self.consecutive_rate_limits = 0  # Reset rate limit counter
        self.save_config()
        
        rumps.notification(
            title="CryptoTicker",
            subtitle="Refresh Interval Updated",
            message=f"Refresh interval set to {interval} seconds"
        )
    
    def manual_refresh(self, _):
        """Manual refresh dengan rate limiting protection"""
        current_time = time.time()
        if current_time - self.last_api_call < 10:  # Minimum 10 detik untuk manual refresh
            remaining = 10 - (current_time - self.last_api_call)
            rumps.notification(
                title="CryptoTicker",
                subtitle="Rate Limit Protection",
                message=f"Please wait {remaining:.0f} seconds before manual refresh"
            )
            return
        
        self.update_prices()
        rumps.notification(
            title="CryptoTicker",
            subtitle="Manual Refresh",
            message="Prices updated manually"
        )
    
    def manual_next_coin(self, _):
        """Manual pindah ke coin berikutnya"""
        with self.coins_lock:
            coins_count = len(self.coins)
        
        if coins_count > 1:
            self.cycle_to_next_coin()
            rumps.notification(
                title="CryptoTicker",
                subtitle="Switched Coin",
                message="Moved to next coin manually"
            )
        else:
            rumps.notification(
                title="CryptoTicker",
                subtitle="Cannot Switch",
                message="Need multiple coins to switch"
            )
    
    def add_coin_dialog(self, _):
        """Dialog untuk input coin symbol"""
        try:
            # Gunakan rumps.Window untuk input dialog
            response = rumps.Window(
                message="Masukkan symbol cryptocurrency (contoh: BTC, ETH, BNB):",
                title="Add New Coin",
                default_text="BTC",
                ok="Add",
                cancel="Cancel",
                dimensions=(250, 20)
            ).run()
            
            if response.clicked:
                symbol = response.text.strip()
                if symbol:
                    self.add_coin_by_symbol(symbol)
                    
        except Exception as e:
            print(f"Error in add_coin_dialog: {e}")
            rumps.notification(
                title="CryptoTicker",
                subtitle="Input Error",
                message="Tidak bisa membuka dialog input. Coba restart aplikasi."
            )
    
    def add_coin_by_symbol(self, symbol):
        """Tambah coin berdasarkan symbol"""
        coin_id = self.get_coin_id_from_symbol(symbol)
        
        if coin_id:
            self.add_coin(coin_id, symbol.upper())
        else:
            rumps.notification(
                title="CryptoTicker",
                subtitle="Coin Not Found",
                message=f"Symbol '{symbol.upper()}' tidak ditemukan. Coba symbol lain."
            )
    
    def add_coin(self, coin_id, symbol=None):
        """Tambah coin baru dengan thread safety"""
        with self.coins_lock:
            if coin_id not in self.coins:
                self.coins.append(coin_id)
                # Reset index jika ini coin pertama
                if len(self.coins) == 1:
                    self.current_coin_index = 0
                
                should_save = True
                display_name = symbol if symbol else coin_id.replace('-', ' ').title()
                message = f"{display_name} has been added to your watchlist"
                
                # Warning jika sudah banyak coins
                if len(self.coins) > 8:
                    rumps.notification(
                        title="CryptoTicker",
                        subtitle="Performance Warning",
                        message=f"Monitoring {len(self.coins)} coins. Consider longer refresh intervals."
                    )
            else:
                should_save = False
                display_name = symbol if symbol else coin_id.replace('-', ' ').title()
                message = f"{display_name} is already in your watchlist"
        
        if should_save:
            self.save_config()
            self.update_coins_menu()
            rumps.notification(
                title="CryptoTicker",
                subtitle="Coin Added",
                message=message
            )
        else:
            rumps.notification(
                title="CryptoTicker",
                subtitle="Coin Already Added",
                message=message
            )
    
    def remove_coin(self, coin_id):
        """Hapus coin dari watchlist dengan thread safety"""
        with self.coins_lock:
            if coin_id in self.coins:
                coin_symbol = self.get_symbol_from_coin_id(coin_id)
                self.coins.remove(coin_id)
                
                # Adjust current_coin_index jika diperlukan
                if self.current_coin_index >= len(self.coins) and len(self.coins) > 0:
                    self.current_coin_index = 0
                elif len(self.coins) == 0:
                    self.current_coin_index = 0
                
                should_save = True
                message = f"{coin_symbol} has been removed from your watchlist"
            else:
                should_save = False
                coin_symbol = self.get_symbol_from_coin_id(coin_id)
                message = f"{coin_symbol} is not in your watchlist"
        
        if should_save:
            # Remove from price data and cache
            with self.data_lock:
                if coin_id in self.price_data:
                    del self.price_data[coin_id]
            
            if coin_id in self.price_cache:
                del self.price_cache[coin_id]
            
            self.save_config()
            self.update_coins_menu()
            rumps.notification(
                title="CryptoTicker",
                subtitle="Coin Removed",
                message=message
            )
    
    def remove_all_coins(self, _):
        """Hapus semua coins dengan thread safety"""
        with self.coins_lock:
            self.coins = []
            self.current_coin_index = 0
        
        with self.data_lock:
            self.price_data = {}
        
        # Clear cache
        self.price_cache = {}
        
        self.save_config()
        self.update_coins_menu()
        self.title = "No Coins"
        rumps.notification(
            title="CryptoTicker",
            subtitle="All Coins Removed",
            message="All coins have been removed from your watchlist"
        )
    
    def update_coins_menu(self):
        """Update menu coins saat ini dengan proper cleanup"""
        # Remove all existing items dengan proper error handling
        try:
            if hasattr(self.coins_menu, '_menu') and self.coins_menu._menu is not None:
                self.coins_menu._menu.removeAllItems()
        except AttributeError as e:
            print(f"Warning: Could not access menu items: {e}")
        except Exception as e:
            print(f"Error removing menu items: {e}")
        
        with self.coins_lock:
            coins_snapshot = self.coins.copy()
        
        if not coins_snapshot:
            try:
                self.coins_menu.add(rumps.MenuItem("No coins added"))
            except Exception as e:
                print(f"Error adding no coins menu item: {e}")
        else:
            for coin in coins_snapshot:
                try:
                    # Gunakan symbol untuk display yang lebih user-friendly
                    coin_symbol = self.get_symbol_from_coin_id(coin)
                    coin_display = f"{coin_symbol} ({coin.replace('-', ' ').title()})"
                    
                    coin_menu = rumps.MenuItem(coin_display)
                    coin_menu.add(rumps.MenuItem(f"Remove {coin_symbol}", 
                                               callback=lambda sender, c=coin: self.remove_coin(c)))
                    self.coins_menu.add(coin_menu)
                except Exception as e:
                    print(f"Error adding coin menu item for {coin}: {e}")
    
    def get_coin_id_from_symbol(self, symbol):
        """Convert symbol ke CoinGecko ID dengan improved error handling"""
        symbol = symbol.lower().strip()
        
        # Check mapping lokal first
        if symbol in self.symbol_to_id:
            return self.symbol_to_id[symbol]
        
        # Jika tidak ada di mapping, coba search di CoinGecko
        try:
            search_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
            response = self.make_api_request(search_url)
            
            if response:
                search_data = response.json()
                coins = search_data.get('coins', [])
                
                # Validate response structure
                if not isinstance(coins, list):
                    print("Invalid API response structure")
                    return None
                
                # Cari exact match dengan symbol
                for coin in coins:
                    if isinstance(coin, dict) and coin.get('symbol', '').lower() == symbol:
                        return coin.get('id')
                
                # Jika tidak ada exact match, ambil yang pertama jika ada
                if coins and isinstance(coins[0], dict):
                    return coins[0].get('id')
            
        except Exception as e:
            print(f"Error searching coin: {e}")
        
        return None
    
    def get_symbol_from_coin_id(self, coin_id):
        """Convert coin ID ke symbol untuk display"""
        # Reverse lookup dari mapping
        for symbol, id_value in self.symbol_to_id.items():
            if id_value == coin_id:
                return symbol.upper()
        
        # Jika tidak ada di mapping, gunakan coin ID yang diformat
        if coin_id == "bitcoin":
            return "BTC"
        elif coin_id == "ethereum":
            return "ETH"
        elif coin_id == "binancecoin":
            return "BNB"
        else:
            # Fallback: ambil bagian pertama dari coin ID
            return coin_id.split('-')[0].upper()[:4]
    
    def start_coin_cycling(self):
        """Mulai cycling antar coins jika ada multiple coins"""
        def cycle_loop():
            while self.monitoring_active:
                try:
                    with self.coins_lock:
                        coin_count = len(self.coins)
                    
                    if coin_count > 1:
                        for _ in range(self.coin_cycle_interval * 10):
                            if not self.monitoring_active:
                                return
                            time.sleep(0.1)
                        self.cycle_to_next_coin()
                    else:
                        time.sleep(2)
                except Exception as e:
                    print(f"Error in coin cycling: {e}")
                    time.sleep(2)
        
        thread = threading.Thread(target=cycle_loop, daemon=True)
        thread.start()
    
    def cycle_to_next_coin(self):
        """Pindah ke coin berikutnya tanpa animation dengan thread safety"""
        with self.coins_lock:
            if len(self.coins) <= 1:
                return
            
            # Pindah sederhana ke coin berikutnya (looping)
            self.current_coin_index = (self.current_coin_index + 1) % len(self.coins)
        
        self.update_status_bar()
    
    def set_cycle_interval(self, interval):
        """Set coin cycling interval"""
        self.coin_cycle_interval = interval
        self.save_config()
        rumps.notification(
            title="CryptoTicker",
            subtitle="Coin Cycling Updated",
            message=f"Coin switching interval set to {interval} seconds"
        )

def main():
    print("🚀 Starting CryptoTicker...")
    print("📱 App akan muncul di status bar macOS")
    print("⚠️  Tekan Ctrl+C untuk menghentikan")
    print("=" * 50)
    app = CryptoTicker()
    app.run()

if __name__ == "__main__":
    main() 
<div align="center">

# CryptoTicker

![CryptoTicker Logo](ticker.png)

_Aplikasi crypto ticker untuk macOS status bar yang menampilkan harga cryptocurrency real-time dengan indikator trend berdasarkan perubahan 24 jam._

</div>

## Fitur

- **Status Bar Integration**: Menampilkan harga crypto langsung di status bar macOS
- **Real-time Updates**: Update harga otomatis dengan interval yang dapat disesuaikan
- **Trend Indicators**: Simbol ▲ (naik) atau ▼ (turun) berdasarkan perubahan 24 jam
- **Multiple Coins**: Dukung multiple cryptocurrency secara bersamaan
- **Auto Coin Cycling**: Pergantian otomatis antar coins dengan format posisi yang jelas
- **Interactive Menu**: Menu klik kanan dengan opsi lengkap
- **Persistent Settings**: Konfigurasi tersimpan otomatis
- **Optimized API Calls**: Batch API calls untuk mengurangi rate limiting
- **Clean Output**: Tidak ada warning urllib3 yang mengganggu

## Persyaratan

- macOS (diperlukan untuk status bar integration)
- Python 3.6+
- Internet connection untuk API CoinGecko

## Instalasi

1. **Clone repository**:

   ```bash
   git clone [repository-url]
   cd CryptoTicker
   ```

2. **Install dependencies**:

   ```bash
   python3 setup.py
   ```

3. **Jalankan aplikasi**:

   ```bash
   python3 main.py
   ```

## Penggunaan

### Menjalankan Aplikasi

Setelah menjalankan aplikasi, ikon crypto ticker akan muncul di status bar macOS. Secara default, aplikasi akan menampilkan Bitcoin dan Ethereum dengan interval refresh 90 detik.

### Menu Options

Klik kanan pada ikon di status bar untuk mengakses menu:

1. **Add New Coins**: Tambah cryptocurrency baru dengan memasukkan symbol

   - Input symbol seperti: BTC, ETH, BNB, ADA, SOL, DOGE, MATIC, dll.
   - Mendukung 30+ coins populer + pencarian otomatis untuk coins lain

2. **Refresh Intervals**: Atur interval update harga

   - 1 menit, 90 detik, 2 menit, 3 menit, 5 menit

3. **Coin Cycling**: Atur interval pergantian antar coins (jika ada multiple coins)

   - 2, 3, 4, 5, 6, atau 10 detik dengan pergantian langsung

4. **Current Coins**: Lihat dan kelola coins yang sedang dipantau

   - Remove individual coins

5. **Remove All Coins**: Hapus semua coins dari watchlist

6. **Manual Refresh**: Update harga secara manual

7. **Next Coin**: Pindah manual ke coin berikutnya (untuk multiple coins)

8. **Exit**: Keluar dari aplikasi

### Status Bar Display

Format tampilan di status bar:

- **Single coin**: `▼ ETH: $2956`
- **Multiple coins**: `▲ BTC: $45000 (1/3)` (dengan indikator posisi)
- **Loading**: `ETH: Loading...`

Format baru dengan indikator trend di depan untuk readability yang lebih baik.

### Indikator Trend

- **▲**: Harga naik dalam 24 jam terakhir
- **▼**: Harga turun dalam 24 jam terakhir
- **=**: Harga tidak berubah signifikan

## Supported Symbols

Aplikasi mendukung 30+ cryptocurrency populer dengan symbol mapping otomatis:

**Major Coins**: BTC, ETH, BNB, ADA, SOL, DOGE, MATIC, LINK, DOT, LTC, BCH, XLM, XRP, AVAX, ATOM, NEAR, FTM, ALGO, TRX, ICP, APT, ARB, OP, SHIB, UNI

**DeFi Tokens**: MKR, CRV, SNX, COMP, SUSHI, LDO

Untuk coins lain yang tidak ada dalam mapping, aplikasi akan mencari otomatis menggunakan CoinGecko search API.

## Data API

Aplikasi menggunakan [CoinGecko API](https://www.coingecko.com/api) untuk mendapatkan:

- Harga real-time cryptocurrency dengan batch calls (optimized)
- Data perubahan 24 jam untuk menentukan trend
- Pencarian cryptocurrency berdasarkan symbol

### API Optimization

- **Batch API Calls**: 95% reduction dalam jumlah API calls
- **Caching System**: 30 detik cache untuk mengurangi load
- **Rate Limiting Protection**: Adaptive intervals untuk mencegah rate limiting
- **Retry Mechanism**: Exponential backoff untuk reliability

## Konfigurasi

Aplikasi secara otomatis menyimpan konfigurasi dalam file `config.json`:

```json
{
  "coins": ["bitcoin", "ethereum"],
  "refresh_interval": 90,
  "coin_cycle_interval": 4
}
```

## Performance Features

- **Thread Safety**: Semua operations menggunakan proper locks
- **Memory Optimization**: Proper cleanup untuk menu items
- **Error Handling**: Comprehensive error handling dan recovery
- **Clean Output**: Suppress urllib3 warnings untuk output yang bersih

## Troubleshooting

### Aplikasi tidak muncul di status bar

- Pastikan menjalankan di macOS
- Check permission sistem untuk menjalankan aplikasi Python
- Restart aplikasi jika diperlukan

### Error koneksi API

- Periksa koneksi internet
- CoinGecko API mungkin mengalami rate limiting
- Aplikasi akan otomatis adjust refresh interval jika rate limited

### High CPU usage

- Kurangi jumlah coins yang dipantau (aplikasi akan warn jika >8 coins)
- Tingkatkan refresh interval
- Restart aplikasi

### Monitoring banyak coins

- Aplikasi akan otomatis adjust interval untuk banyak coins
- Warning muncul jika monitoring >8 coins
- Rate limiting protection akan aktif otomatis

## Dependencies

- `rumps`: Framework untuk membuat aplikasi status bar macOS
- `requests`: HTTP library untuk API calls

## Lisensi

MIT License

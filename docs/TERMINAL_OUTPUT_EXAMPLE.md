# Expected Terminal Output from Deep Learning Script

## Normal Operation Output

When `deep.py` is running correctly, you should see output like this:

```
================================================================================================
LD2410 BREATHING DETECTION - CNN+LSTM + FFT
================================================================================================
  Frame     Dist      Freq       Pwr       Ent  FFT_Conf  DL_Conf    Votes      Detection       Time
------------------------------------------------------------------------------------------------
[*] Starting detection loop...
[*] Deep Learning Model: CNN+LSTM
[*] Detection Threshold: 0.85 | Voting Window: 32
[*] GPS enabled: Will attach coordinates on detection
------------------------------------------------------------------------------------------------

[*] Loading model: cnn_lstm_fast_final_model.pt
[✓] Model loaded successfully
[*] Model device: cpu
[*] Model parameters: 2,345,678
[*] Opening serial /dev/ttyUSB0 @ 115200
[✓] Serial connected

     0   125.50    0.250    85.30    4.20     0.750     0.820   18/32            NO   10:30:45
     1   125.80    0.255    86.10    4.15     0.760     0.835   19/32            NO   10:30:46
     2   126.20    0.260    87.50    4.10     0.780     0.850   20/32            NO   10:30:47
     3   126.50    0.265    88.20    4.05     0.790     0.865   21/32            NO   10:30:48
     4   127.10    0.270    89.10    4.00     0.800     0.880   22/32            NO   10:30:49
     5   127.50    0.275    90.50    3.95     0.820     0.895   23/32            NO   10:30:50
     6   128.20    0.280    91.20    3.90     0.840     0.910   24/32            NO   10:30:51
     7   128.80    0.285    92.10    3.85     0.860     0.925   25/32            NO   10:30:52
     8   129.50    0.290    93.50    3.80     0.880     0.940   26/32            NO   10:30:53
     9   130.20    0.295    94.20    3.75     0.900     0.955   27/32            NO   10:30:54
    10   131.00    0.300    95.10    3.70     0.920     0.970   28/32            NO   10:30:55
    11   131.50    0.305    96.50    3.65     0.940     0.985   29/32            NO   10:30:56
    12   132.20    0.310    97.20    3.60     0.960     0.990   30/32            NO   10:30:57
    13   133.00    0.315    98.10    3.55     0.980     0.995   31/32            NO   10:30:58
    14   133.50    0.320    99.50    3.50     1.000     0.998   32/32      BREATHING   10:30:59 | GPS: 37.774929, -122.419418
[DETECTION] Frame 14: BREATHING | Distance: 133.50cm | FFT: 1.000 | DL: 0.998 | Votes: 32/32
[GPS] Person detected at: 37.774929, -122.419418
```

## Column Descriptions

- **Frame**: Sequential frame number
- **Dist**: Distance in cm from sensor
- **Freq**: Peak breathing frequency (Hz)
- **Pwr**: Peak power in frequency domain
- **Ent**: Spectral entropy
- **FFT_Conf**: FFT-based confidence score (0.0-1.0)
- **DL_Conf**: Deep Learning confidence score (0.0-1.0)
- **Votes**: Number of positive votes in voting window (e.g., 18/32)
- **Detection**: Status: "BREATHING" or "NO"
- **Time**: Current time (HH:MM:SS)
- **GPS**: GPS coordinates (only shown when person is detected)

## Detection Logic

1. **FFT Analysis**: Extracts breathing features from distance signal
2. **Deep Learning**: CNN+LSTM model analyzes BS matrix (if available)
3. **Voting**: Uses max(FFT_Conf, DL_Conf) in a sliding window
4. **Threshold**: Detection occurs when votes >= 18 out of 32 window
5. **GPS**: When person detected, GPS coordinates are fetched and attached

## What Gets Sent to API

Each detection sends:
```json
{
  "breathing": true,
  "freq": 0.320,
  "power": 99.50,
  "entropy": 3.50,
  "distance": 133.50,
  "fft_conf": 1.000,
  "dl_conf": 0.998,
  "votes": 32,
  "voting_window": 32,
  "latitude": 37.774929,
  "longitude": -122.419418
}
```

## Map Display

- Yellow markers appear on map when:
  - `breathing == true`
  - GPS coordinates are available
  - Deep learning confidence is shown in popup

## Troubleshooting

**No output?**
- Check serial port: `/dev/ttyUSB0` (or correct port)
- Check if sensor is sending data
- Verify Flask is running on port 5050

**Model not loading?**
- Check if `cnn_lstm_fast_final_model.pt` exists
- Script will continue with FFT-only mode

**No GPS coordinates?**
- Check if `neo6m_runner.py` is running
- Verify GPS module is connected and sending data
- Check `/api/gps/current` endpoint

**No detections on map?**
- Ensure GPS coordinates are being sent with detections
- Check browser console for errors
- Verify `/api/latest` returns records with GPS


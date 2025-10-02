# Feature Analysis Report for NBA Player Archetype Clustering
Generated: 2025-10-01 16:00:04.591723

## Executive Summary
- Total features analyzed: 47
- Players in dataset: 178
- Zero variance features: 0
- High correlation pairs (>0.9): 11
- Optimal number of clusters: 2
- Best silhouette score: 0.221

## Feature Quality Assessment
### Low Variance Features (may be unsuitable for clustering)
- FTPCT: variance=0.007591, std=0.087125
- TSPCT: variance=0.001823, std=0.042696
- TRBPCT: variance=0.001647, std=0.040579
- ASTPCT: variance=0.007965, std=0.089249
- THto10r: variance=0.006779, std=0.082336
- TENto16r: variance=0.003044, std=0.055172
- SIXTto3PTr: variance=0.000843, std=0.029027
- DRPTSPCT: variance=0.008755, std=0.093570
- DRASTPCT: variance=0.001715, std=0.041408
- DRTOVPCT: variance=0.000454, std=0.021300
- DRPFPCT: variance=0.001416, std=0.037632
- DRIMFGPCT: variance=0.000570, std=0.023872
- PNTASTPCT: variance=0.001413, std=0.037585
- PNTTVPCT: variance=0.000829, std=0.028797

### High Correlation Pairs (potential redundancy)
- THPAr ↔ AVGDIST: 0.950
- ASTPCT ↔ POTAST: 0.930
- TOP ↔ AVGSECPERTCH: 0.910
- TOP ↔ POTAST: 0.915
- AVGSECPERTCH ↔ AVGDRIBPERTCH: 0.986
- POSTUPS ↔ PSTUPFGA: 0.981
- PNTTOUCH ↔ PNTTCHS: 1.000
- PNTTOUCH ↔ PNTFGA: 0.990
- DRIVES ↔ DRFGA: 0.962
- CSFGA ↔ CS3PA: 0.965
- PNTTCHS ↔ PNTFGA: 0.990

## Clustering Performance Analysis
### Silhouette Scores by Number of Clusters
⭐ k=2: 0.221
   k=3: 0.173
   k=4: 0.168
   k=5: 0.119
   k=6: 0.118
   k=7: 0.119
   k=8: 0.091

## Recommendations
⚠️ **FAIR**: Features may produce suboptimal clusters
- Consider removing redundant features from 11 highly correlated pairs
- Consider using k=2 instead of k=8 for optimal clustering

## Detailed Feature Statistics
| Feature | Variance | Std | Mean | Min | Max | Range | Null% | Unique |
|---------|----------|-----|------|-----|-----|-------|-------|--------|
| FTPCT | 0.007591 | 0.087125 | 0.787 | 0.513 | 0.966 | 0.453 | 0.0% | 131 |
| TSPCT | 0.001823 | 0.042696 | 0.586 | 0.494 | 0.724 | 0.230 | 0.0% | 113 |
| THPAr | 0.041402 | 0.203475 | 0.422 | 0.000 | 0.868 | 0.868 | 0.0% | 174 |
| FTr | 0.012102 | 0.110010 | 0.239 | 0.046 | 0.657 | 0.611 | 0.0% | 178 |
| TRBPCT | 0.001647 | 0.040579 | 0.089 | 0.029 | 0.203 | 0.174 | 0.0% | 94 |
| ASTPCT | 0.007965 | 0.089249 | 0.170 | 0.044 | 0.452 | 0.408 | 0.0% | 134 |
| AVGDIST | 21.113392 | 4.594931 | 13.974 | 1.931 | 22.229 | 20.297 | 0.0% | 178 |
| Zto3r | 0.019286 | 0.138874 | 0.065 | 0.000 | 0.837 | 0.837 | 0.0% | 52 |
| THto10r | 0.006779 | 0.082336 | 0.045 | 0.000 | 0.338 | 0.338 | 0.0% | 52 |
| TENto16r | 0.003044 | 0.055172 | 0.026 | 0.000 | 0.319 | 0.319 | 0.0% | 52 |
| SIXTto3PTr | 0.000843 | 0.029027 | 0.012 | 0.000 | 0.203 | 0.203 | 0.0% | 50 |
| HEIGHT | 9.955056 | 3.155163 | 78.449 | 72.000 | 86.000 | 14.000 | 0.0% | 15 |
| WINGSPAN | 1551.195377 | 39.385218 | 53.552 | 0.000 | 92.500 | 92.500 | 0.0% | 51 |
| FRNTCTTCH | 70.559779 | 8.399987 | 25.466 | 10.200 | 56.200 | 46.000 | 0.0% | 125 |
| TOP | 3.410337 | 1.846710 | 2.611 | 0.400 | 8.600 | 8.200 | 0.0% | 57 |
| AVGSECPERTCH | 1.420533 | 1.191861 | 2.908 | 1.200 | 6.060 | 4.860 | 0.0% | 141 |
| AVGDRIBPERTCH | 1.935803 | 1.391331 | 2.167 | 0.270 | 6.040 | 5.770 | 0.0% | 152 |
| ELBWTCH | 2.150017 | 1.466294 | 1.221 | 0.100 | 10.100 | 10.000 | 0.0% | 41 |
| POSTUPS | 1.426161 | 1.194220 | 0.673 | 0.000 | 8.800 | 8.800 | 0.0% | 33 |
| PNTTOUCH | 6.042054 | 2.458059 | 2.447 | 0.200 | 10.900 | 10.700 | 0.0% | 62 |
| DRIVES | 20.752582 | 4.555500 | 5.965 | 0.100 | 20.600 | 20.500 | 0.0% | 108 |
| DRFGA | 4.690749 | 2.165814 | 2.739 | 0.000 | 10.200 | 10.200 | 0.0% | 66 |
| DRPTSPCT | 0.008755 | 0.093570 | 0.487 | 0.000 | 1.000 | 1.000 | 0.0% | 118 |
| DRPASSPCT | 0.016669 | 0.129109 | 0.369 | 0.082 | 0.746 | 0.664 | 0.0% | 143 |
| DRASTPCT | 0.001715 | 0.041408 | 0.093 | 0.000 | 0.242 | 0.242 | 0.0% | 99 |
| DRTOVPCT | 0.000454 | 0.021300 | 0.065 | 0.000 | 0.148 | 0.148 | 0.0% | 72 |
| DRPFPCT | 0.001416 | 0.037632 | 0.071 | 0.000 | 0.227 | 0.227 | 0.0% | 103 |
| DRIMFGPCT | 0.000570 | 0.023872 | 0.636 | 0.553 | 0.705 | 0.152 | 0.0% | 163 |
| CSFGA | 2.294842 | 1.514874 | 3.265 | 0.100 | 8.000 | 7.900 | 0.0% | 59 |
| CS3PA | 2.399525 | 1.549040 | 3.016 | 0.000 | 7.800 | 7.800 | 0.0% | 52 |
| PASSESMADE | 157.786442 | 12.561307 | 33.838 | 13.400 | 76.600 | 63.200 | 0.0% | 143 |
| SECAST | 0.089060 | 0.298429 | 0.453 | 0.000 | 1.400 | 1.400 | 0.0% | 15 |
| POTAST | 13.387373 | 3.658876 | 5.849 | 1.000 | 20.700 | 19.700 | 0.0% | 91 |
| PUFGA | 8.797604 | 2.966076 | 3.184 | 0.000 | 11.900 | 11.900 | 0.0% | 77 |
| PU3PA | 3.078306 | 1.754510 | 1.538 | 0.000 | 7.600 | 7.600 | 0.0% | 50 |
| PSTUPFGA | 0.298913 | 0.546730 | 0.313 | 0.000 | 3.400 | 3.400 | 0.0% | 21 |
| PSTUPPTSPCT | 0.099719 | 0.315783 | 0.335 | 0.000 | 1.000 | 1.000 | 0.0% | 65 |
| PSTUPPASSPCT | 0.073874 | 0.271797 | 0.266 | 0.000 | 1.000 | 1.000 | 0.0% | 83 |
| PSTUPASTPCT | 0.016899 | 0.129995 | 0.065 | 0.000 | 1.000 | 1.000 | 0.0% | 68 |
| PSTUPTOVPCT | 0.014237 | 0.119317 | 0.051 | 0.000 | 1.000 | 1.000 | 0.0% | 60 |
| PNTTCHS | 6.042054 | 2.458059 | 2.447 | 0.200 | 10.900 | 10.700 | 0.0% | 62 |
| PNTFGA | 2.399691 | 1.549093 | 1.412 | 0.000 | 7.300 | 7.300 | 0.0% | 49 |
| PNTPTSPCT | 0.013795 | 0.117451 | 0.632 | 0.000 | 0.857 | 0.857 | 0.0% | 120 |
| PNTPASSPCT | 0.018176 | 0.134819 | 0.317 | 0.085 | 0.833 | 0.748 | 0.0% | 143 |
| PNTASTPCT | 0.001413 | 0.037585 | 0.063 | 0.000 | 0.200 | 0.200 | 0.0% | 94 |
| PNTTVPCT | 0.000829 | 0.028797 | 0.050 | 0.000 | 0.150 | 0.150 | 0.0% | 77 |
| AVGFGATTEMPTEDAGAINSTPERGAME | 0.062379 | 0.249758 | 0.800 | 0.355 | 1.955 | 1.600 | 0.0% | 177 |
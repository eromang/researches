# Cross-Model Confidence Pattern Comparison

**Models compared:** deepseek-r1, gemma3n, llama31, mistral, phi4, qwen3, qwen3-nothink
**Categories:** 5

---

## 1. Overall detection rates at Confirmed level (all actors pooled)

| Category | deepseek-r1 | gemma3n | llama31 | mistral | phi4 | qwen3 | qwen3-nothink |
|---|---|---|---|---|---|---|---|
| Evid. qual. | 1.6% | 13.4% | 6.7% | 0.1% | 0.1% | 16.3% | 9.5% |
| Misattr. | 6.6% | 13.2% | 13.9% | 0.1% | 5.5% | 16.6% | 7.2% |
| Corroboration | 6.2% | 66.2% | 12.6% | 0.2% | 10.4% | 34.3% | 18.0% |
| Contextual | 46.5% | 36.7% | 1.7% | 0.3% | 18.4% | 53.0% | 19.9% |
| Procedural | 0.4% | 0.1% | 0.5% | 0.0% | 0.2% | 0.2% | 0.0% |

---

## 2. Model pairwise tests (Confirmed, all actors pooled)

| Model pair | Category | Rate 1 | Rate 2 | h | p | Sig? |
|---|---|---|---|---|---|---|
| deepseek-r1 vs gemma3n | Evid. qual. | 1.6% | 13.4% | -0.500 | 0.0000 | yes |
| deepseek-r1 vs gemma3n | Misattr. | 6.6% | 13.2% | -0.226 | 0.0000 | yes |
| deepseek-r1 vs gemma3n | Corroboration | 6.2% | 66.2% | -1.401 | 0.0000 | yes |
| deepseek-r1 vs gemma3n | Contextual | 46.5% | 36.7% | 0.200 | 0.0000 | yes |
| deepseek-r1 vs gemma3n | Procedural | 0.4% | 0.1% | 0.065 | 0.1788 | no |
| deepseek-r1 vs llama31 | Evid. qual. | 1.6% | 6.7% | -0.272 | 0.0000 | yes |
| deepseek-r1 vs llama31 | Misattr. | 6.6% | 13.9% | -0.244 | 0.0000 | yes |
| deepseek-r1 vs llama31 | Corroboration | 6.2% | 12.6% | -0.225 | 0.0000 | yes |
| deepseek-r1 vs llama31 | Contextual | 46.5% | 1.7% | 1.242 | 0.0000 | yes |
| deepseek-r1 vs llama31 | Procedural | 0.4% | 0.5% | -0.015 | 0.7395 | no |
| deepseek-r1 vs mistral | Evid. qual. | 1.6% | 0.1% | 0.186 | 0.0004 | yes |
| deepseek-r1 vs mistral | Misattr. | 6.6% | 0.1% | 0.454 | 0.0000 | yes |
| deepseek-r1 vs mistral | Corroboration | 6.2% | 0.2% | 0.410 | 0.0000 | yes |
| deepseek-r1 vs mistral | Contextual | 46.5% | 0.3% | 1.389 | 0.0000 | yes |
| deepseek-r1 vs mistral | Procedural | 0.4% | 0.0% | 0.129 | 0.0452 | yes |
| deepseek-r1 vs phi4 | Evid. qual. | 1.6% | 0.1% | 0.186 | 0.0004 | yes |
| deepseek-r1 vs phi4 | Misattr. | 6.6% | 5.5% | 0.044 | 0.3352 | no |
| deepseek-r1 vs phi4 | Corroboration | 6.2% | 10.4% | -0.156 | 0.0007 | yes |
| deepseek-r1 vs phi4 | Contextual | 46.5% | 18.4% | 0.613 | 0.0000 | yes |
| deepseek-r1 vs phi4 | Procedural | 0.4% | 0.2% | 0.038 | 0.4128 | no |
| deepseek-r1 vs qwen3 | Evid. qual. | 1.6% | 16.3% | -0.580 | 0.0000 | yes |
| deepseek-r1 vs qwen3 | Misattr. | 6.6% | 16.6% | -0.320 | 0.0000 | yes |
| deepseek-r1 vs qwen3 | Corroboration | 6.2% | 34.3% | -0.750 | 0.0000 | yes |
| deepseek-r1 vs qwen3 | Contextual | 46.5% | 53.0% | -0.129 | 0.0046 | yes |
| deepseek-r1 vs qwen3 | Procedural | 0.4% | 0.2% | 0.038 | 0.4135 | no |
| deepseek-r1 vs qwen3-nothink | Evid. qual. | 1.6% | 9.5% | -0.375 | 0.0000 | yes |
| deepseek-r1 vs qwen3-nothink | Misattr. | 6.6% | 7.2% | -0.024 | 0.5927 | no |
| deepseek-r1 vs qwen3-nothink | Corroboration | 6.2% | 18.0% | -0.376 | 0.0000 | yes |
| deepseek-r1 vs qwen3-nothink | Contextual | 46.5% | 19.9% | 0.576 | 0.0000 | yes |
| deepseek-r1 vs qwen3-nothink | Procedural | 0.4% | 0.0% | 0.129 | 0.0452 | yes |
| gemma3n vs llama31 | Evid. qual. | 13.4% | 6.7% | 0.228 | 0.0000 | yes |
| gemma3n vs llama31 | Misattr. | 13.2% | 13.9% | -0.018 | 0.6890 | no |
| gemma3n vs llama31 | Corroboration | 66.2% | 12.6% | 1.176 | 0.0000 | yes |
| gemma3n vs llama31 | Contextual | 36.7% | 1.7% | 1.042 | 0.0000 | yes |
| gemma3n vs llama31 | Procedural | 0.1% | 0.5% | -0.080 | 0.1019 | no |
| gemma3n vs mistral | Evid. qual. | 13.4% | 0.1% | 0.686 | 0.0000 | yes |
| gemma3n vs mistral | Misattr. | 13.2% | 0.1% | 0.680 | 0.0000 | yes |
| gemma3n vs mistral | Corroboration | 66.2% | 0.2% | 1.810 | 0.0000 | yes |
| gemma3n vs mistral | Contextual | 36.7% | 0.3% | 1.189 | 0.0000 | yes |
| gemma3n vs mistral | Procedural | 0.1% | 0.0% | 0.065 | 0.3172 | no |
| gemma3n vs phi4 | Evid. qual. | 13.4% | 0.1% | 0.686 | 0.0000 | yes |
| gemma3n vs phi4 | Misattr. | 13.2% | 5.5% | 0.270 | 0.0000 | yes |
| gemma3n vs phi4 | Corroboration | 66.2% | 10.4% | 1.244 | 0.0000 | yes |
| gemma3n vs phi4 | Contextual | 36.7% | 18.4% | 0.413 | 0.0000 | yes |
| gemma3n vs phi4 | Procedural | 0.1% | 0.2% | -0.027 | 0.5634 | no |
| gemma3n vs qwen3 | Evid. qual. | 13.4% | 16.3% | -0.080 | 0.0814 | no |
| gemma3n vs qwen3 | Misattr. | 13.2% | 16.6% | -0.094 | 0.0393 | yes |
| gemma3n vs qwen3 | Corroboration | 66.2% | 34.3% | 0.650 | 0.0000 | yes |
| gemma3n vs qwen3 | Contextual | 36.7% | 53.0% | -0.329 | 0.0000 | yes |
| gemma3n vs qwen3 | Procedural | 0.1% | 0.2% | -0.027 | 0.5628 | no |
| gemma3n vs qwen3-nothink | Evid. qual. | 13.4% | 9.5% | 0.125 | 0.0065 | yes |
| gemma3n vs qwen3-nothink | Misattr. | 13.2% | 7.2% | 0.202 | 0.0000 | yes |
| gemma3n vs qwen3-nothink | Corroboration | 66.2% | 18.0% | 1.025 | 0.0000 | yes |
| gemma3n vs qwen3-nothink | Contextual | 36.7% | 19.9% | 0.376 | 0.0000 | yes |
| gemma3n vs qwen3-nothink | Procedural | 0.1% | 0.0% | 0.065 | 0.3172 | no |
| llama31 vs mistral | Evid. qual. | 6.7% | 0.1% | 0.458 | 0.0000 | yes |
| llama31 vs mistral | Misattr. | 13.9% | 0.1% | 0.698 | 0.0000 | yes |
| llama31 vs mistral | Corroboration | 12.6% | 0.2% | 0.635 | 0.0000 | yes |
| llama31 vs mistral | Contextual | 1.7% | 0.3% | 0.147 | 0.0027 | yes |
| llama31 vs mistral | Procedural | 0.5% | 0.0% | 0.144 | 0.0252 | yes |
| llama31 vs phi4 | Evid. qual. | 6.7% | 0.1% | 0.458 | 0.0000 | yes |
| llama31 vs phi4 | Misattr. | 13.9% | 5.5% | 0.288 | 0.0000 | yes |
| llama31 vs phi4 | Corroboration | 12.6% | 10.4% | 0.069 | 0.1332 | no |
| llama31 vs phi4 | Contextual | 1.7% | 18.4% | -0.629 | 0.0000 | yes |
| llama31 vs phi4 | Procedural | 0.5% | 0.2% | 0.053 | 0.2560 | no |
| llama31 vs qwen3 | Evid. qual. | 6.7% | 16.3% | -0.308 | 0.0000 | yes |
| llama31 vs qwen3 | Misattr. | 13.9% | 16.6% | -0.076 | 0.0965 | no |
| llama31 vs qwen3 | Corroboration | 12.6% | 34.3% | -0.526 | 0.0000 | yes |
| llama31 vs qwen3 | Contextual | 1.7% | 53.0% | -1.371 | 0.0000 | yes |
| llama31 vs qwen3 | Procedural | 0.5% | 0.2% | 0.053 | 0.2565 | no |
| llama31 vs qwen3-nothink | Evid. qual. | 6.7% | 9.5% | -0.104 | 0.0237 | yes |
| llama31 vs qwen3-nothink | Misattr. | 13.9% | 7.2% | 0.220 | 0.0000 | yes |
| llama31 vs qwen3-nothink | Corroboration | 12.6% | 18.0% | -0.151 | 0.0010 | yes |
| llama31 vs qwen3-nothink | Contextual | 1.7% | 19.9% | -0.666 | 0.0000 | yes |
| llama31 vs qwen3-nothink | Procedural | 0.5% | 0.0% | 0.144 | 0.0252 | yes |
| mistral vs phi4 | Evid. qual. | 0.1% | 0.1% | 0.000 | 1.0000 | no |
| mistral vs phi4 | Misattr. | 0.1% | 5.5% | -0.410 | 0.0000 | yes |
| mistral vs phi4 | Corroboration | 0.2% | 10.4% | -0.566 | 0.0000 | yes |
| mistral vs phi4 | Contextual | 0.3% | 18.4% | -0.776 | 0.0000 | yes |
| mistral vs phi4 | Procedural | 0.0% | 0.2% | -0.091 | 0.1571 | no |
| mistral vs qwen3 | Evid. qual. | 0.1% | 16.3% | -0.766 | 0.0000 | yes |
| mistral vs qwen3 | Misattr. | 0.1% | 16.6% | -0.774 | 0.0000 | yes |
| mistral vs qwen3 | Corroboration | 0.2% | 34.3% | -1.160 | 0.0000 | yes |
| mistral vs qwen3 | Contextual | 0.3% | 53.0% | -1.518 | 0.0000 | yes |
| mistral vs qwen3 | Procedural | 0.0% | 0.2% | -0.091 | 0.1569 | no |
| mistral vs qwen3-nothink | Evid. qual. | 0.1% | 9.5% | -0.561 | 0.0000 | yes |
| mistral vs qwen3-nothink | Misattr. | 0.1% | 7.2% | -0.478 | 0.0000 | yes |
| mistral vs qwen3-nothink | Corroboration | 0.2% | 18.0% | -0.785 | 0.0000 | yes |
| mistral vs qwen3-nothink | Contextual | 0.3% | 19.9% | -0.813 | 0.0000 | yes |
| mistral vs qwen3-nothink | Procedural | 0.0% | 0.0% | 0.000 | — | no |
| phi4 vs qwen3 | Evid. qual. | 0.1% | 16.3% | -0.766 | 0.0000 | yes |
| phi4 vs qwen3 | Misattr. | 5.5% | 16.6% | -0.364 | 0.0000 | yes |
| phi4 vs qwen3 | Corroboration | 10.4% | 34.3% | -0.594 | 0.0000 | yes |
| phi4 vs qwen3 | Contextual | 18.4% | 53.0% | -0.743 | 0.0000 | yes |
| phi4 vs qwen3 | Procedural | 0.2% | 0.2% | -0.000 | 0.9992 | no |
| phi4 vs qwen3-nothink | Evid. qual. | 0.1% | 9.5% | -0.561 | 0.0000 | yes |
| phi4 vs qwen3-nothink | Misattr. | 5.5% | 7.2% | -0.069 | 0.1344 | no |
| phi4 vs qwen3-nothink | Corroboration | 10.4% | 18.0% | -0.220 | 0.0000 | yes |
| phi4 vs qwen3-nothink | Contextual | 18.4% | 19.9% | -0.037 | 0.4169 | no |
| phi4 vs qwen3-nothink | Procedural | 0.2% | 0.0% | 0.091 | 0.1571 | no |
| qwen3 vs qwen3-nothink | Evid. qual. | 16.3% | 9.5% | 0.204 | 0.0000 | yes |
| qwen3 vs qwen3-nothink | Misattr. | 16.6% | 7.2% | 0.296 | 0.0000 | yes |
| qwen3 vs qwen3-nothink | Corroboration | 34.3% | 18.0% | 0.375 | 0.0000 | yes |
| qwen3 vs qwen3-nothink | Contextual | 53.0% | 19.9% | 0.706 | 0.0000 | yes |
| qwen3 vs qwen3-nothink | Procedural | 0.2% | 0.0% | 0.091 | 0.1569 | no |

**Summary:** 79/105 tests significant at p<0.05.

---

## 3. Actor uniformity comparison

| Model | Pairwise sig. (p<0.05) | Total tests | Uniformity |
|---|---|---|---|
| deepseek-r1 | 1 | 50 | Actor-uniform |
| gemma3n | 13 | 50 | Actor-differentiated |
| llama31 | 3 | 50 | Mostly uniform |
| mistral | 0 | 50 | Actor-uniform |
| phi4 | 10 | 50 | Moderately differentiated |
| qwen3 | 1 | 50 | Actor-uniform |
| qwen3-nothink | 8 | 50 | Moderately differentiated |

---

## 4. Model-specific vocabulary (top 10 n-grams)

### deepseek-r1

| N-gram | Doc rate |
|---|---|
| confidence moderate | 64.4% |
| confidence high | 54.9% |
| e g | 60.7% |
| attribution confidence | 72.2% |
| geopolitical implications | 67.3% |
| state sponsored | 51.8% |
| escalation risk | 59.1% |
| definitive proof | 50.6% |
| implications confidence | 52.6% |
| geopolitical implications confidence | 52.6% |

### gemma3n

| N-gram | Doc rate |
|---|---|
| linked actors | 64.7% |
| definitive attribution | 49.3% |
| moderate rationale | 51.4% |
| state sponsored | 39.9% |
| preliminary intelligence | 35.4% |
| strong technical | 39.7% |
| attribution remains | 37.1% |
| publicly available | 33.9% |
| needed to confirm | 32.5% |
| moderate confidence | 28.6% |

### llama31

| N-gram | Doc rate |
|---|---|
| geopolitical implications | 80.2% |
| attribution confidence | 78.4% |
| escalation risks | 69.1% |
| confidence moderate | 63.6% |
| linked actors | 61.3% |
| attribution confidence moderate | 61.5% |
| implications high | 50.3% |
| geopolitical implications high | 50.3% |
| confidence level | 16.7% |
| moderate reasoning | 24.4% |

### mistral

| N-gram | Doc rate |
|---|---|
| geopolitical implications | 96.7% |
| escalation risks | 96.7% |
| defensive priorities | 73.6% |
| attribution confidence | 68.1% |
| linked actors | 65.9% |
| risks moderate | 62.6% |
| escalation risks moderate | 62.6% |
| priorities high | 54.9% |
| defensive priorities high | 54.9% |
| implications moderate | 50.5% |

### phi4

| N-gram | Doc rate |
|---|---|
| confidence moderate | 85.3% |
| confidence high | 85.7% |
| geopolitical implications | 96.0% |
| escalation risks | 93.6% |
| attribution confidence | 95.5% |
| linked actors | 73.4% |
| implications confidence | 70.2% |
| geopolitical implications confidence | 70.2% |
| risks confidence | 68.5% |
| escalation risks confidence | 68.5% |

### qwen3

| N-gram | Doc rate |
|---|---|
| e g | 66.5% |
| linked actors | 61.7% |
| confidence level | 47.3% |
| strong technical | 40.3% |
| technical and intelligence | 38.1% |
| intelligence evidence | 38.0% |
| technical and intelligence evidence | 38.0% |
| state sponsored | 35.4% |
| level moderate | 36.2% |
| confidence level moderate | 36.2% |

### qwen3-nothink

| N-gram | Doc rate |
|---|---|
| confidence moderate | 74.6% |
| confidence high | 74.4% |
| geopolitical implications | 83.5% |
| defensive priorities | 79.5% |
| attribution confidence | 78.5% |
| linked actors | 68.5% |
| priorities confidence | 71.3% |
| defensive priorities confidence | 71.3% |
| priorities confidence high | 71.3% |
| defensive priorities confidence high | 71.3% |

---

## 5. Key observations


---

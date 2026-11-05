\# SecureVoiceAI



\## Speaker Verification Performance Benchmark



\*\*Evaluation Date:\*\* 5 November 2026

\*\*Model:\*\* SpeechBrain ECAPA-TDNN

\*\*Pretrained Model:\*\* `speechbrain/spkrec-ecapa-voxceleb`

\*\*Evaluation Dataset:\*\* VoxCeleb1 Test

\*\*Evaluation Script:\*\* `evaluate\_speaker\_verification.py`



\---



\## 1. Overview



SecureVoiceAI uses an ECAPA-TDNN speaker embedding model to perform voice-based speaker verification.



This benchmark evaluates the model's ability to distinguish between genuine speaker pairs and impostor speaker pairs using the official VoxCeleb1 test trial list.



The evaluation measures:



\* False Acceptance Rate (FAR)

\* False Rejection Rate (FRR)

\* Verification Accuracy

\* Equal Error Rate (EER)

\* Optimal equal-error threshold



\## 2. Dataset



| Metric                      |          Value |

| --------------------------- | -------------: |

| Dataset                     | VoxCeleb1 Test |

| Total evaluation pairs      |         37,611 |

| Genuine pairs               |         18,802 |

| Impostor pairs              |         18,809 |

| Unique recordings processed |          4,708 |



The evaluation used the VoxCeleb1 test trial file, `veri\_test2.txt`.



A genuine pair contains recordings from the same speaker. An impostor pair contains recordings from different speakers.



The downloaded audio archive was verified against its published MD5 checksum before extraction.



\## 3. Evaluation Results



\### Application Threshold: 0.60



| Performance Metric          |           Result |

| --------------------------- | ---------------: |

| False Acceptance Rate (FAR) |          0.0000% |

| False Rejection Rate (FRR)  |         50.3936% |

| Accuracy                    |         74.8079% |

| Equal Error Rate (EER)      |          0.8985% |

| EER Threshold               |           0.2802 |

| Processing Time             | 3,846.21 seconds |



\### Confusion Matrix



| Result        |  Count |

| ------------- | -----: |

| True Accepts  |  9,327 |

| False Accepts |      0 |

| True Rejects  | 18,809 |

| False Rejects |  9,475 |



At the application's current threshold of 0.60, the evaluation produced no false acceptances among the 18,809 tested impostor pairs.



However, the false rejection rate was approximately 50.39%, indicating that many genuine pairs did not reach the current acceptance threshold.



\## 4. Understanding the Metrics



\*\*False Acceptance Rate (FAR)\*\*

The percentage of impostor attempts incorrectly accepted as genuine speakers.



\*\*False Rejection Rate (FRR)\*\*

The percentage of genuine speaker attempts incorrectly rejected.



\*\*Accuracy\*\*

The percentage of all evaluated pairs classified correctly.



\*\*Equal Error Rate (EER)\*\*

The point where FAR and FRR are approximately equal. A lower EER generally indicates better speaker verification performance.



\*\*EER Threshold\*\*

The similarity threshold corresponding to the estimated equal-error operating point.



\## 5. Threshold Analysis



The application currently uses a cosine similarity threshold of 0.60.



The benchmark estimated an EER threshold of approximately 0.2802, with an EER of 0.8985%.



These thresholds serve different purposes:



\* The application threshold controls the current authentication decision.

\* The EER threshold represents a point where false acceptance and false rejection rates are approximately balanced.



The EER threshold should not automatically replace the application's current threshold.



A production threshold must be selected according to security requirements, acceptable rejection rates, and additional calibration testing.



The complete threshold analysis is generated in:



`Data/Evaluation/results/threshold\_analysis.csv`



\## 6. Technical Implementation



The evaluation pipeline performs the following operations:



1\. Loads the pretrained ECAPA-TDNN speaker verification model.

2\. Reads genuine and impostor pairs from the VoxCeleb1 trial list.

3\. Loads and preprocesses the corresponding audio recordings.

4\. Generates speaker embeddings.

5\. Caches embeddings to avoid repeatedly processing the same recording.

6\. Calculates cosine similarity between speaker embeddings.

7\. Evaluates authentication decisions at the configured threshold.

8\. Calculates FAR, FRR, accuracy, and EER.

9\. Saves evaluation metrics in JSON format and threshold results in CSV format.



\### Generated Evaluation Files



\* `evaluation\_metrics.json` â€” Overall benchmark results.

\* `threshold\_analysis.csv` â€” Performance metrics at different thresholds.



\## 7. Performance Interpretation



The benchmark demonstrates that the system can distinguish genuine and impostor speaker pairs with a low estimated equal-error rate.



However, the results at the current application threshold reveal a significant false rejection problem.



This suggests that the threshold requires further investigation and calibration before the system can be considered suitable for a production authentication environment.



The zero false acceptance count is an observation from this particular test set. It does not establish that the system has a zero false acceptance rate in all real-world situations.



\## 8. Limitations



The following limitations should be considered:



1\. The benchmark evaluates pairwise speaker verification and does not measure the entire application's user experience.

2\. The model is a pretrained VoxCeleb-based checkpoint; this evaluation should not be presented as independent validation on a completely unrelated speaker corpus.

3\. Performance may vary with microphones, background noise, recording devices, accents, and speaking conditions.

4\. Processing time depends on the hardware and software environment used for evaluation.

5\. The benchmark does not evaluate liveness detection or audio replay/spoofing resistance.

6\. Further testing on independent datasets and real-world recordings is necessary.



\## 9. Future Improvements



Potential improvements include:



\* Calibrating the authentication threshold using a separate validation dataset.

\* Evaluating performance under different background noise conditions.

\* Testing recordings from different microphones and devices.

\* Adding ROC and DET curve visualizations.

\* Measuring latency under different hardware configurations.

\* Investigating spoofing and replay-attack detection as a separate security feature.



\## 10. Conclusion



The SecureVoiceAI speaker verification engine was evaluated using 37,611 genuine and impostor trials from the VoxCeleb1 Test dataset.



The benchmark achieved an estimated Equal Error Rate of \*\*0.8985%\*\*.



At the application's current similarity threshold of 0.60, the system achieved an accuracy of \*\*74.8079%\*\*, with a measured FAR of \*\*0.0000%\*\* and FRR of \*\*50.3936%\*\* on the evaluated pairs.



These results provide a measurable baseline for future improvements to the SecureVoiceAI speaker verification system.



\---



\*\*Project:\*\* SecureVoiceAI

\*\*Repository:\*\* https://github.com/Parvezz22/SecureVoiceAI

\*\*Benchmark:\*\* VoxCeleb1 Test Speaker Verification Evaluation

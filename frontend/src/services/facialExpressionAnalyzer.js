/**
 * AutoViva Production-Ready Facial Expression Analyzer Service (v2.0)
 * Powered by MediaPipe Face Landmarker & Calibrated Blendshape Coefficients.
 * 
 * Target Expression States:
 * 1. Happy
 * 2. Sad
 * 3. Angry
 * 4. Confused
 * 5. Stressed / Anxious
 * 6. Neutral
 * 7. Uncertain
 * 
 * Key Features:
 * - Uses existing student webcam <video> element (Zero secondary getUserMedia calls).
 * - Calibrated sensitivity multipliers to detect subtle micro-expressions (Sad, Angry, Confused, Stressed).
 * - Temporal rolling-window smoothing (N=15 frames) with recency-weighted voting.
 * - Debug mode (`window.autovivaDebugExpressions = true`) for real-time score inspection.
 * - 100% Client-side processing — zero backend model dependencies or startup blocking.
 */

import { FaceLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';

class FacialExpressionAnalyzer {
  constructor() {
    this.faceLandmarker = null;
    this.isInitializing = false;
    this.isReady = false;
    this.initError = null;

    // Temporal Smoothing Rolling Window (N = 15 frames ~3 seconds)
    this.windowSize = 15;
    this.history = [];

    // Debug logging flag
    this.debugMode = true;

    // Session Analytics Accumulator
    this.sessionStats = {
      totalSamples: 0,
      faceDetectedSamples: 0,
      noFaceSamples: 0,
      multipleFacesSamples: 0,
      uncertainSamples: 0,
      totalConfidenceSum: 0,
      expressionCounts: {
        NEUTRAL: 0,
        HAPPY: 0,
        SAD: 0,
        ANGRY: 0,
        CONFUSED: 0,
        STRESSED: 0,
        SURPRISE: 0
      }
    };

    // Sampling Throttle (4 FPS = ~250ms interval)
    this.sampleIntervalMs = 250;
    this.lastSampleTime = 0;
    this.isProcessingFrame = false;
  }

  /**
   * Initializes MediaPipe FaceLandmarker ONCE during viva camera startup.
   */
  async initialize() {
    if (this.isReady || this.isInitializing) return true;
    this.isInitializing = true;
    this.initError = null;

    try {
      console.log('[FacialExpressionAnalyzer] Resolving MediaPipe Vision Wasm files...');
      const filesetResolver = await FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
      );

      console.log('[FacialExpressionAnalyzer] Loading FaceLandmarker model...');
      this.faceLandmarker = await FaceLandmarker.createFromOptions(filesetResolver, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
          delegate: 'GPU'
        },
        outputFaceBlendshapes: true,
        runningMode: 'VIDEO',
        numFaces: 2
      });

      this.isReady = true;
      this.isInitializing = false;
      console.log('[FacialExpressionAnalyzer v2.0] Model loaded & calibrated.');
      return true;
    } catch (err) {
      console.warn('[FacialExpressionAnalyzer] GPU init fallback to CPU:', err);
      try {
        const filesetResolver = await FilesetResolver.forVisionTasks(
          'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
        );
        this.faceLandmarker = await FaceLandmarker.createFromOptions(filesetResolver, {
          baseOptions: {
            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
            delegate: 'CPU'
          },
          outputFaceBlendshapes: true,
          runningMode: 'VIDEO',
          numFaces: 2
        });
        this.isReady = true;
        this.isInitializing = false;
        return true;
      } catch (cpuErr) {
        console.error('[FacialExpressionAnalyzer] Failed to initialize MediaPipe model:', cpuErr);
        this.initError = 'Facial analysis unavailable';
        this.isInitializing = false;
        this.isReady = false;
        return false;
      }
    }
  }

  /**
   * Processes a video frame from the existing HTML <video> element.
   */
  analyzeVideoFrame(videoElement, timestampMs = performance.now()) {
    if (!this.isReady || !videoElement || videoElement.readyState < 2) {
      return this._buildStateOutput('MODEL_UNAVAILABLE', 'Facial analysis unavailable', false, 0);
    }

    if (timestampMs - this.lastSampleTime < this.sampleIntervalMs) {
      return this.getLastSmoothedResult();
    }
    this.lastSampleTime = timestampMs;

    if (this.isProcessingFrame) {
      return this.getLastSmoothedResult();
    }
    this.isProcessingFrame = true;

    try {
      const startTime = performance.now();
      const results = this.faceLandmarker.detectForVideo(videoElement, timestampMs);
      const latencyMs = Math.round(performance.now() - startTime);

      const numFaces = results?.faceLandmarks?.length || 0;

      if (numFaces === 0) {
        this._recordAnalytics('NO_FACE', 0);
        this.isProcessingFrame = false;
        return this._pushAndSmooth('NO_FACE', 'Face not detected', false, 0, latencyMs);
      }

      if (numFaces > 1) {
        this._recordAnalytics('MULTIPLE_FACES', 0);
        this.isProcessingFrame = false;
        return this._pushAndSmooth('MULTIPLE_FACES', 'Multiple faces detected', false, 0, latencyMs);
      }

      const blendshapes = results.faceBlendshapes?.[0]?.categories || [];
      if (!blendshapes || blendshapes.length === 0) {
        this.isProcessingFrame = false;
        return this._pushAndSmooth('LOW_CONFIDENCE', 'Low face detection confidence', true, 0.3, latencyMs);
      }

      // Classify Blendshape Coefficients using Calibrated Multi-Class Mapper
      const rawClassification = this.classifyBlendshapes(blendshapes);
      this._recordAnalytics(rawClassification.expression, rawClassification.confidence);

      this.isProcessingFrame = false;
      return this._pushAndSmooth(
        rawClassification.expression,
        `Facial Expression: ${this._formatExpressionLabel(rawClassification.expression)}`,
        true,
        rawClassification.confidence,
        latencyMs,
        rawClassification.debugScores
      );
    } catch (err) {
      console.warn('[FacialExpressionAnalyzer] Inference frame error:', err);
      this.isProcessingFrame = false;
      return this._buildStateOutput('MODEL_ERROR', 'Facial analysis error', false, 0);
    }
  }

  /**
   * Calibrated Multi-Class Expression Classifier.
   * Uses weighted composite metrics & sensitivity multipliers to detect:
   * Happy, Sad, Angry, Confused, Stressed / Anxious, Neutral, and Uncertain.
   */
  classifyBlendshapes(categories) {
    const scores = {};
    categories.forEach(c => {
      scores[c.categoryName] = c.score;
    });

    const get = (name) => scores[name] || 0.0;

    // --- 1. HAPPY METRIC ---
    // Smile + cheek elevation
    const happyRaw = (get('mouthSmileRight') + get('mouthSmileLeft') + get('cheekSquintRight') + get('cheekSquintLeft')) / 4.0;
    const happyScore = happyRaw * 1.3;

    // --- 2. SAD METRIC ---
    // Frown + inner eyebrow raise + mouth pucker/shrug
    const sadRaw = (get('mouthFrownRight') + get('mouthFrownLeft') + get('browInnerUp') * 1.5 + get('mouthShrugLower') + get('mouthPucker')) / 5.5;
    const sadScore = sadRaw * 2.8;

    // --- 3. ANGRY METRIC ---
    // Brow furrow (down) + lip press/lower + eye squint
    const browFurrow = (get('browDownRight') + get('browDownLeft')) / 2.0;
    const lipTension = (get('mouthPressRight') + get('mouthPressLeft') + get('mouthLowerDownRight') + get('mouthLowerDownLeft')) / 4.0;
    const eyeSquint = (get('eyeSquintRight') + get('eyeSquintLeft')) / 2.0;
    const angryRaw = (browFurrow * 2.0 + lipTension + eyeSquint) / 4.0;
    const angryScore = angryRaw * 2.5;

    // --- 4. CONFUSED METRIC ---
    // Asymmetric eyebrow elevation (one brow raised) + brow inner + eye squint + mouth roll/pucker
    const browAsymmetry = Math.abs(get('browOuterUpRight') - get('browOuterUpLeft'));
    const confusedRaw = (browAsymmetry * 2.2 + get('browInnerUp') + eyeSquint + get('mouthRollLower')) / 5.0;
    const confusedScore = confusedRaw * 3.0;

    // --- 5. STRESSED / ANXIOUS METRIC ---
    // Worried inner eyebrow + brow tension + widened eyes + mouth stretch/compression
    const eyeWide = (get('eyeWideRight') + get('eyeWideLeft')) / 2.0;
    const mouthStretch = (get('mouthStretchRight') + get('mouthStretchLeft')) / 2.0;
    const stressedRaw = (get('browInnerUp') * 1.8 + browFurrow * 1.2 + eyeWide * 1.2 + mouthStretch * 1.5 + lipTension) / 6.7;
    const stressedScore = stressedRaw * 2.7;

    // --- 6. SURPRISE METRIC ---
    const surpriseRaw = (get('jawOpen') * 1.5 + eyeWide * 1.5 + get('browInnerUp')) / 4.0;
    const surpriseScore = surpriseRaw * 1.8;

    const candidateScores = {
      HAPPY: Number(happyScore.toFixed(3)),
      SAD: Number(sadScore.toFixed(3)),
      ANGRY: Number(angryScore.toFixed(3)),
      CONFUSED: Number(confusedScore.toFixed(3)),
      STRESSED: Number(stressedScore.toFixed(3)),
      SURPRISE: Number(surpriseScore.toFixed(3))
    };

    const candidates = [
      { name: 'HAPPY', score: happyScore },
      { name: 'SAD', score: sadScore },
      { name: 'ANGRY', score: angryScore },
      { name: 'CONFUSED', score: confusedScore },
      { name: 'STRESSED', score: stressedScore },
      { name: 'SURPRISE', score: surpriseScore }
    ];

    candidates.sort((a, b) => b.score - a.score);
    const top = candidates[0];

    if (this.debugMode || window.autovivaDebugExpressions) {
      console.log('[FacialExpression Debug Scores]:', candidateScores, `Winner: ${top.name} (${top.score.toFixed(3)})`);
    }

    // Adaptive Neutral Baseline (If top non-neutral candidate < 0.14)
    if (top.score < 0.14) {
      return {
        expression: 'NEUTRAL',
        confidence: Number(Math.min(0.95, 1.0 - top.score).toFixed(2)),
        debugScores: candidateScores
      };
    }

    // Confidence Gating (If score between 0.14 and 0.22, mark UNCERTAIN)
    if (top.score < 0.22) {
      return {
        expression: 'UNCERTAIN',
        confidence: Number((top.score * 2.5).toFixed(2)),
        debugScores: candidateScores
      };
    }

    const normalizedConf = Number(Math.min(0.96, 0.45 + top.score * 1.4).toFixed(2));
    return {
      expression: top.name,
      confidence: normalizedConf,
      debugScores: candidateScores
    };
  }

  /**
   * Recency-Weighted Temporal Rolling Window Smoothing (N=15 frames ~3s).
   */
  _pushAndSmooth(stateKey, displayLabel, faceDetected, confidence, latencyMs = 0, debugScores = {}) {
    this.history.push({ stateKey, displayLabel, faceDetected, confidence, debugScores });
    if (this.history.length > this.windowSize) {
      this.history.shift();
    }

    const counts = {};
    let totalWeight = 0;
    let weightedConfSum = 0;

    this.history.forEach((item, idx) => {
      const weight = idx + 1; // Linear recency weight
      counts[item.stateKey] = (counts[item.stateKey] || 0) + weight;
      totalWeight += weight;
      weightedConfSum += item.confidence * weight;
    });

    let maxWeight = -1;
    let smoothedState = stateKey;

    Object.keys(counts).forEach(k => {
      if (counts[k] > maxWeight) {
        maxWeight = counts[k];
        smoothedState = k;
      }
    });

    const smoothedConf = Number((weightedConfSum / totalWeight).toFixed(2));
    const formattedLabel = this._formatDisplayLabel(smoothedState);

    return {
      state: smoothedState,
      displayLabel: formattedLabel,
      faceDetected: smoothedState !== 'NO_FACE' && smoothedState !== 'MULTIPLE_FACES',
      confidence: smoothedConf,
      latencyMs,
      debugScores: this.history[this.history.length - 1]?.debugScores || {}
    };
  }

  _formatExpressionLabel(expr) {
    if (expr === 'STRESSED') return 'Stressed / Anxious';
    if (expr === 'CONFUSED') return 'Confused';
    return expr.charAt(0) + expr.slice(1).toLowerCase();
  }

  _formatDisplayLabel(stateKey) {
    if (stateKey === 'NO_FACE') return 'Face not detected';
    if (stateKey === 'MULTIPLE_FACES') return 'Multiple faces detected';
    if (stateKey === 'LOW_CONFIDENCE') return 'Low face detection confidence';
    if (stateKey === 'UNCERTAIN') return 'Facial Expression: Uncertain';
    return `Facial Expression: ${this._formatExpressionLabel(stateKey)}`;
  }

  getLastSmoothedResult() {
    if (this.history.length === 0) {
      return this._buildStateOutput('NO_FACE', 'Face not detected', false, 0);
    }
    const last = this.history[this.history.length - 1];
    return this._pushAndSmooth(last.stateKey, last.displayLabel, last.faceDetected, last.confidence);
  }

  _buildStateOutput(state, displayLabel, faceDetected, confidence) {
    return {
      state,
      displayLabel,
      faceDetected,
      confidence,
      latencyMs: 0,
      debugScores: {}
    };
  }

  _recordAnalytics(expression, confidence) {
    this.sessionStats.totalSamples += 1;
    if (expression === 'NO_FACE') {
      this.sessionStats.noFaceSamples += 1;
    } else if (expression === 'MULTIPLE_FACES') {
      this.sessionStats.multipleFacesSamples += 1;
    } else {
      this.sessionStats.faceDetectedSamples += 1;
      this.sessionStats.totalConfidenceSum += confidence;

      if (expression === 'UNCERTAIN') {
        this.sessionStats.uncertainSamples += 1;
      } else if (this.sessionStats.expressionCounts[expression] !== undefined) {
        this.sessionStats.expressionCounts[expression] += 1;
      }
    }
  }

  getSessionAnalytics() {
    const total = this.sessionStats.totalSamples || 1;
    const faceDet = this.sessionStats.faceDetectedSamples || 1;

    let dominant = 'NEUTRAL';
    let maxCount = -1;

    Object.keys(this.sessionStats.expressionCounts).forEach(exp => {
      if (this.sessionStats.expressionCounts[exp] > maxCount) {
        maxCount = this.sessionStats.expressionCounts[exp];
        dominant = exp;
      }
    });

    const percentages = {};
    Object.keys(this.sessionStats.expressionCounts).forEach(exp => {
      const count = this.sessionStats.expressionCounts[exp];
      percentages[exp] = Math.round((count / faceDet) * 100);
    });

    const avgConf = faceDet > 0 ? Number((this.sessionStats.totalConfidenceSum / faceDet).toFixed(2)) : 0.0;

    return {
      totalAnalyzedDurationSeconds: Math.round(total * (this.sampleIntervalMs / 1000)),
      faceDetectedCoveragePercent: Math.round((this.sessionStats.faceDetectedSamples / total) * 100),
      dominantExpression: this._formatExpressionLabel(dominant),
      averageConfidence: avgConf,
      expressionDistribution: percentages,
      detectionDetails: {
        totalSamples: this.sessionStats.totalSamples,
        faceDetectedSamples: this.sessionStats.faceDetectedSamples,
        noFaceSamples: this.sessionStats.noFaceSamples,
        multipleFacesSamples: this.sessionStats.multipleFacesSamples,
        uncertainSamples: this.sessionStats.uncertainSamples
      }
    };
  }
}

export const facialExpressionAnalyzer = new FacialExpressionAnalyzer();

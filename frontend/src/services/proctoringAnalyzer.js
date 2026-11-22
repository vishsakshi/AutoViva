import { FilesetResolver, ObjectDetector } from '@mediapipe/tasks-vision';

const WASM_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm';
const MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/float32/1/efficientdet_lite0.tflite';
const DETECTED_CATEGORIES = ['person', 'cell phone', 'book', 'laptop'];

class ProctoringAnalyzer {
  constructor() {
    this.detector = null;
    this.initialization = null;
  }

  async initialize() {
    if (this.detector) return;
    if (this.initialization) return this.initialization;

    this.initialization = (async () => {
      const vision = await FilesetResolver.forVisionTasks(WASM_URL);
      const options = {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: 'GPU' },
        runningMode: 'VIDEO',
        scoreThreshold: 0.55,
        maxResults: 20,
        categoryAllowlist: DETECTED_CATEGORIES,
      };

      try {
        this.detector = await ObjectDetector.createFromOptions(vision, options);
      } catch (gpuError) {
        console.warn('GPU object detection is unavailable; trying CPU.', gpuError);
        this.detector = await ObjectDetector.createFromOptions(vision, {
          ...options,
          baseOptions: { modelAssetPath: MODEL_URL, delegate: 'CPU' },
        });
      }
    })();

    try {
      await this.initialization;
    } catch (error) {
      this.initialization = null;
      throw error;
    }
  }

  detectForVideo(video, timestamp) {
    if (!this.detector) {
      throw new Error('The proctoring object detector has not been initialized.');
    }

    const result = this.detector.detectForVideo(video, timestamp);
    const people = new Set();
    const prohibitedItems = new Set();

    for (const detection of result.detections || []) {
      const category = detection.categories?.[0];
      const label = (category?.categoryName || category?.displayName || '').toLowerCase();
      if (!category || category.score < 0.55) continue;

      if (label === 'person' && detection.boundingBox) {
        const { originX, originY, width, height } = detection.boundingBox;
        people.add([originX, originY, width, height].join(':'));
      } else if (['cell phone', 'book', 'laptop'].includes(label)) {
        prohibitedItems.add(label);
      }
    }

    return {
      personCount: people.size,
      prohibitedItems: [...prohibitedItems],
    };
  }
}

export const proctoringAnalyzer = new ProctoringAnalyzer();
